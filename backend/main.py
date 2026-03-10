from __future__ import annotations

from pathlib import Path
from typing import List

from qvs.benchmark import load_benchmark_queries
from qvs.engines.faiss_flat import FaissFlatEngine
from qvs.engines.qiskit_swaptest import QiskitSwapTestEngine
from qvs.pipeline import CLIPEmbeddingModel, EmbeddingCache
from qvs.repository import LocalCSVDataLoader

CLIP_MODEL_NAME = "ViT-B/32"
CLIP_BATCH_SIZE = 16


def _load_cached_vectors(dataset_dir: Path) -> tuple[List[List[float]], int, Path]:
    cache = EmbeddingCache(dataset_dir / "cache")
    snapshot = cache.load()
    if not snapshot:
        raise SystemExit(f"No cached embeddings found under {cache.cache_dir}. Run scripts/build_embeddings.py first.")
    matrix = cache.load_matrix()
    if matrix is None:
        raise SystemExit(f"Embeddings file missing at {cache.embeddings_path()}. Rebuild the cache.")
    vectors = matrix.tolist()
    return vectors, snapshot.dimension, cache.embeddings_path()


def main() -> None:
    dataset_dir = Path(__file__).parent / "data" / "sample_dataset"
    loader = LocalCSVDataLoader(dataset_dir=dataset_dir)
    dataset = loader.get_dataset()
    vectors, cached_dim, cache_path = _load_cached_vectors(dataset_dir)
    clip_model = CLIPEmbeddingModel(model_name=CLIP_MODEL_NAME, batch_size=CLIP_BATCH_SIZE)
    if cached_dim > clip_model.embedding_dimension:
        raise SystemExit(
            f"Cached embeddings ({cached_dim}) exceed CLIP output size ({clip_model.embedding_dimension}). Rebuild cache."
        )

    ground_truth_path = dataset_dir / "ground_truth.json"
    queries = load_benchmark_queries(ground_truth_path)
    demo_query = queries[0]
    query_vector = clip_model.encode_texts([demo_query.text])[0]
    if cached_dim < query_vector.shape[0]:
        query_vector = query_vector[:cached_dim]
    query_vector = query_vector.tolist()

    print("Dataset:", loader.describe_source())
    print(f"Embeddings cache: {cache_path}")
    print(f"Demo query ({demo_query.id}): {demo_query.text}")

    engines = [
        FaissFlatEngine(dimension=cached_dim),
        QiskitSwapTestEngine(),
    ]

    for engine in engines:
        engine.build_index(vectors=vectors, ids=dataset.ids())
        result = engine.search(query_vector=query_vector, top_k=3, shots=2048)
        print(f"\nEngine: {engine.name}")
        print("IDs:", result.ids)
        print("Scores:", result.scores)
        print("Meta:", result.meta)


if __name__ == "__main__":
    main()
