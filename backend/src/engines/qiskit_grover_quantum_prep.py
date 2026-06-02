from __future__ import annotations

import math
from typing import Any, List

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import StatePreparation
from qiskit_aer import AerSimulator

from .base import SearchEngineStrategy, SearchResult


class QiskitGroverQuantumPrepEngine(SearchEngineStrategy):
    """Grover's algorithm with quantum state preparation.

    Demonstrates O(sqrt(N)) oracle scaling for unstructured search with quantum
    state preparation. Unlike QiskitGroverEngine which uses classical dot
    products to find the target, this engine encodes vectors as quantum
    states using StatePreparation gates and uses quantum measurements to
    determine the closest match.

    State preparation uses Qiskit's StatePreparation gate to encode vector
    amplitudes directly into quantum states. The target determination is
    done via quantum measurement rather than classical similarity computation.
    """

    def __init__(self, *, backend: AerSimulator | None = None) -> None:
        self._backend = backend or AerSimulator()
        self._vectors: np.ndarray | None = None
        self._ids: List[str] = []
        self._circuit_depth: int | None = None
        self._num_qubits: int | None = None

    @property
    def name(self) -> str:
        return "qiskit_grover_quantum_prep"

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

        # --- Quantum state preparation to find target_idx ---
        target_idx = self._find_target_quantum(query, shots)

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
            "score_semantics": "grover_measurement_frequency_quantum_prep",
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
    # Quantum state preparation
    # ------------------------------------------------------------------

    def _find_target_quantum(self, query: np.ndarray, shots: int) -> int:
        """Find target index using quantum swap test circuits.

        For each database vector, creates a swap test circuit that prepares
        the query state and database vector state as quantum states, then
        estimates their fidelity via controlled-SWAP measurement on the
        ancilla qubit. Returns the index with highest measured fidelity.
        """
        n_items = len(self._ids)
        best_fidelity = -1.0
        best_idx = 0

        # Determine the number of qubits needed for state encoding
        vector_dim = len(query)
        n_state_qubits = int(np.ceil(np.log2(vector_dim)))
        padded_dim = 2 ** n_state_qubits

        # Pad query state with zeros if needed
        query_state = np.zeros(padded_dim, dtype=np.complex128)
        query_state[:vector_dim] = query

        for item_idx in range(n_items):
            # Pad database vector with zeros if needed
            db_vector = self._vectors[item_idx]
            db_state = np.zeros(padded_dim, dtype=np.complex128)
            db_state[:vector_dim] = db_vector

            # Build swap test circuit
            # Layout: [ancilla] [query_register] [db_register]
            circuit = QuantumCircuit(1 + 2 * n_state_qubits, 1)

            ancilla_qubit = 0
            query_qubits = list(range(1, 1 + n_state_qubits))
            db_qubits = list(range(1 + n_state_qubits, 1 + 2 * n_state_qubits))

            # Prepare query state using StatePreparation
            query_prep = StatePreparation(query_state)
            circuit.append(query_prep, query_qubits)

            # Prepare database vector state using StatePreparation
            db_prep = StatePreparation(db_state)
            circuit.append(db_prep, db_qubits)

            # Swap test circuit:
            # H on ancilla
            circuit.h(ancilla_qubit)

            # Controlled-SWAP between query and db registers, controlled by ancilla
            for q_qubit, db_qubit in zip(query_qubits, db_qubits):
                circuit.cswap(ancilla_qubit, q_qubit, db_qubit)

            # H on ancilla
            circuit.h(ancilla_qubit)

            # Measure ancilla
            circuit.measure(ancilla_qubit, 0)

            # Transpile circuit for AerSimulator (decomposes StatePreparation gates)
            circuit = transpile(circuit, self._backend)

            # Run circuit on backend
            job = self._backend.run(circuit, shots=shots)
            counts = job.result().get_counts()

            # Fidelity = P(ancilla measured as 0) = 1/2 + 1/2 * cos(theta)
            # where theta is the relative phase between states.
            # Estimate from measurement counts: fidelity ~ (counts['0'] / shots)
            count_0 = counts.get('0', 0)
            measured_fidelity = count_0 / shots

            if measured_fidelity > best_fidelity:
                best_fidelity = measured_fidelity
                best_idx = item_idx

        return best_idx

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
