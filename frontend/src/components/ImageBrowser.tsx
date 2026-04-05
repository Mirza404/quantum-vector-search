import { useEffect, useState } from 'react'
import { fetchImages, type PaginatedImages } from '../api'

export default function ImageBrowser() {
  const [data, setData] = useState<PaginatedImages | null>(null)
  const [page, setPage] = useState(1)
  const perPage = 20

  useEffect(() => {
    fetchImages(page, perPage).then(setData).catch(console.error)
  }, [page])

  if (!data) return <p>Loading images...</p>

  const totalPages = Math.ceil(data.total / perPage)

  return (
    <div className="image-browser">
      <h2>Dataset ({data.total} images)</h2>
      <div className="image-grid">
        {data.images.map((img) => (
          <div key={img.id} className="image-card">
            <img src={img.url} alt={img.id} loading="lazy" />
            <span className="image-id">{img.id}</span>
          </div>
        ))}
      </div>
      <div className="pagination">
        <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>
          Prev
        </button>
        <span>
          {page} / {totalPages}
        </span>
        <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>
          Next
        </button>
      </div>
    </div>
  )
}
