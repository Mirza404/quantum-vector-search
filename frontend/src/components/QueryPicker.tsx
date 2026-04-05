import { useEffect, useState } from 'react'
import { fetchQueries, type QueryItem } from '../api'

interface Props {
  onSelect: (query: QueryItem) => void
  disabled?: boolean
}

export default function QueryPicker({ onSelect, disabled }: Props) {
  const [queries, setQueries] = useState<QueryItem[]>([])
  const [selected, setSelected] = useState('')

  useEffect(() => {
    fetchQueries().then(setQueries).catch(console.error)
  }, [])

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value
    setSelected(id)
    const q = queries.find((q) => q.id === id)
    if (q) onSelect(q)
  }

  return (
    <div className="query-picker">
      <label htmlFor="query-select">Query:</label>
      <select id="query-select" value={selected} onChange={handleChange} disabled={disabled}>
        <option value="">-- pick a query --</option>
        {queries.map((q) => (
          <option key={q.id} value={q.id}>
            {q.text}
          </option>
        ))}
      </select>
    </div>
  )
}
