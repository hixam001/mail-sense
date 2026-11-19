"""Descriptive count statistics with explicit undefined small-sample results."""

import math
import statistics as stats
from collections import Counter
from numbers import Real

from app.services.analytics_data import metric_unit, select_records
from app.services.corpus_split import load_split_dataset


def summarize(values):
    values = list(values)
    if any(
        isinstance(v, bool) or not isinstance(v, Real) or not math.isfinite(v) or v < 0
        for v in values
    ):
        raise ValueError("invalid_measurements")
    ordered, n = sorted(values), len(values)
    result = dict.fromkeys(
        ("mean", "median", "mode", "min", "max", "q1", "q3", "iqr", "sample_variance", "sample_std")
    )
    result.update(n=n, mode_tied=False, notes=[])
    if not n:
        result["notes"] = ["No observations in selected subset."]
        return result

    def quantile(p):
        position = (n - 1) * p
        lower, upper = math.floor(position), math.ceil(position)
        return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)

    frequencies = Counter(values)
    peak = max(frequencies.values())
    modes = [v for v, frequency in frequencies.items() if frequency == peak]
    try:
        variance = stats.variance(values) if n > 1 else None
        result.update(
            mean=stats.fmean(values),
            median=stats.median(values),
            mode=min(modes),
            mode_tied=len(modes) > 1,
            min=ordered[0],
            max=ordered[-1],
            q1=quantile(0.25),
            q3=quantile(0.75),
            sample_variance=variance,
            sample_std=math.sqrt(variance) if variance is not None else None,
        )
        result["iqr"] = result["q3"] - result["q1"]
    except (OverflowError, ValueError) as error:
        raise ValueError("invalid_measurements") from error
    if any(not math.isfinite(v) for v in result.values() if isinstance(v, Real)):
        raise ValueError("invalid_measurements")
    if n < 2:
        result["notes"] = [
            "Sample variance and standard deviation require at least 2 observations."
        ]
    return result


def descriptive_statistics(rows, scope="all", metric="token_count"):
    unit = metric_unit(metric)
    selected = select_records(rows, scope)
    return {
        "scope": scope,
        "metric": metric,
        "unit": unit,
        "groups": {
            label: summarize(row[metric] for row in selected if row["label"] == label)
            for label in ("spam", "ham")
        },
    }


def dataset_statistics(root, scope="all", metric="token_count"):
    rows, _ = load_split_dataset(root, scope)
    return descriptive_statistics(rows, scope, metric)
