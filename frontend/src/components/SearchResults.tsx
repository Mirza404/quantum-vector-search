import type { EngineResult, SearchResponse } from '../api'

function EnginePanel({ result, label }: { result: EngineResult; label: string }) {
  return (
    <div className="engine-panel">
      <h3>{label}</h3>
      <p className="engine-name">{result.engine_name}</p>
      <div className="engine-stats">
        <span>MRR: <strong>{result.mrr.toFixed(3)}</strong></span>
        <span>Target rank: <strong>{result.target_rank ?? 'not found'}</strong></span>
        <span>Time: <strong>{result.search_ms.toFixed(1)} ms</strong></span>
      </div>
      <div className="image-grid">
        {result.results.map((item, i) => (
          <div key={item.image_id} className={`image-card ${item.is_target ? 'is-target' : ''}`}>
            <span className="rank">#{i + 1}</span>
            <img src={item.image_url} alt={item.image_id} loading="lazy" />
            <span className="score">{item.score.toFixed(3)}</span>
            {item.is_target && <span className="target-badge">ground truth</span>}
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
    <div className="search-results">
      <p className="query-info">
        Query: <em>{data.query_text}</em> &mdash; target: <code>{data.target_image_id}</code>
      </p>
      <div className="side-by-side">
        <EnginePanel result={data.classical} label="Classical" />
        <EnginePanel result={data.quantum} label="Quantum" />
      </div>
    </div>
  )
}
