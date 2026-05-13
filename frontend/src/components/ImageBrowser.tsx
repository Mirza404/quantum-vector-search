import { useEffect, useState } from 'react'
import { fetchImages, type PaginatedImages } from '../api'

export default function ImageBrowser() {
  const [data, setData] = useState<PaginatedImages | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadAllImages = async () => {
      try {
        const allImages: typeof PaginatedImages.prototype.images = []
        let page = 1
        let totalFetched = 0
        let total = 0

        // Fetch first page to get total count
        const firstPage = await fetchImages(1, 100)
        total = firstPage.total
        allImages.push(...firstPage.images)
        totalFetched = firstPage.images.length

        // Fetch remaining pages if needed
        while (totalFetched < total) {
          page++
          const nextPage = await fetchImages(page, 100)
          allImages.push(...nextPage.images)
          totalFetched += nextPage.images.length
        }

        // Set data with all images
        setData({
          images: allImages,
          page: 1,
          per_page: totalFetched,
          total: total,
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load images')
        console.error(err)
      }
    }

    loadAllImages()
  }, [])

  if (error)
    return (
      <p className="rounded-2xl border border-red-200 bg-red-50 px-4 py-8 text-center text-sm text-red-600 shadow-inner">
        Error loading images: {error}
      </p>
    )

  if (!data)
    return (
      <p className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500 shadow-inner">
        Loading images...
      </p>
    )

  return (
    <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-card">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Dataset</p>
          <h2 className="text-2xl font-semibold text-slate-900">
            {data.total.toLocaleString()} images
          </h2>
        </div>
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
    </section>
  )
}
