import { useCallback, useEffect, useState } from 'react'
import { NavLink, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { runSearch, type QueryItem, type SearchResponse } from './api'
import { ENGINES } from './engines'
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
        Comparing 7 engines side by side. Classical engines finish in milliseconds; the
        quantum simulator dominates the wait. <strong>Expect ~10-20 s at dim 128.</strong>
      </p>
      <div className="mx-auto mt-4 h-1.5 max-w-sm overflow-hidden rounded-full bg-white">
        <div className="h-full w-1/3 animate-[loading-bar_1.4s_ease-in-out_infinite] rounded-full bg-violet-500" />
      </div>
    </div>
  )
}

function SearchEmptyState() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white px-5 py-8 text-center shadow-card">
      <p className="text-sm font-semibold text-slate-900">Pick a query above to run it.</p>
      <p className="mt-2 text-sm text-slate-500">
        The same query is sent through every classical and quantum engine. We show the top
        results from each, the rank of the ground-truth image, and per-engine timing.
      </p>
    </div>
  )
}

function SearchRoute() {
  const location = useLocation()
  const navigate = useNavigate()
  const [queryId, setQueryId] = useState<string | null>(null)
  const [searchData, setSearchData] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleQuery = useCallback(
    (query: QueryItem) => {
      const selectedQueryId = query.id
      setQueryId(selectedQueryId)
      setSearchData(null)
      setLoading(true)
      setError(null)
      runSearch(selectedQueryId)
        .then((result) => {
          setSearchData(result)
          setLoading(false)
        })
        .catch((err) => {
          setError(err instanceof Error ? err.message : 'Search failed')
          setLoading(false)
        })
    },
    [],
  )

  useEffect(() => {
    if (location.search) {
      navigate(location.pathname, { replace: true })
    }
  }, [location.pathname, location.search, navigate])

  return (
    <section className="space-y-4">
      <QueryPicker selectedId={queryId} onSelect={handleQuery} disabled={loading} />
      {loading && <SearchLoading />}
      {error && (
        <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-center text-sm font-medium text-red-600">
          {error}
        </p>
      )}
      {!loading && !error && !searchData && <SearchEmptyState />}
      {searchData && !loading && <SearchResults data={searchData} />}
    </section>
  )
}

const ACTIVE_ENGINE_COUNT = Object.values(ENGINES).filter((engine) => engine.category !== 'ibm').length
const CURRENT_YEAR = new Date().getFullYear()

function App() {
  const tabClass = ({ isActive }: { isActive: boolean }) =>
    [
      'flex-1 rounded-xl border px-5 py-2 text-center text-sm font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
      isActive
        ? 'border-brand bg-brand-muted text-brand focus-visible:outline-brand'
        : 'border-slate-200 text-slate-600 hover:border-slate-300 hover:text-slate-900 focus-visible:outline-slate-500',
    ].join(' ')

  return (
    <div className="flex-1 px-4 pb-12 pt-8 md:px-10 lg:px-12">
      <header className="mb-8 text-center">
        <h1 className="text-4xl font-semibold text-slate-900 md:text-5xl">
          Classical vs. Quantum Image Search
        </h1>
        <p className="mt-2 text-base text-slate-500">
          Cross-modal retrieval using CLIP embeddings - benchmarked across {ACTIVE_ENGINE_COUNT} active engines + IBM validation
        </p>
        <p className="mt-1 text-xs text-slate-400">IUS Graduation Project, {CURRENT_YEAR}</p>
      </header>

      <nav className="mb-8 flex flex-col gap-3 sm:flex-row">
        <NavLink to="/browse" className={tabClass}>
          Browse Images
        </NavLink>
        <NavLink to="/search" className={tabClass}>
          Search
        </NavLink>
        <NavLink to="/benchmarks" className={tabClass}>
          Benchmarks
        </NavLink>
      </nav>

      <Routes>
        <Route path="/" element={<Navigate to="/browse" replace />} />
        <Route path="/browse" element={<ImageBrowser />} />
        <Route path="/search" element={<SearchRoute />} />
        <Route path="/benchmarks" element={<BenchmarkResults />} />
        <Route path="*" element={<Navigate to="/browse" replace />} />
      </Routes>
    </div>
  )
}

export default App
