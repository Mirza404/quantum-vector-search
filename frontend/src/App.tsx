import { useCallback, useEffect, useState } from 'react'
import { NavLink, Navigate, Route, Routes, useSearchParams } from 'react-router-dom'
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
        quantum simulator dominates the wait. <strong>Expect ~10–20 s at dim 128.</strong>
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

/**
 * The Search route owns its own state and reads the selected query from the URL.
 * That keeps the deep-link / refresh story working: hitting /search?q=query_X
 * re-runs the search on mount, so reload preserves what the user was looking at.
 */
function SearchRoute() {
  const [searchParams, setSearchParams] = useSearchParams()
  const queryId = searchParams.get('q')
  const [searchData, setSearchData] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleQuery = useCallback(
    (query: QueryItem) => {
      // Update URL; the effect below picks it up and runs the search.
      setSearchParams({ q: query.id })
    },
    [setSearchParams],
  )

  // Fire whenever the query id in the URL changes. The cancelled flag protects
  // against React StrictMode's intentional double-invoke in dev: if the first
  // run is torn down before the network response lands, we discard it instead
  // of leaving stale state behind. (Earlier versions kept a lastFetchedId
  // guard, which caused the second invocation to short-circuit and leave
  // loading=true forever - see git history.)
  useEffect(() => {
    if (!queryId) {
      setSearchData(null)
      setError(null)
      setLoading(false)
      return
    }
    let cancelled = false
    setLoading(true)
    setError(null)
    runSearch(queryId)
      .then((result) => {
        if (!cancelled) {
          setSearchData(result)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Search failed')
          setLoading(false)
        }
      })
    return () => {
      cancelled = true
    }
  }, [queryId])

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

const TOTAL_ENGINES = Object.keys(ENGINES).length
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
          Cross-modal retrieval using CLIP embeddings — benchmarked across {TOTAL_ENGINES} engines
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
