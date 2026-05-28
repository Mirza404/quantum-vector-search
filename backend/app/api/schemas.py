"""Pydantic response models for the API."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class ImageItem(BaseModel):
    id: str
    url: str  # relative path served by the backend


class PaginatedImages(BaseModel):
    images: List[ImageItem]
    page: int
    per_page: int
    total: int


class QueryItem(BaseModel):
    id: str
    text: str
    target_image_id: str  # ground-truth image for accuracy calculation


class QueriesResponse(BaseModel):
    queries: List[QueryItem]


class EngineResultItem(BaseModel):
    image_id: str
    image_url: str
    score: float
    is_target: bool  # whether this is the ground-truth match


class EngineResult(BaseModel):
    engine_name: str
    category: str  # classical | quantum | hybrid | ibm
    results: List[EngineResultItem]
    mrr: float
    target_rank: Optional[int]  # 1-indexed rank of the ground-truth image, None if outside top_k
    search_ms: float


class SearchConfig(BaseModel):
    """Config the live /api/search request actually ran with.

    Returned alongside results so the UI can show 'running at dim 128, 512 shots'
    instead of leaving the grader guessing.
    """
    dimension: int
    shots: int           # applied to quantum engines; classical engines ignore it
    layers: int          # currently unused by all active engines, here for completeness
    top_k: int


class SearchResponse(BaseModel):
    query_id: str
    query_text: str
    target_image_id: str
    config: SearchConfig
    engines: List[EngineResult]


class EngineBenchmarkSummary(BaseModel):
    engine_name: str
    category: str
    avg_mrr: float
    avg_search_ms: float
    avg_state_prep_ms: Optional[float]  # None for classical engines
    avg_total_ms: float
    circuit_depth: Optional[int]
    num_qubits: Optional[int]
    avg_oracle_calls: Optional[float]
    total_runs: int


class BenchmarkSummaryResponse(BaseModel):
    engines: List[EngineBenchmarkSummary]


class BenchmarkBreakdownRow(BaseModel):
    """One row per (engine, dimension, shots) - NOT collapsed across configs."""
    engine_name: str
    category: str
    dimension: int
    shots: Optional[int]  # None / -1 for classical engines
    avg_mrr: float
    avg_search_ms: float
    avg_state_prep_ms: Optional[float]
    avg_total_ms: float
    circuit_depth: Optional[int]
    num_qubits: Optional[int]
    avg_oracle_calls: Optional[float]
    runs: int


class BenchmarkBreakdownResponse(BaseModel):
    rows: List[BenchmarkBreakdownRow]


class EngineCatalogEntry(BaseModel):
    id: str
    category: str  # classical | quantum | hybrid | ibm
    is_quantum: bool
    live: bool  # whether the engine is exposed by /api/search


class EngineCatalogResponse(BaseModel):
    engines: List[EngineCatalogEntry]
