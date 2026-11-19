"""Aggregate numeric distributions and word document frequencies without raw records."""

from bisect import bisect_right
from collections import Counter

from app.services.analytics_data import metric_unit, select_records
from app.services.corpus_split import load_split_dataset
from app.services.descriptive import summarize
from app.services.text_features import tokenize


def distributions(rows, scope="all", metric="token_count", class_label="all", top_n=15):
    if type(top_n) is not int or not 1 <= top_n <= 30:
        raise ValueError("invalid_top_n")
    selected = select_records(rows, scope, class_label)
    result = dict(
        scope=scope,
        metric=metric,
        class_label=class_label,
        selected_records=len(selected),
        items=[],
        bins=[],
        boxplot=None,
    )
    if metric == "top_words":
        counts = Counter(word for row in selected for word in set(tokenize(row["model_text"])))
        result.update(
            frequency_type="document_frequency",
            unit="documents",
            items=[
                {"word": word, "count": count}
                for word, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[
                    :top_n
                ]
            ],
        )
        return result
    result.update(
        unit=metric_unit(metric),
        frequency_type=None,
        bin_closure="left_closed_right_open_last_closed",
    )
    values = [row[metric] for row in selected]
    summary = summarize(values)
    if not values:
        return result
    low, high = summary["min"], summary["max"]
    edges = (
        [low, low + 1]
        if low == high
        else [low + (high - low) * index / 10 for index in range(10)] + [high]
    )
    counts = [0] * (len(edges) - 1)
    for value in values:
        counts[min(bisect_right(edges, value) - 1, len(counts) - 1)] += 1
    result["bins"] = [
        dict(lower=edges[i], upper=edges[i + 1], count=count) for i, count in enumerate(counts)
    ]
    result["boxplot"] = {key: summary[key] for key in ("min", "q1", "median", "q3", "max")}
    return result


def dataset_distributions(root, scope="all", metric="token_count", class_label="all", top_n=15):
    rows, _ = load_split_dataset(root, scope)
    return distributions(rows, scope, metric, class_label, top_n)
