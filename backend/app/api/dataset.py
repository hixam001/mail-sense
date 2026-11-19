"""Verified aggregate-only dataset routes."""

from collections import Counter
from typing import Literal

from fastapi import APIRouter, Query, Request

from app.schemas.analytics import DatasetSummary, DistributionResponse, StatisticsResponse
from app.schemas.common import CountMetric, Scope
from app.services.analytics_data import select_records
from app.services.corpus_sources import CANONICAL
from app.services.descriptive import descriptive_statistics
from app.services.distributions import distributions

router = APIRouter(prefix="/api/v1/dataset", tags=["Dataset"])


@router.get("/summary", response_model=DatasetSummary)
def summary(request: Request, scope: Scope = "all"):
    rows, manifest, report, sources = request.app.state.mail_sense.dataset_snapshot()
    selected = select_records(rows, scope)
    counts = Counter(row["label"] for row in selected)
    total = len(selected)
    duplicates, conflicts = (
        report["duplicate_records_excluded"],
        report["conflicting_records_excluded"],
    )
    parse_rejections = report["parse_rejections"]
    return dict(
        scope=scope,
        dataset_id=manifest["dataset_id"],
        split_id=manifest["split_id"],
        total=total,
        class_counts={label: counts[label] for label in ("spam", "ham")},
        class_proportions={label: counts[label] / total for label in ("spam", "ham")},
        source_groups={
            group: sum(row["source_group"] == group for row in selected) for group in CANONICAL
        },
        excluded_count=parse_rejections + duplicates + conflicts,
        duplicate_count=duplicates,
        parse_rejected_count=parse_rejections,
        label_conflict_count=conflicts,
        exclusion_scope="source_corpus_before_split",
        source_archives=sources["archives"],
        historical_notice=(
            "Historical curated corpus; class fractions are not modern inbox prevalence."
        ),
    )


@router.get("/statistics", response_model=StatisticsResponse)
def statistics(request: Request, scope: Scope = "all", metric: CountMetric = "token_count"):
    rows, _, _, _ = request.app.state.mail_sense.dataset_snapshot()
    return descriptive_statistics(rows, scope, metric)


@router.get("/distributions", response_model=DistributionResponse)
def distribution(
    request: Request,
    metric: Literal["character_count", "token_count", "top_words"] = Query(...),
    scope: Scope = "all",
    class_label: Literal["all", "ham", "spam"] = "all",
    top_n: int = Query(15, ge=1, le=30),
):
    rows, _, _, _ = request.app.state.mail_sense.dataset_snapshot()
    return distributions(rows, scope, metric, class_label, top_n)
