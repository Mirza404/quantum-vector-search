from __future__ import annotations

import math
from typing import Any, List, Sequence

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from .base import SearchEngineStrategy, SearchResult


class QiskitGroverEngine(SearchEngineStrategy):
    """Grover's algorithm for quantum vector search on a simulator.

    Demonstrates O(sqrt(N)) oracle scaling for unstructured search.  The oracle
    marks the database vector closest to the query (determined classically
    during state preparation).  This isolates the *search* step so that
    oracle query counts can be measured independently of the O(N) state
    preparation cost which, without qRAM, cannot currently be avoided.

    State preparation is hardcoded for the toy dataset (O(N) gate
    operations).  The benchmark value is in the oracle call count -
    floor(pi*sqrt(N) / 4) - not in end-to-end wall-clock time.
    """

    def __init__(self, *, backend: AerSimulator | None = None) -> None:
        self._backend = backend or AerSimulator()
        self._vectors: np.ndarray | None = None
        self._ids: List[str] = []
        self._circuit_depth: int | None = None
        self._num_qubits: int | None = None

    @property
    def name(self) -> str:
        return "qiskit_grover"

    # ------------------------------------------------------------------
    # Index
    # ------------------------------------------------------------------

    def build_index(self, *, vectors: List[List[float]], ids: List[str], **params: Any) -> None:
        if len(vectors) != len(ids):
            raise ValueError("vectors and ids must have the same length")
        if not vectors:
            raise ValueError("cannot build index with no vectors")
        matrix = np.asarray(vectors, dtype=np.float64)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        self._vectors = matrix / norms
        self._ids = ids

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        *,
        query_vector: List[float],
        top_k: int = 10,
        shots: int = 1024,
        **params: Any,
    ) -> SearchResult:
        if self._vectors is None:
            raise RuntimeError("call build_index before search")

        query = np.asarray(query_vector, dtype=np.float64)
        q_norm = np.linalg.norm(query)
        if q_norm == 0.0:
            raise ValueError("query vector must be non-zero")
        query = query / q_norm

        n_items = len(self._ids)

        # --- Classical pre-computation (O(N) - the step qRAM would replace) ---
        similarities = self._vectors @ query
        target_idx = int(np.argmax(similarities))

        # Pad N to the next power of two so the index register is clean.
        n_index = max(2, 1 << (n_items - 1).bit_length())
        n_qubits = int(math.log2(n_index))
        oracle_calls = max(1, int(math.pi / 4 * math.sqrt(n_index)))

        # --- Build Grover circuit ---
        circuit = self._build_grover_circuit(n_qubits, target_idx, oracle_calls)

        if self._circuit_depth is None:
            self._circuit_depth = circuit.depth()
            self._num_qubits = circuit.num_qubits

        # --- Execute ---
        job = self._backend.run(circuit, shots=shots)
        counts = job.result().get_counts()

        # --- Decode measurement results into a ranking ---
        ranked_ids = self._decode_counts(counts, n_items)

        meta = {
            "shots": shots,
            "oracle_calls": oracle_calls,
            "n_index_qubits": n_qubits,
            "circuit_depth": self._circuit_depth,
            "num_qubits": self._num_qubits,
            "target_idx": target_idx,
            "score_semantics": "grover_measurement_frequency",
        }

        top = ranked_ids[:top_k]
        # Score by measurement frequency (normalised).
        total_shots = sum(counts.values())
        freq_by_id: dict[str, float] = {}
        for bitstring, count in counts.items():
            idx = int(bitstring, 2)
            if idx < n_items:
                freq_by_id[self._ids[idx]] = count / total_shots
        scores = [freq_by_id.get(id_, 0.0) for id_ in top]

        return SearchResult(ids=top, scores=scores, meta=meta)

    # ------------------------------------------------------------------
    # Circuit construction
    # ------------------------------------------------------------------

    def _build_grover_circuit(
        self, n_qubits: int, target_idx: int, iterations: int
    ) -> QuantumCircuit:
        """Build a standard Grover circuit: H|0> -> (Oracle * Diffusion)^k -> Measure."""
        circuit = QuantumCircuit(n_qubits, n_qubits)

        # Uniform superposition
        circuit.h(range(n_qubits))

        for _ in range(iterations):
            # Oracle: flip phase of |target_idx>
            self._apply_oracle(circuit, n_qubits, target_idx)
            # Diffusion: invert about the mean
            self._apply_diffusion(circuit, n_qubits)

        circuit.measure(range(n_qubits), range(n_qubits))
        return circuit

    @staticmethod
    def _apply_oracle(circuit: QuantumCircuit, n_qubits: int, target: int) -> None:
        """Phase oracle: applies Z (phase flip) to |target>.

        Flips X gates around the target's zero-bits so that a multi-controlled
        Z fires only on the target basis state.
        """
        # Flip qubits where the target has a 0 bit
        for qubit in range(n_qubits):
            if not (target >> qubit) & 1:
                circuit.x(qubit)

        # Multi-controlled Z = H on last qubit, MCX, H on last qubit
        if n_qubits == 1:
            circuit.z(0)
        else:
            circuit.h(n_qubits - 1)
            circuit.mcx(list(range(n_qubits - 1)), n_qubits - 1)
            circuit.h(n_qubits - 1)

        # Undo the X flips
        for qubit in range(n_qubits):
            if not (target >> qubit) & 1:
                circuit.x(qubit)

    @staticmethod
    def _apply_diffusion(circuit: QuantumCircuit, n_qubits: int) -> None:
        """Diffusion operator: 2|s><s| - I where |s> is uniform superposition."""
        circuit.h(range(n_qubits))
        circuit.x(range(n_qubits))

        # Multi-controlled Z on |11...1>
        if n_qubits == 1:
            circuit.z(0)
        else:
            circuit.h(n_qubits - 1)
            circuit.mcx(list(range(n_qubits - 1)), n_qubits - 1)
            circuit.h(n_qubits - 1)

        circuit.x(range(n_qubits))
        circuit.h(range(n_qubits))

    # ------------------------------------------------------------------
    # Result decoding
    # ------------------------------------------------------------------

    def _decode_counts(self, counts: dict[str, int], n_items: int) -> List[str]:
        """Convert measurement counts to a ranked list of image IDs.

        Indices >= n_items (padding) are discarded.  IDs are ranked by
        descending measurement frequency.
        """
        freq: dict[int, int] = {}
        for bitstring, count in counts.items():
            idx = int(bitstring, 2)
            if idx < n_items:
                freq[idx] = freq.get(idx, 0) + count

        # Rank by count descending, break ties by index ascending
        ranked = sorted(freq.keys(), key=lambda i: (-freq[i], i))

        # Append any IDs that didn't appear in measurements at all
        seen = set(ranked)
        for i in range(n_items):
            if i not in seen:
                ranked.append(i)

        return [self._ids[i] for i in ranked]
