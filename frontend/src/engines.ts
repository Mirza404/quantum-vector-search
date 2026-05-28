/**
 * Single source of truth for engine display: human-readable names,
 * classification (classical / quantum / hybrid / ibm), score semantics
 * (what each engine's per-result `score` actually means), and the
 * algorithmic-scaling label shown in the benchmarks table.
 *
 * Both BenchmarkResults and SearchResults read from here so the two views
 * agree.
 */

export type EngineCategory = 'classical' | 'quantum' | 'hybrid' | 'ibm'

export interface EngineMeta {
  /** Snake_case identifier returned by the backend. */
  id: string
  /** Short human label shown in headers / cards. */
  label: string
  /** Longer one-line description for tooltips and "About" panels. */
  description: string
  /** Classification used for grouping and colour-coding. */
  category: EngineCategory
  /** Comparisons per query (algorithmic scaling), shown under "Scaling". */
  scaling: string
  /** Semantic of the per-result `score` field for this engine. */
  scoreType: string
}

export const ENGINES: Record<string, EngineMeta> = {
  brute_force_cosine: {
    id: 'brute_force_cosine',
    label: 'Brute-force cosine',
    description: 'NumPy dot product against every normalised vector. Ground truth for accuracy.',
    category: 'classical',
    scaling: 'O(N) comparisons',
    scoreType: 'cosine similarity (−1 to 1, higher = closer)',
  },
  faiss_flat_l2: {
    id: 'faiss_flat_l2',
    label: 'FAISS flat (L2)',
    description: 'FAISS IndexFlatL2 — exact search using SIMD-vectorised L2 distance.',
    category: 'classical',
    scaling: 'O(N) comparisons',
    scoreType: 'negative L2 distance (higher = closer)',
  },
  faiss_hnsw_l2: {
    id: 'faiss_hnsw_l2',
    label: 'FAISS HNSW (L2)',
    description: 'Approximate nearest-neighbour search via a hierarchical navigable small-world graph.',
    category: 'classical',
    scaling: 'O(log N) graph hops',
    scoreType: 'negative L2 distance (higher = closer)',
  },
  hybrid_hnsw_swap_test: {
    id: 'hybrid_hnsw_swap_test',
    label: 'Hybrid (HNSW + swap test)',
    description: 'HNSW prefilters M candidates, then the swap test reranks them on the simulator.',
    category: 'hybrid',
    scaling: 'O(log N + M) comparisons',
    scoreType: 'swap-test overlap |⟨ψ|φ⟩|²',
  },
  hybrid_hnsw_swap_test_ibm: {
    id: 'hybrid_hnsw_swap_test_ibm',
    label: 'Hybrid (HNSW + swap test, IBM QPU)',
    description: 'Same hybrid pipeline, but the swap-test circuits execute on real IBM hardware. Validation run only.',
    category: 'ibm',
    scaling: 'IBM QPU validation',
    scoreType: 'swap-test overlap |⟨ψ|φ⟩|²',
  },
  qiskit_swap_test: {
    id: 'qiskit_swap_test',
    label: 'Swap test (Qiskit)',
    description: 'Quantum swap test on AerSimulator — estimates squared overlap of two amplitude-encoded vectors.',
    category: 'quantum',
    scaling: 'O(N) circuit runs',
    scoreType: 'swap-test overlap |⟨ψ|φ⟩|²',
  },
  qiskit_grover: {
    id: 'qiskit_grover',
    label: 'Grover (hardcoded oracle)',
    description: "Grover's algorithm with a classically pre-built oracle. Measures the √N oracle-call scaling.",
    category: 'quantum',
    scaling: 'O(√N) oracle calls',
    scoreType: 'measurement frequency at target index',
  },
  qiskit_grover_quantum_prep: {
    id: 'qiskit_grover_quantum_prep',
    label: 'Grover (quantum state prep)',
    description: "Grover variant that prepares the candidate state quantumly rather than via a classical oracle.",
    category: 'quantum',
    scaling: 'O(√N) oracle calls',
    scoreType: 'measurement frequency at target index',
  },
}

/** Fallback for unknown engine IDs so the UI never blanks out. */
export function getEngine(id: string): EngineMeta {
  return (
    ENGINES[id] ?? {
      id,
      label: id,
      description: 'Unknown engine — add it to frontend/src/engines.ts.',
      category: 'quantum',
      scaling: '—',
      scoreType: '—',
    }
  )
}

/** Tailwind tokens grouped by category so colour-coding stays consistent. */
export const CATEGORY_STYLE: Record<EngineCategory, {
  badge: string
  row: string
  bar: string
  text: string
}> = {
  classical: {
    badge: 'bg-blue-100 text-blue-800',
    row: 'bg-blue-50 hover:bg-blue-50',
    bar: 'bg-blue-500',
    text: 'text-blue-900',
  },
  quantum: {
    badge: 'bg-purple-100 text-purple-800',
    row: 'bg-purple-50 hover:bg-purple-50',
    bar: 'bg-purple-500',
    text: 'text-purple-900',
  },
  hybrid: {
    badge: 'bg-emerald-100 text-emerald-800',
    row: 'bg-emerald-50 hover:bg-emerald-50',
    bar: 'bg-emerald-500',
    text: 'text-emerald-900',
  },
  ibm: {
    badge: 'bg-amber-100 text-amber-800',
    row: 'bg-amber-50 hover:bg-amber-50',
    bar: 'bg-amber-500',
    text: 'text-amber-900',
  },
}
