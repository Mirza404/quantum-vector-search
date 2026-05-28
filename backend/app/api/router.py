"""API router - images, queries, benchmarks, and side-by-side search."""

from __future__ import annotations

from time import perf_counter
from typing import List

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from .dependencies import (
    BENCHMARK_ONLY_CATEGORY,
    IMAGES_DIR,
    LIVE_ENGINE_CATALOG,
    SEARCH_DIMENSION,
    SEARCH_LAYERS,
    SEARCH_SHOTS,
    SEARCH_TOP_K,
    get_built_live_engines,
    get_clip_model,
    get_engine_category,
    get_image_ids,
    get_live_vectors_and_ids,
    get_queries,
    get_storage,
)
from .schemas import (
    BenchmarkBreakdownResponse,
    BenchmarkBreakdownRow,
    BenchmarkSummaryResponse,
    EngineCatalogEntry,
    EngineCatalogResponse,
    EngineResult,
    EngineResultItem,
    EngineBenchmarkSummary,
    ImageItem,
    PaginatedImages,
    QueriesResponse,
    QueryItem,
    SearchConfig,
    SearchResponse,
)

api_router = APIRouter(prefix="/api")

# ---------------------------------------------------------------------------
# GET /api/images - paginated dataset listing
# ---------------------------------------------------------------------------


@api_router.get("/images", response_model=PaginatedImages)
def list_images(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    all_ids = get_image_ids()
    total = len(all_ids)
    start = (page - 1) * per_page
    page_ids = all_ids[start : start + per_page]
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
# GET /api/queries - list ground-truth queries
# ---------------------------------------------------------------------------


@api_router.get("/queries", response_model=QueriesResponse)
def list_queries():
    return QueriesResponse(
        queries=[
            QueryItem(id=q.id, text=q.text, target_image_id=q.target_id)
            for q in get_queries()
        ]
    )


# ---------------------------------------------------------------------------
# GET /api/engines - live engine catalogue with category and quantum flag
# ---------------------------------------------------------------------------


@api_router.get("/engines", response_model=EngineCatalogResponse)
def list_engines():
    """Engines available to /api/search, plus benchmark-only engines (e.g. IBM).

    Frontends should read this rather than hardcoding lists.
    """
    live = [
        EngineCatalogEntry(
            id=str(e["id"]),
            category=str(e["category"]),
            is_quantum=bool(e["is_quantum"]),
            live=True,
        )
        for e in LIVE_ENGINE_CATALOG
    ]
    benchmark_only = [
        EngineCatalogEntry(id=eid, category=cat, is_quantum=True, live=False)
        for eid, cat in BENCHMARK_ONLY_CATEGORY.items()
    ]
    return EngineCatalogResponse(engines=live + benchmark_only)


# ---------------------------------------------------------------------------
# GET /api/benchmarks - aggregated benchmark summary (one row per engine)
# ---------------------------------------------------------------------------


@api_router.get("/benchmarks", response_model=BenchmarkSummaryResponse)
def get_benchmarks(query_id: str | None = Query(None)):
    rows = get_storage().load_benchmark_summary(query_id=query_id)
    engines = [
        EngineBenchmarkSummary(
            engine_name=row["engine_name"],
            category=get_engine_category(row["engine_name"]),
            avg_mrr=float(row["avg_mrr"]),
            avg_search_ms=float(row["avg_search_ms"]),
            avg_state_prep_ms=(
                float(row["avg_state_prep_ms"]) if row.get("avg_state_prep_ms") is not None else None
            ),
            avg_total_ms=float(row["avg_total_ms"]),
            circuit_depth=row["circuit_depth"],
            num_qubits=row["num_qubits"],
            avg_oracle_calls=(
                float(row["avg_oracle_calls"]) if row["avg_oracle_calls"] is not None else None
            ),
            total_runs=int(row["total_runs"]),
        )
        for row in rows
    ]
    return BenchmarkSummaryResponse(engines=engines)


# ---------------------------------------------------------------------------
# GET /api/benchmarks/by-config - per (engine, dim, shots) row (NOT aggregated)
# Used by the frontend to surface the shots-vs-MRR breakdown that RQ1 needs.
# ---------------------------------------------------------------------------


@api_router.get("/benchmarks/by-config", response_model=BenchmarkBreakdownResponse)
def get_benchmark_breakdown():
    rows = get_storage().load_benchmark_breakdown()
    return BenchmarkBreakdownResponse(
        rows=[
            BenchmarkBreakdownRow(
                engine_name=row["engine_name"],
                category=get_engine_category(row["engine_name"]),
                dimension=int(row["dimension"]),
                shots=int(row["shots"]) if row["shots"] is not None else None,
                avg_mrr=float(row["avg_mrr"]),
                avg_search_ms=float(row["avg_search_ms"]),
                avg_state_prep_ms=(
                    float(row["avg_state_prep_ms"]) if row.get("avg_state_prep_ms") is not None else None
                ),
                avg_total_ms=float(row["avg_total_ms"]),
                circuit_depth=row["circuit_depth"],
                num_qubits=row["num_qubits"],
                avg_oracle_calls=(
                    float(row["avg_oracle_calls"]) if row["avg_oracle_calls"] is not None else None
                ),
                runs=int(row["runs"]),
            )
            for row in rows
        ]
    )


# ---------------------------------------------------------------------------
# GET /api/search?query_id=... - run every engine, side by side
# Engines are pre-built and cached (see get_built_live_engines) so each
# request only pays for the search step.
# ---------------------------------------------------------------------------


def _run_engine(
    engine,
    *,
    query_vector: List[float],
    target_id: str,
    is_quantum: bool,
) -> EngineResult:
    search_kwargs = {"query_vector": query_vector, "top_k": SEARCH_TOP_K}
    if is_quantum:
        search_kwargs.update({"shots": SEARCH_SHOTS, "layers": SEARCH_LAYERS})

    start = perf_counter()
    result = engine.search(**search_kwargs)
    search_ms = (perf_counter() - start) * 1000

    target_rank: int | None = None
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
        category=get_engine_category(engine.name),
        results=items,
        mrr=mrr,
        target_rank=target_rank,
        search_ms=search_ms,
    )


@api_router.get("/search", response_model=SearchResponse)
def search(query_id: str = Query(..., description="ID from /api/queries")):
    query = next((q for q in get_queries() if q.id == query_id), None)
    if query is None:
        raise HTTPException(status_code=404, detail=f"Query '{query_id}' not found")

    built = get_built_live_engines()
    if not built:
        raise HTTPException(
            status_code=503,
            detail="No image vectors in database. Run index_dataset.py first.",
        )

    # We only need vectors for the query; engines are already indexed.
    _, vectors = get_live_vectors_and_ids()
    if not vectors:
        raise HTTPException(status_code=503, detail="Image vectors disappeared between cache and DB.")

    clip = get_clip_model()
    query_vector = clip.encode_texts([query.text])[0]
    query_vector = query_vector[: len(vectors[0])].astype("float32").tolist()

    engine_results = [
        _run_engine(engine, query_vector=query_vector, target_id=query.target_id, is_quantum=is_quantum)
        for engine, is_quantum in built
    ]

    return SearchResponse(
        query_id=query.id,
        query_text=query.text,
        target_image_id=query.target_id,
        config=SearchConfig(
            dimension=SEARCH_DIMENSION,
            shots=SEARCH_SHOTS,
            layers=SEARCH_LAYERS,
            top_k=SEARCH_TOP_K,
        ),
        engines=engine_results,
    )
