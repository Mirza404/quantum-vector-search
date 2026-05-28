/** Thin API client - all fetch calls in one place. */

const BASE = '/api'

export interface ImageItem {
  id: string
  url: string
}

export interface PaginatedImages {
  images: ImageItem[]
  page: number
  per_page: number
  total: number
}

export interface QueryItem {
  id: string
  text: string
  target_image_id: string
}

export interface EngineResultItem {
  image_id: string
  image_url: string
  score: number
  is_target: boolean
}

export interface EngineResult {
  engine_name: string
  category: string
  results: EngineResultItem[]
  mrr: number
  target_rank: number | null
  search_ms: number
}

export interface SearchConfig {
  dimension: number
  shots: number
  layers: number
  top_k: number
}

export interface SearchResponse {
  query_id: string
  query_text: string
  target_image_id: string
  config: SearchConfig
  engines: EngineResult[]
}

export interface EngineBenchmarkSummary {
  engine_name: string
  category: string
  avg_mrr: number
  avg_search_ms: number
  avg_state_prep_ms: number | null
  avg_total_ms: number
  circuit_depth: number | null
  num_qubits: number | null
  avg_oracle_calls: number | null
  total_runs: number
}

export interface BenchmarkSummaryResponse {
  engines: EngineBenchmarkSummary[]
}

export interface BenchmarkBreakdownRow {
  engine_name: string
  category: string
  dimension: number
  shots: number | null
  avg_mrr: number
  avg_search_ms: number
  avg_state_prep_ms: number | null
  avg_total_ms: number
  circuit_depth: number | null
  num_qubits: number | null
  avg_oracle_calls: number | null
  runs: number
}

export interface BenchmarkBreakdownResponse {
  rows: BenchmarkBreakdownRow[]
}

export async function fetchImages(page = 1, perPage = 20): Promise<PaginatedImages> {
  const res = await fetch(`${BASE}/images?page=${page}&per_page=${perPage}`)
  if (!res.ok) throw new Error(`Failed to fetch images: ${res.status}`)
  return res.json()
}

export async function fetchQueries(): Promise<QueryItem[]> {
  const res = await fetch(`${BASE}/queries`)
  if (!res.ok) throw new Error(`Failed to fetch queries: ${res.status}`)
  const data = await res.json()
  return data.queries
}

export async function runSearch(queryId: string): Promise<SearchResponse> {
  const res = await fetch(`${BASE}/search?query_id=${encodeURIComponent(queryId)}`)
  if (!res.ok) throw new Error(`Search failed: ${res.status}`)
  return res.json()
}

export async function fetchBenchmarks(queryId?: string): Promise<BenchmarkSummaryResponse> {
  const url = queryId ? `/api/benchmarks?query_id=${encodeURIComponent(queryId)}` : '/api/benchmarks'
  const res = await fetch(url)
  if (!res.ok) throw new Error('Failed to fetch benchmarks')
  return res.json()
}

export async function fetchBenchmarkBreakdown(): Promise<BenchmarkBreakdownResponse> {
  const res = await fetch('/api/benchmarks/by-config')
  if (!res.ok) throw new Error('Failed to fetch benchmark breakdown')
  return res.json()
}
