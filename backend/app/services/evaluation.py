"""Frozen held-out evaluation with explicit confusion counts and null denominators."""

import json
import tempfile
from pathlib import Path

from app.services.corpus_sources import corpus_lock
from app.services.corpus_split import load_split_dataset
from app.services.model_store import load_models
from app.services.training import binary_presence

EVALUATION_FILE = "artifacts/reports/evaluation.json"


def classification_metrics(actual, predicted):
    actual, predicted = list(actual), list(predicted)
    if len(actual) != len(predicted) or any(
        label not in {"ham", "spam"} for label in actual + predicted
    ):
        raise ValueError("invalid_evaluation_labels")
    counts = dict(tn=0, fp=0, fn=0, tp=0)
    for truth, guess in zip(actual, predicted, strict=True):
        key = (
            ("tp" if guess == "spam" else "fn")
            if truth == "spam"
            else ("fp" if guess == "spam" else "tn")
        )
        counts[key] += 1
    tn, fp, fn, tp = (counts[key] for key in ("tn", "fp", "fn", "tp"))
    notes = []

    def ratio(name, numerator, denominator):
        if not denominator:
            notes.append(f"{name} is undefined because its denominator is zero.")
            return None
        return numerator / denominator

    return dict(
        positive_class="spam",
        test_count=len(actual),
        confusion_matrix=counts,
        accuracy=ratio("Accuracy", tp + tn, len(actual)),
        precision=ratio("Precision", tp, tp + fp),
        recall=ratio("Recall", tp, tp + fn),
        f1=ratio("F1", 2 * tp, 2 * tp + fp + fn),
        false_positive_rate=ratio("False positive rate", fp, fp + tn),
        zero_division_policy="null_with_note",
        notes=notes,
    )


def build_evaluation(root):
    loaded = load_models(root)
    rows, manifest = load_split_dataset(root, "test")
    if (
        manifest["dataset_id"] != loaded.metadata["dataset_id"]
        or manifest["split_id"] != loaded.metadata["split_id"]
        or [row["message_id"] for row in rows] != manifest["test_ids"]
    ):
        raise ValueError("evaluation_split_mismatch")
    counts = loaded.vectorizer.transform([row["model_text"] for row in rows])
    actual = [row["label"] for row in rows]
    models = {}
    for name, model in loaded.models.items():
        x = binary_presence(counts) if name == "bernoulli" else counts
        predictions = model.predict(x).tolist()
        models[name] = {
            "model": name,
            "split_id": manifest["split_id"],
            "test_ids_sha256": manifest["test_ids_sha256"],
            **classification_metrics(actual, predictions),
        }
    return dict(
        schema_version=1,
        dataset_id=manifest["dataset_id"],
        split_id=manifest["split_id"],
        artifact_id=loaded.metadata["artifact_id"],
        test_ids_sha256=manifest["test_ids_sha256"],
        test_count=len(rows),
        positive_class="spam",
        same_test_ids=True,
        models=models,
        limitations=[
            "Historical curated corpus; scores do not establish modern robustness.",
            "Fixed alpha=1 and training-only vocabulary; no held-out tuning.",
            "Model probabilities are estimates, not calibrated certainty.",
        ],
    )


def _path(root):
    root = Path(root).resolve()
    path = root / EVALUATION_FILE
    if path.is_symlink() or not path.resolve().is_relative_to(root):
        raise ValueError("invalid_evaluation_path")
    return root, path


def prepare_evaluation(root):
    root, path = _path(root)
    with corpus_lock(root / "data/raw"):
        report = build_evaluation(root)
        data = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".evaluation-", dir=path.parent) as folder:
            output = Path(folder) / "evaluation.json"
            output.write_bytes(data)
            output.replace(path)
        return report


def verify_evaluation(root):
    root, path = _path(root)
    expected = build_evaluation(root)
    with path.open("rb") as stream:
        data = stream.read(128 * 1024 + 1)
    if len(data) > 128 * 1024:
        raise ValueError("evaluation_report_limit")
    if json.dumps(json.loads(data), sort_keys=True) != json.dumps(expected, sort_keys=True):
        raise ValueError("evaluation_report_mismatch")
    return expected
