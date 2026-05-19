"""API router - images, queries, and dual-engine search."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import List

import numpy as np
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from .dependencies import (
    IMAGES_DIR,
    SEARCH_DIMENSION,
    SEARCH_LAYERS,
    SEARCH_SHOTS,
    SEARCH_TOP_K,
    get_all_engines,
    get_classical_engine,
    get_clip_model,
    get_image_ids,
    get_queries,
    get_quantum_engine,
    get_storage,
)
from .schemas import (
    EngineResult,
    EngineResultItem,
    ImageItem,
    PaginatedImages,
    QueriesResponse,
    QueryItem,
    SearchResponse,
)

api_router = APIRouter(prefix="/api")

# ---------------------------------------------------------------------------
# GET /api/images - paginated listing of dataset images
# ---------------------------------------------------------------------------


@api_router.get("/images", response_model=PaginatedImages)
def list_images(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    all_ids = get_image_ids()
    total = len(all_ids)
    start = (page - 1) * per_page
    end = start + per_page
    page_ids = all_ids[start:end]
    return PaginatedImages(
        images=[ImageItem(id=img_id, url=f"/api/images/{img_id}") for img_id in page_ids],
        page=page,
        per_page=per_page,
        total=total,
    )


# ---------------------------------------------------------------------------
# GET /api/images/{image_id} - serve a single image file
# ---------------------------------------------------------------------------

_IMAGE_EXTENSIONS = [".webp", ".jpg", ".jpeg", ".png", ".bmp"]


@api_router.get("/images/{image_id}")
def get_image(image_id: str):
    for ext in _IMAGE_EXTENSIONS:
        path = IMAGES_DIR / f"{image_id}{ext}"
        if path.exists():
            return FileResponse(path)
    raise HTTPException(status_code=404, detail=f"Image '{image_id}' not found")


# ---------------------------------------------------------------------------
# GET /api/queries - list available ground-truth queries
# ---------------------------------------------------------------------------


@api_router.get("/queries", response_model=QueriesResponse)
def list_queries():
    queries = get_queries()
    return QueriesResponse(
        queries=[
            QueryItem(id=q.id, text=q.text, target_image_id=q.target_id)
            for q in queries
        ]
    )


# ---------------------------------------------------------------------------
# GET /api/engines - list available search engines
# ---------------------------------------------------------------------------


@api_router.get("/engines")
def list_engines():
    return {"engines": [
        "brute_force_cosine",
        "faiss_flat_l2", 
        "faiss_hnsw_l2",
        "qiskit_swap_test",
        "qiskit_grover",
        "qiskit_grover_quantum_prep",
    ]}


# ---------------------------------------------------------------------------
# GET /api/search?query_id=... - run search on both engines, side by side
# ---------------------------------------------------------------------------


def _run_engine(
    engine,
    query_vector: List[float],
    dataset_ids: List[str],
    vectors: List[List[float]],
    target_id: str,
    *,
    is_quantum: bool,
) -> EngineResult:
    engine.build_index(vectors=vectors, ids=dataset_ids)

    search_kwargs = {"query_vector": query_vector, "top_k": SEARCH_TOP_K}
    if is_quantum:
        search_kwargs["shots"] = SEARCH_SHOTS
        search_kwargs["layers"] = SEARCH_LAYERS

    start = perf_counter()
    result = engine.search(**search_kwargs)
    search_ms = (perf_counter() - start) * 1000

    # Build response items and find target rank
    target_rank = None
    items: List[EngineResultItem] = []
    for rank, (img_id, score) in enumerate(zip(result.ids, result.scores), 1):
        is_target = img_id == target_id
        if is_target and target_rank is None:
            target_rank = rank
        items.append(
            EngineResultItem(
                image_id=img_id,
                image_url=f"/api/images/{img_id}",
                score=float(score),
                is_target=is_target,
            )
        )

    mrr = 1.0 / target_rank if target_rank else 0.0

    return EngineResult(
        engine_name=engine.name,
        results=items,
        mrr=mrr,
        target_rank=target_rank,
        search_ms=round(search_ms, 2),
    )


@api_router.get("/search", response_model=SearchResponse)
def search(query_id: str = Query(..., description="ID from /api/queries")):
    queries = get_queries()
    query = next((q for q in queries if q.id == query_id), None)
    if query is None:
        raise HTTPException(status_code=404, detail=f"Query '{query_id}' not found")

    storage = get_storage()
    stored = storage.load_image_vectors()
    if not stored:
        raise HTTPException(status_code=503, detail="No image vectors in database. Run index_dataset.py first.")

    dataset_ids = list(stored.keys())
    full_matrix = np.array([stored[id_] for id_ in dataset_ids], dtype=np.float32)
    vectors = full_matrix[:, :SEARCH_DIMENSION].tolist()

    clip = get_clip_model()
    query_vector = clip.encode_texts([query.text])[0]
    query_vector = query_vector[:SEARCH_DIMENSION].astype(np.float32).tolist()

    engine_results = []
    for engine, is_quantum in get_all_engines():
        result = _run_engine(engine, query_vector, dataset_ids, vectors, query.target_id, is_quantum=is_quantum)
        engine_results.append(result)

    return SearchResponse(
        query_id=query.id,
        query_text=query.text,
        target_image_id=query.target_id,
        engines=engine_results,
    )
