import { useEffect, useState } from 'react'
import { fetchImages, type PaginatedImages } from '../api'

export default function ImageBrowser() {
  const [data, setData] = useState<PaginatedImages | null>(null)
  const [page, setPage] = useState(1)
  const perPage = 20

  useEffect(() => {
    fetchImages(page, perPage).then(setData).catch(console.error)
  }, [page])

  if (!data)
    return (
      <p className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500 shadow-inner">
        Loading images...
      </p>
    )

  const totalPages = Math.ceil(data.total / perPage)

  return (
    <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-card">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Dataset</p>
          <h2 className="text-2xl font-semibold text-slate-900">
            {data.total.toLocaleString()} images
          </h2>
          <p className="text-sm text-slate-500">Page {page} of {totalPages}</p>
        </div>
        <span className="rounded-full bg-slate-100 px-4 py-1 text-xs font-semibold text-slate-600">
          {perPage} per page
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        {data.images.map((img) => (
          <figure
            key={img.id}
            className="group rounded-2xl border border-slate-100 bg-slate-50 p-3 transition hover:-translate-y-1 hover:shadow-lg"
          >
            <img
              src={img.url}
              alt={img.id}
              loading="lazy"
              className="mb-3 h-36 w-full rounded-xl object-cover"
            />
            <figcaption className="flex items-center justify-between text-xs text-slate-500">
              <span className="font-mono text-[11px] tracking-wide">{img.id}</span>
              <span className="rounded-full bg-white/60 px-2 py-0.5 font-medium text-slate-400 shadow-sm">
                #{img.id.slice(-3)}
              </span>
            </figcaption>
          </figure>
        ))}
      </div>

      <div className="mt-6 flex items-center justify-center gap-4 text-sm font-semibold text-slate-600">
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page <= 1}
          className="rounded-full border border-slate-200 px-4 py-2 text-xs uppercase tracking-wide text-slate-600 transition hover:border-slate-300 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Prev
        </button>
        <span className="text-slate-500">
          {page} / {totalPages}
        </span>
        <button
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          disabled={page >= totalPages}
          className="rounded-full border border-slate-200 px-4 py-2 text-xs uppercase tracking-wide text-slate-600 transition hover:border-slate-300 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Next
        </button>
      </div>
    </section>
  )
}
