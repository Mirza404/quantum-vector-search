import { useState } from 'react'
import { runSearch, type QueryItem, type SearchResponse } from './api'
import ImageBrowser from './components/ImageBrowser'
import QueryPicker from './components/QueryPicker'
import SearchResults from './components/SearchResults'
import BenchmarkResults from './components/BenchmarkResults'

type View = 'browse' | 'search' | 'benchmarks'

function App() {
  const [view, setView] = useState<View>('browse')
  const [searchData, setSearchData] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleQuery = async (query: QueryItem) => {
    setLoading(true)
    setError(null)
    setView('search')
    try {
      const result = await runSearch(query.id)
      setSearchData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  const tabClass = (tab: View) =>
    [
      'flex-1 rounded-xl border px-5 py-2 text-sm font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
      view === tab
        ? 'border-brand bg-brand-muted text-brand focus-visible:outline-brand'
        : 'border-slate-200 text-slate-600 hover:border-slate-300 hover:text-slate-900 focus-visible:outline-slate-500',
    ].join(' ')

  return (
    <div className="flex-1 px-4 pb-12 pt-8 md:px-10 lg:px-12">
      <header className="mb-8 text-center">
        <h1 className="text-4xl font-semibold text-slate-900 md:text-5xl">Quantum Vector Search</h1>
        <p className="mt-2 text-base text-slate-500">Classical vs. quantum image search - side by side</p>
      </header>

      <nav className="mb-8 flex flex-col gap-3 sm:flex-row">
        <button className={tabClass('browse')} onClick={() => setView('browse')}>
          Browse Images
        </button>
        <button className={tabClass('search')} onClick={() => setView('search')}>
          Search
        </button>
        <button className={tabClass('benchmarks')} onClick={() => setView('benchmarks')}>
          Benchmarks
        </button>
      </nav>

      {view === 'search' && (
        <section className="space-y-4">
          <QueryPicker onSelect={handleQuery} disabled={loading} />
          {loading && (
            <p className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-center text-sm text-slate-600">
              Searching...
            </p>
          )}
          {error && (
            <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-center text-sm font-medium text-red-600">
              {error}
            </p>
          )}
          {searchData && !loading && <SearchResults data={searchData} />}
        </section>
      )}

      {view === 'browse' && <ImageBrowser />}

      {view === 'benchmarks' && <BenchmarkResults />}
    </div>
  )
}

export default App
