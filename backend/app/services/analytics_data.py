"""Shared validation and subset selection for pure statistical services."""

SCOPES = {"all", "train", "test"}
METRICS = {"character_count": "characters/email", "token_count": "tokens/email"}


def select_records(rows, scope="all", class_label="all"):
    if scope not in SCOPES or class_label not in {"all", "ham", "spam"}:
        raise ValueError("invalid_subset")
    selected = []
    for row in rows:
        if row.get("label") not in {"ham", "spam"}:
            raise ValueError("invalid_record_label")
        if scope != "all" and row.get("split") not in {"train", "test"}:
            raise ValueError("missing_record_split")
        if (scope == "all" or row["split"] == scope) and (
            class_label == "all" or row["label"] == class_label
        ):
            selected.append(row)
    return selected


def metric_unit(metric):
    if metric not in METRICS:
        raise ValueError("invalid_metric")
    return METRICS[metric]
