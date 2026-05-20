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
    results: List[EngineResultItem]
    mrr: float
    target_rank: Optional[int]  # rank of the ground-truth image (1-indexed), None if not found
    search_ms: float


class SearchResponse(BaseModel):
    query_id: str
    query_text: str
    target_image_id: str
    engines: List[EngineResult]


class EngineBenchmarkSummary(BaseModel):
    engine_name: str
    avg_mrr: float
    avg_search_ms: float
    avg_total_ms: float
    circuit_depth: Optional[int]
    num_qubits: Optional[int]
    avg_oracle_calls: Optional[float]
    total_runs: int


class BenchmarkSummaryResponse(BaseModel):
    engines: List[EngineBenchmarkSummary]
