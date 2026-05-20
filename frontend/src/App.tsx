import { useState } from 'react'
import { runSearch, type QueryItem, type SearchResponse } from './api'
import ImageBrowser from './components/ImageBrowser'
import QueryPicker from './components/QueryPicker'
import SearchResults from './components/SearchResults'
import BenchmarkResults from './components/BenchmarkResults'

function SearchLoading() {
  return (
    <div className="rounded-2xl border border-violet-100 bg-violet-50/70 px-5 py-6 text-center shadow-card">
      <div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-full bg-white shadow-sm">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-violet-200 border-t-violet-600" />
      </div>
      <p className="text-sm font-semibold text-slate-900">Running search engines</p>
      <p className="mt-1 text-xs text-slate-500">
        Building indexes, embedding the query, and comparing classical, quantum, and hybrid results.
      </p>
      <div className="mx-auto mt-4 h-1.5 max-w-sm overflow-hidden rounded-full bg-white">
        <div className="h-full w-1/3 animate-[loading-bar_1.4s_ease-in-out_infinite] rounded-full bg-violet-500" />
      </div>
    </div>
  )
}

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
        <h1 className="text-4xl font-semibold text-slate-900 md:text-5xl">Classical vs. Quantum Image Search</h1>
        <p className="mt-2 text-base text-slate-500">Cross-modal retrieval using CLIP embeddings — benchmarked across 7 engines</p>
        <p className="mt-1 text-xs text-slate-400">IUS Graduation Project, 2026</p>
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
          {loading && <SearchLoading />}
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
