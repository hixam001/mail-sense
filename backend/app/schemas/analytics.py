"""Typed aggregate responses, excluding all private message-level fields."""

from typing import Literal

from pydantic import BaseModel

from app.schemas.common import CountMetric, Scope


class PublicArchive(BaseModel):
    archive_name: str
    source_url: str
    source_group: str
    label: Literal["ham", "spam"]
    sha256: str
    size_bytes: int
    acquired_at: str
    processing_status: str
    files_seen: int | None
    files_accepted: int | None
    files_rejected: int | None


class DatasetSummary(BaseModel):
    scope: Scope
    dataset_id: str
    split_id: str
    total: int
    class_counts: dict[str, int]
    class_proportions: dict[str, float]
    source_groups: dict[str, int]
    excluded_count: int
    duplicate_count: int
    parse_rejected_count: int
    label_conflict_count: int
    exclusion_scope: Literal["source_corpus_before_split"]
    source_archives: list[PublicArchive]
    historical_notice: str


class DescriptiveGroup(BaseModel):
    n: int
    mean: float | None
    median: float | None
    mode: float | None
    mode_tied: bool
    min: float | None
    max: float | None
    q1: float | None
    q3: float | None
    iqr: float | None
    sample_variance: float | None
    sample_std: float | None
    notes: list[str]


class StatisticsResponse(BaseModel):
    scope: Scope
    metric: CountMetric
    unit: str
    groups: dict[str, DescriptiveGroup]


class HistogramBin(BaseModel):
    lower: float
    upper: float
    count: int


class WordFrequency(BaseModel):
    word: str
    count: int


class DistributionResponse(BaseModel):
    scope: Scope
    metric: Literal["character_count", "token_count", "top_words"]
    class_label: Literal["all", "ham", "spam"]
    selected_records: int
    frequency_type: str | None
    unit: str
    items: list[WordFrequency]
    bins: list[HistogramBin]
    boxplot: dict[str, float] | None
    bin_closure: str | None = None
