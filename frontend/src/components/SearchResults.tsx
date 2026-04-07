import type { EngineResult, SearchResponse } from '../api'

function EnginePanel({ result, label }: { result: EngineResult; label: string }) {
  return (
    <div className="rounded-3xl border border-slate-100 bg-white p-6 shadow-card">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">{label}</p>
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

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {result.results.map((item, i) => (
          <div
            key={item.image_id}
            className={[
              'relative rounded-2xl border bg-slate-50 p-3 shadow-sm transition hover:-translate-y-1',
              item.is_target ? 'border-emerald-300 ring-2 ring-emerald-100' : 'border-slate-100',
            ].join(' ')}
          >
            <span className="absolute left-3 top-2 rounded-full bg-white/80 px-2 py-0.5 text-xs font-semibold text-slate-500 shadow">
              #{i + 1}
            </span>
            <img
              src={item.image_url}
              alt={item.image_id}
              loading="lazy"
              className="mb-3 h-40 w-full rounded-xl object-cover"
            />
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span className="font-mono">{item.image_id}</span>
              <span className="font-semibold text-slate-700">
                {item.score.toFixed(3)}
              </span>
            </div>
            {item.is_target && (
              <span className="mt-2 inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-emerald-700">
                GT ground truth
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
  return (
    <div className="space-y-6">
      <p className="text-center text-sm text-slate-600">
        Query: <span className="font-medium text-slate-900">{data.query_text}</span> | target{' '}
        <code className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">
          {data.target_image_id}
        </code>
      </p>
      <div className="grid gap-6 lg:grid-cols-2">
        <EnginePanel result={data.classical} label="Classical" />
        <EnginePanel result={data.quantum} label="Quantum" />
      </div>
    </div>
  )
}
