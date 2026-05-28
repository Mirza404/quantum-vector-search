import { useState } from 'react'
import type { EngineResult, SearchResponse } from '../api'
import { CATEGORY_STYLE, getEngine } from '../engines'

function EnginePanel({ result }: { result: EngineResult }) {
  const meta = getEngine(result.engine_name)
  const truthRank = result.target_rank ?? null
  const [expanded, setExpanded] = useState(false)

  const initialCount = 6
  const totalAvailable = result.results.length
  const visibleCount = expanded ? totalAvailable : Math.min(initialCount, totalAvailable)
  const items = result.results.slice(0, visibleCount)
  const truthBeyondInitial =
    !expanded && truthRank !== null && truthRank > initialCount && truthRank <= totalAvailable

  return (
    <div className="flex h-full min-h-[620px] flex-col rounded-3xl border border-slate-100 bg-white p-6 shadow-card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-xl font-semibold text-slate-900">{meta.label}</h3>
          <div className="text-xs text-slate-400 font-mono">{meta.id}</div>
          <div className="mt-1 text-xs text-slate-500" title={meta.description}>
            Score: {meta.scoreType}
          </div>
        </div>
        <div className="flex flex-col text-right text-sm text-slate-500">
          <span title="Mean Reciprocal Rank for this query (1.0 = correct image was first)">
            MRR{' '}
            <span className="font-semibold text-slate-900">{result.mrr.toFixed(3)}</span>
          </span>
          <span title="Position where the correct image appeared in this engine's results (lower is better; 1 = first)">
            Correct image at{' '}
            <span className="font-semibold text-slate-900">
              {truthRank !== null ? `#${truthRank}` : 'not in top results'}
            </span>
          </span>
          <span title="Wall-clock time for the similarity step (CPU simulator for quantum engines)">
            Search{' '}
            <span className="font-semibold text-slate-900">
              {result.search_ms.toFixed(1)} ms
            </span>
          </span>
        </div>
      </div>

      {truthBeyondInitial && (
        <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
          Correct image is at position #{truthRank} of {totalAvailable} — beyond the {initialCount} shown.{' '}
          <button
            type="button"
            onClick={() => setExpanded(true)}
            className="font-semibold underline hover:no-underline"
          >
            Show all
          </button>
          .
        </p>
      )}

      <div className="mt-6 grid flex-1 auto-rows-fr gap-4 sm:grid-cols-2">
        {items.map((item, i) => (
          <div
            key={item.image_id}
            className={[
              'relative flex min-h-[240px] flex-col rounded-2xl border bg-slate-50 p-3 shadow-sm transition hover:-translate-y-1',
              item.is_target ? 'border-emerald-300 ring-2 ring-emerald-100' : 'border-slate-100',
            ].join(' ')}
          >
            <span className="absolute left-3 top-2 z-10 rounded-full bg-slate-950 px-2.5 py-1 text-xs font-bold text-white shadow-lg ring-2 ring-white/80">
              #{i + 1}
            </span>
            <img
              src={item.image_url}
              alt={item.image_id}
              loading="lazy"
              className="mb-3 h-40 w-full rounded-xl object-cover"
            />
            <div className="mt-auto flex items-center justify-between text-xs text-slate-500">
              <span className="font-mono" title={meta.scoreType}>
                Score: {item.score.toFixed(3)}
              </span>
            </div>
            {item.is_target && (
              <span className="mt-2 inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-emerald-700">
                Ground truth
              </span>
            )}
          </div>
        ))}
      </div>

      {totalAvailable > initialCount && (
        <div className="mt-4 text-center">
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="text-xs font-semibold text-slate-600 underline hover:text-slate-900"
          >
            {expanded
              ? `Collapse to top ${initialCount}`
              : `Show all ${totalAvailable} results`}
          </button>
        </div>
      )}
    </div>
  )
}

interface Props {
  data: SearchResponse
}

export default function SearchResults({ data }: Props) {
  // Group by category from the API response, not by hard-coded names.
  const classical: EngineResult[] = []
  const others: EngineResult[] = []
  for (const e of data.engines) {
    if (e.category === 'classical') classical.push(e)
    else others.push(e)
  }
  const classicalStyle = CATEGORY_STYLE.classical
  const quantumStyle = CATEGORY_STYLE.quantum

  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center gap-2 text-center text-sm text-slate-600">
        <p>
          Query: <span className="font-medium text-slate-900">{data.query_text}</span>
        </p>
        <div className="inline-flex flex-wrap items-center justify-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
          <span title="CLIP vectors are truncated from 512 dims to this size before search">
            <strong className="text-slate-900">dim</strong> {data.config.dimension}
          </span>
          <span className="text-slate-300">|</span>
          <span title="Number of circuit executions per quantum similarity measurement; classical engines ignore this">
            <strong className="text-slate-900">{data.config.shots}</strong> shots
            <span className="ml-1 text-slate-400">(quantum only)</span>
          </span>
          <span className="text-slate-300">|</span>
          <span title="Maximum results returned by each engine; also the k in MRR@k">
            top-<strong className="text-slate-900">{data.config.top_k}</strong>
          </span>
        </div>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border-2 border-blue-300 p-4 space-y-4">
          <div className={`rounded-2xl border border-blue-200 px-4 py-3 ${classicalStyle.row}`}>
            <p className={`text-center text-sm font-semibold uppercase tracking-wide ${classicalStyle.text}`}>
              Classical Engines
            </p>
          </div>
          <div className="space-y-4">
            {classical.map((engine) => (
              <EnginePanel key={engine.engine_name} result={engine} />
            ))}
          </div>
        </div>

        <div className="rounded-2xl border-2 border-purple-300 p-4 space-y-4">
          <div className={`rounded-2xl border border-purple-200 px-4 py-3 ${quantumStyle.row}`}>
            <p className={`text-center text-sm font-semibold uppercase tracking-wide ${quantumStyle.text}`}>
              Quantum &amp; Hybrid Engines
            </p>
          </div>
          <div className="space-y-4">
            {others.map((engine) => (
              <EnginePanel key={engine.engine_name} result={engine} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
