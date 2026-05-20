import { useEffect, useState } from 'react'
import { fetchBenchmarks, type EngineBenchmarkSummary } from '../api'

const COMPLEXITY: Record<string, string> = {
  brute_force_cosine: 'O(N)',
  faiss_flat_l2: 'O(N)',
  faiss_hnsw_l2: 'O(log N)',
  qiskit_swap_test: 'O(N)',
  qiskit_grover: 'O(√N)',
  qiskit_grover_quantum_prep: 'O(√N)',
}

export default function BenchmarkResults() {
  const [data, setData] = useState<EngineBenchmarkSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const classicalEngines = ['brute_force_cosine', 'faiss_flat_l2', 'faiss_hnsw_l2']
  const quantumEngines = ['qiskit_swap_test', 'qiskit_grover', 'qiskit_grover_quantum_prep']
  const isClassical = (engineName: string) => classicalEngines.includes(engineName)

  const formatValue = (value: number | null | undefined, decimals = 2) => {
    if (value === null || value === undefined) return '—'
    return value.toFixed(decimals)
  }

  useEffect(() => {
    ;(async () => {
      try {
        const response = await fetchBenchmarks()
        setData(response.engines)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch benchmarks')
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const getHighestMRREngine = () => {
    if (data.length === 0) return null
    return data.reduce((prev, current) =>
      prev.avg_mrr > current.avg_mrr ? prev : current
    )
  }

  const getBestQuantumEngine = () => {
    const quantum = data.filter(e => quantumEngines.includes(e.engine_name))
    if (quantum.length === 0) return null
    return quantum.reduce((prev, current) =>
      prev.avg_mrr > current.avg_mrr ? prev : current
    )
  }

  const getWorstEngine = () => {
    if (data.length === 0) return null
    return data.reduce((prev, current) =>
      prev.avg_mrr < current.avg_mrr ? prev : current
    )
  }

  const bestEngine = getHighestMRREngine()
  const bestQuantum = getBestQuantumEngine()
  const worstEngine = getWorstEngine()
  const highestEngine = bestEngine?.engine_name ?? null

  const generateConclusion = () => {
    if (!bestEngine || !bestQuantum || !worstEngine) return null
    const swapTest = data.find(e => e.engine_name === 'qiskit_swap_test')
    return (
      `Across all benchmark queries and both vector dimensions, ${bestEngine.engine_name} achieves the highest accuracy ` +
      `(MRR ${bestEngine.avg_mrr.toFixed(3)}), confirming it as the ground truth baseline. ` +
      `Among quantum engines, ${bestQuantum.engine_name} performs best (MRR ${bestQuantum.avg_mrr.toFixed(3)}). ` +
      `The ${worstEngine.engine_name} engine shows the lowest accuracy (MRR ${worstEngine.avg_mrr.toFixed(3)}). ` +
      (swapTest ? `The swap test engine (MRR ${swapTest.avg_mrr.toFixed(3)}) requires ` +
      `${swapTest.circuit_depth ?? '—'} circuit depth and ${swapTest.num_qubits ?? '—'} qubits. ` : '') +
      `Classical engines are orders of magnitude faster than quantum engines, which reflects simulation overhead rather than true quantum hardware performance.`
    )
  }

  const getRowClass = (engineName: string) => {
    if (highestEngine === engineName) return 'border-b border-slate-100 bg-green-200 hover:bg-green-200'
    if (isClassical(engineName)) return 'border-b border-slate-100 bg-blue-50 hover:bg-blue-50'
    return 'border-b border-slate-100 bg-purple-50 hover:bg-purple-50'
  }

  const getCellClass = (engineName: string) => {
    if (highestEngine === engineName) return 'text-slate-900 font-bold'
    return 'text-slate-600'
  }

  return (
    <section className="space-y-6">
      <div className="text-center">
        <h2 className="text-3xl font-semibold text-slate-900">Benchmark Results</h2>
        <p className="mt-2 text-base text-slate-500">Classical vs. Quantum engine comparison</p>
      </div>

      <div className="rounded-3xl border border-slate-100 bg-white p-6 shadow-card space-y-6">
        {loading && (
          <div className="text-center py-8 text-slate-500">Loading benchmarks...</div>
        )}
        {error && (
          <div className="text-center py-8 text-red-600">Error: {error}</div>
        )}
        {!loading && !error && data.length === 0 && (
          <div className="text-center py-8 text-slate-500">No benchmark data available</div>
        )}
        {!loading && !error && data.length > 0 && (
          <>
            <p className="text-sm text-slate-600 leading-relaxed text-center">
              The table below shows average performance metrics for each engine across all 20
              benchmark queries and both vector dimensions (64 and 128). MRR (Mean Reciprocal Rank)
              measures search accuracy — higher is better. Search time and total time are in
              milliseconds. Circuit depth and qubit count are quantum resource metrics — lower
              circuit depth means less decoherence risk on real hardware.
            </p>
            <div className="overflow-x-auto mt-8 mb-8">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="px-4 py-3 text-left font-semibold text-slate-900">Engine</th>
                    <th className="px-4 py-3 text-left font-semibold text-slate-900">Complexity</th>
                    <th className="px-4 py-3 text-center font-semibold text-slate-900">Avg MRR</th>
                    <th className="px-4 py-3 text-center font-semibold text-slate-900">Avg Search Time (ms)</th>
                    <th className="px-4 py-3 text-center font-semibold text-slate-900">Avg Total Time (ms)</th>
                    <th className="px-4 py-3 text-center font-semibold text-slate-900">Circuit Depth</th>
                    <th className="px-4 py-3 text-center font-semibold text-slate-900">Qubits</th>
                    <th className="px-4 py-3 text-center font-semibold text-slate-900">Avg Oracle Calls</th>
                    <th className="px-4 py-3 text-center font-semibold text-slate-900">Total Runs</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((row) => (
                    <tr key={row.engine_name} className={getRowClass(row.engine_name)}>
                      <td className={`px-4 py-3 font-medium ${highestEngine === row.engine_name ? 'text-slate-900 font-bold' : 'text-slate-900'}`}>
                        {row.engine_name}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-mono font-semibold ${
                          isClassical(row.engine_name)
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-purple-100 text-purple-800'
                        }`}>
                          {COMPLEXITY[row.engine_name] ?? '—'}
                        </span>
                      </td>
                      <td className={`px-4 py-3 text-center ${getCellClass(row.engine_name)}`}>
                        {formatValue(row.avg_mrr, 3)}
                      </td>
                      <td className={`px-4 py-3 text-center ${getCellClass(row.engine_name)}`}>
                        {formatValue(row.avg_search_ms, 1)}
                      </td>
                      <td className={`px-4 py-3 text-center ${getCellClass(row.engine_name)}`}>
                        {formatValue(row.avg_total_ms, 1)}
                      </td>
                      <td className={`px-4 py-3 text-center ${getCellClass(row.engine_name)}`}>
                        {isClassical(row.engine_name) ? '—' : row.circuit_depth ?? '—'}
                      </td>
                      <td className={`px-4 py-3 text-center ${getCellClass(row.engine_name)}`}>
                        {isClassical(row.engine_name) ? '—' : row.num_qubits ?? '—'}
                      </td>
                      <td className={`px-4 py-3 text-center ${getCellClass(row.engine_name)}`}>
                        {isClassical(row.engine_name) ? '—' : formatValue(row.avg_oracle_calls)}
                      </td>
                      <td className={`px-4 py-3 text-center ${getCellClass(row.engine_name)}`}>
                        {row.total_runs}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-sm text-slate-600 leading-relaxed text-center">
              {generateConclusion()}
            </p>
          </>
        )}
      </div>
    </section>
  )
}