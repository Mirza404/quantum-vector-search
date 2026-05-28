import { type ChangeEvent, useEffect, useState } from 'react'
import { fetchQueries, type QueryItem } from '../api'

interface Props {
  onSelect: (query: QueryItem) => void
  /** Controlled selection from the parent route. Optional. */
  selectedId?: string | null
  disabled?: boolean
}

export default function QueryPicker({ onSelect, selectedId, disabled }: Props) {
  const [queries, setQueries] = useState<QueryItem[]>([])

  useEffect(() => {
    fetchQueries().then(setQueries).catch(console.error)
  }, [])

  const handleChange = (e: ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value
    const q = queries.find((q) => q.id === id)
    if (q) onSelect(q)
  }

  const selected = selectedId ?? ''

  return (
    <div className="flex flex-col gap-2 rounded-2xl border border-slate-200 bg-white p-4 shadow-card sm:flex-row sm:items-center">
      <label
        htmlFor="query-select"
        className="text-sm font-semibold uppercase tracking-wide text-slate-500 sm:basis-32"
      >
        Query
      </label>
      <select
        id="query-select"
        value={selected}
        onChange={handleChange}
        disabled={disabled}
        className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 shadow-inner focus:border-brand focus:outline-none focus:ring-4 focus:ring-brand/20 disabled:opacity-60"
      >
        <option value="">Pick a query...</option>
        {queries.map((q) => (
          <option key={q.id} value={q.id}>
            {q.text}
          </option>
        ))}
      </select>
    </div>
  )
}
