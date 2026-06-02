import { useEffect, useState } from 'react'
import {
  fetchBenchmarkBreakdown,
  fetchBenchmarks,
  type BenchmarkBreakdownRow,
  type EngineBenchmarkSummary,
} from '../api'
import { CATEGORY_STYLE, getEngine } from '../engines'
import MetricsLegend from './MetricsLegend'

type ViewMode = 'summary' | 'breakdown'

const fmt = (value: number | null | undefined, decimals = 2) =>
  value === null || value === undefined ? '-' : value.toFixed(decimals)

export default function BenchmarkResults() {
  const [summary, setSummary] = useState<EngineBenchmarkSummary[]>([])
  const [breakdown, setBreakdown] = useState<BenchmarkBreakdownRow[]>([])
  const [view, setView] = useState<ViewMode>('summary')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    ;(async () => {
      try {
        const [s, b] = await Promise.all([fetchBenchmarks(), fetchBenchmarkBreakdown()])
        setSummary(s.engines)
        setBreakdown(b.rows)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch benchmarks')
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const bestSummary =
    summary.length === 0
      ? null
      : summary.reduce((p, c) => (p.avg_mrr > c.avg_mrr ? p : c))

  const renderConclusion = () => {
    if (summary.length === 0) return null
    const best = bestSummary!
    const others = summary.filter((e) => e.category !== 'classical')
    const bestQuantum = others.length
      ? others.reduce((p, c) => (p.avg_mrr > c.avg_mrr ? p : c))
      : null
    const worst = summary.reduce((p, c) => (p.avg_mrr < c.avg_mrr ? p : c))
    const bestLabel = getEngine(best.engine_name).label
    const worstLabel = getEngine(worst.engine_name).label
    return (
      <p className="text-sm text-slate-600 leading-relaxed text-center">
        Highest accuracy in this run: <strong>{bestLabel}</strong> at MRR{' '}
        {best.avg_mrr.toFixed(3)}. Lowest: {worstLabel} at MRR {worst.avg_mrr.toFixed(3)}.
        {bestQuantum && (
          <>
            {' '}
            Best non-classical engine: <strong>{getEngine(bestQuantum.engine_name).label}</strong>{' '}
            at MRR {bestQuantum.avg_mrr.toFixed(3)}
            {bestQuantum.circuit_depth != null && bestQuantum.num_qubits != null && (
              <>
                {' '}
                ({bestQuantum.num_qubits} qubits, circuit depth {bestQuantum.circuit_depth})
              </>
            )}
            .
          </>
        )}{' '}
        Wall-clock times on this page run on a CPU simulator and are not comparable across the
        classical/quantum split - see the legend above.
      </p>
    )
  }

  const renderSummaryTable = () => (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-slate-900">
            <th className="px-4 py-3 text-left font-semibold">Engine</th>
            <th className="px-4 py-3 text-left font-semibold">Scaling</th>
            <th className="px-4 py-3 text-center font-semibold" title="Mean Reciprocal Rank - higher is better">
              Avg MRR
            </th>
            <th className="px-4 py-3 text-center font-semibold" title="Average milliseconds per query for the similarity step only">
              Search ms
            </th>
            <th className="px-4 py-3 text-center font-semibold" title="Time spent encoding vectors into a quantum state; classical engines skip this">
              State-prep ms
            </th>
            <th className="px-4 py-3 text-center font-semibold">Circuit depth</th>
            <th className="px-4 py-3 text-center font-semibold">Qubits</th>
            <th className="px-4 py-3 text-center font-semibold">Avg oracle calls</th>
            <th className="px-4 py-3 text-center font-semibold">Runs</th>
          </tr>
        </thead>
        <tbody>
          {summary.map((row) => {
            const meta = getEngine(row.engine_name)
            const style = CATEGORY_STYLE[meta.category]
            const isBest = bestSummary?.engine_name === row.engine_name
            const isClassical = row.category === 'classical'
            const rowClass = `border-b border-slate-100 ${isBest ? 'bg-green-100' : style.row}`
            const cellClass = isBest ? 'text-slate-900 font-semibold' : 'text-slate-600'
            return (
              <tr key={row.engine_name} className={rowClass}>
                <td className="px-4 py-3 text-slate-900">
                  <div className="font-medium">{meta.label}</div>
                  <div className="text-xs text-slate-400 font-mono">{meta.id}</div>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-block rounded-full px-2 py-0.5 text-xs font-mono font-semibold ${style.badge}`}
                    title={meta.description}
                  >
                    {meta.scaling}
                  </span>
                </td>
                <td className={`px-4 py-3 text-center ${cellClass}`}>{fmt(row.avg_mrr, 3)}</td>
                <td className={`px-4 py-3 text-center ${cellClass}`}>{fmt(row.avg_search_ms, 1)}</td>
                <td className={`px-4 py-3 text-center ${cellClass}`}>
                  {isClassical ? '-' : fmt(row.avg_state_prep_ms, 1)}
                </td>
                <td className={`px-4 py-3 text-center ${cellClass}`}>
                  {isClassical ? '-' : row.circuit_depth ?? '-'}
                </td>
                <td className={`px-4 py-3 text-center ${cellClass}`}>
                  {isClassical ? '-' : row.num_qubits ?? '-'}
                </td>
                <td className={`px-4 py-3 text-center ${cellClass}`}>
                  {row.avg_oracle_calls == null ? '-' : fmt(row.avg_oracle_calls)}
                </td>
                <td className={`px-4 py-3 text-center ${cellClass}`}>{row.total_runs}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )

  const renderBreakdownTable = () => (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-slate-900">
            <th className="px-4 py-3 text-left font-semibold">Engine</th>
            <th className="px-4 py-3 text-center font-semibold">Dim</th>
            <th className="px-4 py-3 text-center font-semibold">Shots</th>
            <th className="px-4 py-3 text-center font-semibold">Avg MRR</th>
            <th className="px-4 py-3 text-center font-semibold">Search ms</th>
            <th className="px-4 py-3 text-center font-semibold">State-prep ms</th>
            <th className="px-4 py-3 text-center font-semibold">Depth</th>
            <th className="px-4 py-3 text-center font-semibold">Qubits</th>
            <th className="px-4 py-3 text-center font-semibold">Runs</th>
          </tr>
        </thead>
        <tbody>
          {breakdown.map((row) => {
            const meta = getEngine(row.engine_name)
            const style = CATEGORY_STYLE[meta.category]
            const isClassical = row.category === 'classical'
            const shotsLabel = isClassical || row.shots === null || row.shots === -1 ? '-' : row.shots
            return (
              <tr
                key={`${row.engine_name}-${row.dimension}-${row.shots}`}
                className={`border-b border-slate-100 ${style.row}`}
              >
                <td className="px-4 py-3 text-slate-900">
                  <div className="font-medium">{meta.label}</div>
                  <div className="text-xs text-slate-400 font-mono">{meta.id}</div>
                </td>
                <td className="px-4 py-3 text-center text-slate-700">{row.dimension}</td>
                <td className="px-4 py-3 text-center text-slate-700">{shotsLabel}</td>
                <td className="px-4 py-3 text-center font-semibold text-slate-900">
                  {fmt(row.avg_mrr, 3)}
                </td>
                <td className="px-4 py-3 text-center text-slate-600">{fmt(row.avg_search_ms, 1)}</td>
                <td className="px-4 py-3 text-center text-slate-600">
                  {isClassical ? '-' : fmt(row.avg_state_prep_ms, 1)}
                </td>
                <td className="px-4 py-3 text-center text-slate-600">
                  {isClassical ? '-' : row.circuit_depth ?? '-'}
                </td>
                <td className="px-4 py-3 text-center text-slate-600">
                  {isClassical ? '-' : row.num_qubits ?? '-'}
                </td>
                <td className="px-4 py-3 text-center text-slate-600">{row.runs}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )

  const viewTabClass = (mode: ViewMode) =>
    [
      'rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors',
      view === mode
        ? 'bg-slate-900 text-white'
        : 'bg-slate-100 text-slate-600 hover:bg-slate-200',
    ].join(' ')

  return (
    <section className="space-y-6">
      <div className="text-center">
        <h2 className="text-3xl font-semibold text-slate-900">Benchmark Results</h2>
        <p className="mt-2 text-base text-slate-500">
          Accuracy and quantum resource cost per engine.
        </p>
      </div>

      <div className="rounded-3xl border border-slate-100 bg-white p-6 shadow-card space-y-6">
        <MetricsLegend />

        <div className="flex items-center justify-center gap-2">
          <span className="text-xs uppercase tracking-wide text-slate-400">View:</span>
          <button type="button" onClick={() => setView('summary')} className={viewTabClass('summary')}>
            Summary (one row per engine)
          </button>
          <button type="button" onClick={() => setView('breakdown')} className={viewTabClass('breakdown')}>
            By dim &amp; shots
          </button>
        </div>

        {loading && <div className="text-center py-8 text-slate-500">Loading benchmarks...</div>}
        {error && <div className="text-center py-8 text-red-600">Error: {error}</div>}
        {!loading && !error && summary.length === 0 && (
          <div className="text-center py-8 text-slate-500">
            No benchmark data available yet. Run <code>python3 scripts/run_benchmarks.py</code> from{' '}
            <code>backend/</code>.
          </div>
        )}

        {!loading && !error && summary.length > 0 && (
          <>
            {view === 'summary' ? renderSummaryTable() : renderBreakdownTable()}
            {view === 'summary' && renderConclusion()}
          </>
        )}
      </div>
    </section>
  )
}
