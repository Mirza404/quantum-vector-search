import type { EngineResult, SearchResponse } from '../api'

function EnginePanel({ result }: { result: EngineResult }) {
  const limitedResults = result.results.slice(0, 6)
  return (
    <div className="flex h-full min-h-[620px] flex-col rounded-3xl border border-slate-100 bg-white p-6 shadow-card">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-xl font-semibold text-slate-900">{result.engine_name}</h3>
        </div>
        <div className="flex flex-col text-right text-sm text-slate-500">
          <span>
            MRR <span className="font-semibold text-slate-900">{result.mrr.toFixed(3)}</span>
          </span>
          <span>
            Rank{' '}
            <span className="font-semibold text-slate-900">
              {result.target_rank ?? 'N/A'}
            </span>
          </span>
          <span>
            Time{' '}
            <span className="font-semibold text-slate-900">
              {result.search_ms.toFixed(1)} ms
            </span>
          </span>
        </div>
      </div>

      <div className="mt-6 grid flex-1 auto-rows-fr gap-4 sm:grid-cols-2">
        {limitedResults.map((item, i) => (
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
              <span className="font-semibold">
                Probability: {item.score.toFixed(3)}
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
    </div>
  )
}

interface Props {
  data: SearchResponse
}

export default function SearchResults({ data }: Props) {
  const classicalEngineNames = ['brute_force_cosine', 'faiss_flat_l2', 'faiss_hnsw_l2']
  const quantumEngineNames = [
    'hybrid_hnsw_swap_test',
    'qiskit_swap_test',
    'qiskit_grover',
    'qiskit_grover_quantum_prep',
  ]

  const classicalEngines = data.engines.filter((e) => classicalEngineNames.includes(e.engine_name))
  const quantumEngines = data.engines.filter((e) => quantumEngineNames.includes(e.engine_name))

  return (
    <div className="space-y-6">
      <p className="text-center text-sm text-slate-600">
        Query: <span className="font-medium text-slate-900">{data.query_text}</span>
      </p>
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Classical Engines Column */}
        <div className="rounded-2xl border-2 border-blue-300 p-4 space-y-4">
          <div className="rounded-2xl bg-blue-50 border border-blue-200 px-4 py-3">
            <p className="text-center text-sm font-semibold uppercase tracking-wide text-blue-900">Classical Engines</p>
          </div>
          <div className="space-y-4">
            {classicalEngines.map((engine) => (
              <EnginePanel key={engine.engine_name} result={engine} />
            ))}
          </div>
        </div>

        {/* Quantum Engines Column */}
        <div className="rounded-2xl border-2 border-purple-300 p-4 space-y-4">
          <div className="rounded-2xl bg-purple-50 border border-purple-200 px-4 py-3">
            <p className="text-center text-sm font-semibold uppercase tracking-wide text-purple-900">Quantum Engines</p>
          </div>
          <div className="space-y-4">
            {quantumEngines.map((engine) => (
              <EnginePanel key={engine.engine_name} result={engine} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
