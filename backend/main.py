from __future__ import annotations

from pathlib import Path
import sys
from typing import List

BACKEND_ROOT = Path(__file__).resolve().parent
SRC_PATH = BACKEND_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from benchmark import load_benchmark_queries
from engines.faiss_flat import FaissFlatEngine
from engines.qiskit_swaptest import QiskitSwapTestEngine
from pipeline import CLIPEmbeddingModel
from repository import LocalCSVDataLoader

CLIP_MODEL_NAME = "ViT-B/32"
CLIP_BATCH_SIZE = 16


def _generate_dataset_vectors(dataset, clip_model: CLIPEmbeddingModel) -> tuple[List[List[float]], int]:
    image_paths = [record.image_path for record in dataset.records]
    matrix = clip_model.encode_images(image_paths)
    matrix = matrix.astype("float32", copy=False)
    return matrix.tolist(), matrix.shape[1]


def main() -> None:
    dataset_dir = BACKEND_ROOT / "data" / "sample_dataset"
    loader = LocalCSVDataLoader(dataset_dir=dataset_dir)
    dataset = loader.get_dataset()
    clip_model = CLIPEmbeddingModel(model_name=CLIP_MODEL_NAME, batch_size=CLIP_BATCH_SIZE)
    vectors, dataset_dim = _generate_dataset_vectors(dataset, clip_model)

    ground_truth_path = dataset_dir / "ground_truth.jsonc"
    queries = load_benchmark_queries(ground_truth_path)
    demo_query = queries[0]
    query_vector = clip_model.encode_texts([demo_query.text])[0]
    if dataset_dim < query_vector.shape[0]:
        query_vector = query_vector[:dataset_dim]
    query_vector = query_vector.tolist()

    print("Dataset:", loader.describe_source())
    print(f"Embeddings dimension: {dataset_dim}")
    print(f"Demo query ({demo_query.id}): {demo_query.text}")

    engines = [
        FaissFlatEngine(dimension=dataset_dim),
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
