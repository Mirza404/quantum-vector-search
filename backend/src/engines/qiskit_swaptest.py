from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, List, Sequence

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from .base import SearchEngineStrategy, SearchResult


@dataclass
class _EncodedState:
    amplitudes: np.ndarray


class QiskitSwapTestEngine(SearchEngineStrategy):
    """Quantum-inspired engine that estimates similarity via a swap test."""

    def __init__(self, *, backend: AerSimulator | None = None) -> None:
        self._backend = backend or AerSimulator()
        self._records: List[_EncodedState] = []
        self._ids: List[str] = []
        self._vector_dim: int | None = None
        self._circuit_depth: int | None = None
        self._num_qubits: int | None = None

    @property
    def name(self) -> str:
        return "qiskit_swap_test"

    def build_index(self, *, vectors: List[List[float]], ids: List[str], **params: Any) -> None:
        if len(vectors) != len(ids):
            raise ValueError("vectors and ids must have the same length")
        if not vectors:
            raise ValueError("cannot build quantum index with no vectors")
        self._vector_dim = len(vectors[0])
        self._ids = ids
        self._records = [_EncodedState(amplitudes=self._encode(v)) for v in vectors]

    def search(self, *, query_vector: List[float], top_k: int = 10, shots: int = 1024, **params: Any) -> SearchResult:
        if self._vector_dim is None:
            raise RuntimeError("call build_index before search")
        if len(query_vector) != self._vector_dim:
            raise ValueError("query vector dimension mismatch")
        query_state = self._encode(query_vector)
        scores: List[float] = []
        for record in self._records:
            score = self._run_swap_test(query_state, record.amplitudes, shots=shots)
            scores.append(score)
        paired = list(zip(self._ids, scores))
        paired.sort(key=lambda item: item[1], reverse=True)
        top = paired[:top_k]
        meta = {
            "shots": shots,
            "score_semantics": "swap_test_overlap_probability",
            "circuit_depth": self._circuit_depth,
            "num_qubits": self._num_qubits,
        }
        return SearchResult(ids=[i for i, _ in top], scores=[s for _, s in top], meta=meta)

    # Helpers -----------------------------------------------------------------

    def _encode(self, vector: Sequence[float]) -> np.ndarray:
        arr = np.asarray(vector, dtype=float)
        padded = self._pad_to_power_of_two(arr)
        norm = np.linalg.norm(padded)
        if norm == 0:
            raise ValueError("cannot encode zero vector")
        return (padded / norm).astype(complex)

    @staticmethod
    def _pad_to_power_of_two(arr: np.ndarray) -> np.ndarray:
        length = arr.shape[0]
        target = 1 if length <= 1 else 1 << (length - 1).bit_length()
        if target == length:
            return arr
        padded = np.zeros(target, dtype=float)
        padded[:length] = arr
        return padded

    def _run_swap_test(self, query_state: np.ndarray, data_state: np.ndarray, *, shots: int) -> float:
        if query_state.shape[0] != data_state.shape[0]:
            raise ValueError("encoded state dimension mismatch")
        num_qubits = int(math.log2(query_state.shape[0]))
        circuit = QuantumCircuit(1 + 2 * num_qubits, 1)
        ancilla = 0
        left = list(range(1, 1 + num_qubits))
        right = list(range(1 + num_qubits, 1 + 2 * num_qubits))
        circuit.h(ancilla)
        circuit.initialize(query_state.tolist(), left)
        circuit.initialize(data_state.tolist(), right)
        for ql, qr in zip(left, right):
            circuit.cswap(ancilla, ql, qr)
        circuit.h(ancilla)
        circuit.measure(ancilla, 0)
        if self._circuit_depth is None:
            self._circuit_depth = circuit.depth()
            self._num_qubits = circuit.num_qubits
        job = self._backend.run(circuit, shots=shots)
        result = job.result()
        counts = result.get_counts()
        prob_zero = counts.get("0", 0) / shots
        overlap_squared = max(0.0, min(1.0, 2 * prob_zero - 1))
        return math.sqrt(overlap_squared)
