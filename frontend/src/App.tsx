import { useState } from 'react'
import { runSearch, type QueryItem, type SearchResponse } from './api'
import ImageBrowser from './components/ImageBrowser'
import QueryPicker from './components/QueryPicker'
import SearchResults from './components/SearchResults'
import './App.css'

type View = 'browse' | 'search'

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

  return (
    <div className="app">
      <header>
        <h1>Quantum Vector Search</h1>
        <p className="subtitle">Classical vs. quantum image search — side by side</p>
      </header>

      <nav className="tabs">
        <button className={view === 'browse' ? 'active' : ''} onClick={() => setView('browse')}>
          Browse Images
        </button>
        <button className={view === 'search' ? 'active' : ''} onClick={() => setView('search')}>
          Search
        </button>
      </nav>

      {view === 'search' && (
        <section>
          <QueryPicker onSelect={handleQuery} disabled={loading} />
          {loading && <p className="status">Searching...</p>}
          {error && <p className="status error">{error}</p>}
          {searchData && !loading && <SearchResults data={searchData} />}
        </section>
      )}

      {view === 'browse' && <ImageBrowser />}
    </div>
  )
}

export default App
