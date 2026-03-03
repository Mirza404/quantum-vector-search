from __future__ import annotations

from qvs.engines.vector_mock import VectorMockEngine
from qvs.engines.quantum_mock import QuantumMockEngine


def main() -> None:
    # Tiny dummy dataset (later: load real dataset + embedding vectors)
    ids = ["a", "b", "c", "d"]
    vectors = [
        [0.0, 0.0],
        [1.0, 0.0],
        [0.0, 1.0],
        [1.0, 1.0],
    ]
    query = [0.9, 0.2]

    engines = [
        VectorMockEngine(),
        QuantumMockEngine(seed=42),
    ]

    for engine in engines:
        engine.build_index(vectors=vectors, ids=ids)
        result = engine.search(query_vector=query, top_k=2, shots=2048, layers=2)
        print(f"\nEngine: {engine.name}")
        print("IDs:", result.ids)
        print("Scores:", result.scores)
        print("Meta:", result.meta)


if __name__ == "__main__":
    main()