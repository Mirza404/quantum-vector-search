from __future__ import annotations

from pathlib import Path
from typing import List

from qvs.benchmark import load_benchmark_queries
from qvs.engines.faiss_flat import FaissFlatEngine
from qvs.engines.qiskit_swaptest import QiskitSwapTestEngine
from qvs.pipeline import EmbeddingCache, MockCLIPEmbeddingGenerator
from qvs.repository import LocalCSVDataLoader

DEMO_DIMENSION = 8
EMBEDDING_SEED = "mock-clip"


def _load_vectors(dataset_dir: Path, texts: List[str], *, dimension: int) -> tuple[List[List[float]], bool]:
    cache = EmbeddingCache(dataset_dir / "cache")
    snapshot = cache.load()
    matrix = cache.load_matrix() if snapshot else None

    if snapshot and matrix is not None and snapshot.dimension >= dimension:
        return matrix[:, :dimension].tolist(), True

    embedder = MockCLIPEmbeddingGenerator(seed=EMBEDDING_SEED)
    return embedder.embed_many(texts, dimension=dimension), False


def main() -> None:
    dataset_dir = Path(__file__).parent / "data" / "sample_dataset"
    loader = LocalCSVDataLoader(dataset_dir=dataset_dir)
    dataset = loader.get_dataset()
    vectors, from_cache = _load_vectors(dataset_dir, dataset.texts(), dimension=DEMO_DIMENSION)
    embedder = MockCLIPEmbeddingGenerator(seed=EMBEDDING_SEED)

    ground_truth_path = dataset_dir / "ground_truth.json"
    queries = load_benchmark_queries(ground_truth_path)
    demo_query = queries[0]
    query_vector = embedder.embed(demo_query.text, dimension=DEMO_DIMENSION)

    print("Dataset:", loader.describe_source())
    print("Embeddings source:", "cache" if from_cache else "fresh (run scripts/build_embeddings.py to persist)")
    print(f"Demo query ({demo_query.id}): {demo_query.text}")

    engines = [
        FaissFlatEngine(dimension=DEMO_DIMENSION),
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
