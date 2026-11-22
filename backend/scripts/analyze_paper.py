"""Secondary paired analysis of frozen models; publish aggregates, never mail."""

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from statistics import NormalDist

import numpy as np
from scipy.stats import binomtest

from app.services.corpus_split import load_split_dataset
from app.services.model_store import load_models

ROOT = Path(__file__).resolve().parents[2]
REPORT = "artifacts/reports/paper_statistics.json"
SEED = 20261122
REPLICATES = 10_000


def wilson(successes, n):
    if not 0 <= successes <= n or n <= 0:
        raise ValueError("invalid_binomial_counts")
    p = successes / n
    z = NormalDist().inv_cdf(0.975)
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return {"estimate": p, "lower": max(0, center - half), "upper": min(1, center + half)}


def exact_p(m_only, b_only):
    if min(m_only, b_only) < 0:
        raise ValueError("invalid_discordant_counts")
    n = m_only + b_only
    return float(binomtest(m_only, n, 0.5).pvalue) if n else 1.0


def paired_analysis(actual, multinomial, bernoulli, *, replicates=REPLICATES, seed=SEED):
    if not len(actual) == len(multinomial) == len(bernoulli) or replicates < 100:
        raise ValueError("invalid_paired_input")
    counts = {label: Counter() for label in ("ham", "spam")}
    for truth, m, b in zip(actual, multinomial, bernoulli, strict=True):
        if truth not in counts or m not in counts or b not in counts:
            raise ValueError("invalid_label")
        category = (
            "both_correct"
            if m == b == truth
            else "multinomial_only"
            if m == truth
            else "bernoulli_only"
            if b == truth
            else "both_wrong"
        )
        counts[truth][category] += 1
    order = ["both_correct", "multinomial_only", "bernoulli_only", "both_wrong"]
    groups = {label: {key: counts[label][key] for key in order} for label in counts}
    sizes = {label: sum(group.values()) for label, group in groups.items()}
    if not min(sizes.values()):
        raise ValueError("both_actual_classes_required")
    total = Counter()
    for group in groups.values():
        total.update(group)
    generator = np.random.default_rng(seed)
    draws = {}
    for label, group in groups.items():
        probabilities = np.array(list(group.values()), dtype=float) / sizes[label]
        sampled = generator.multinomial(sizes[label], probabilities, size=replicates)
        draws[label] = sampled[:, 1] - sampled[:, 2]
    differences = {
        "accuracy": (draws["ham"] + draws["spam"]) / len(actual),
        "recall": draws["spam"] / sizes["spam"],
        "false_positive_rate": -draws["ham"] / sizes["ham"],
    }
    estimates = {
        "accuracy": (total["multinomial_only"] - total["bernoulli_only"]) / len(actual),
        "recall": (groups["spam"]["multinomial_only"] - groups["spam"]["bernoulli_only"])
        / sizes["spam"],
        "false_positive_rate": (groups["ham"]["bernoulli_only"] - groups["ham"]["multinomial_only"])
        / sizes["ham"],
    }
    return {
        "by_actual_class": groups,
        "overall": dict(total),
        "exact_mcnemar_p": exact_p(total["multinomial_only"], total["bernoulli_only"]),
        "discordant_pairs": total["multinomial_only"] + total["bernoulli_only"],
        "bootstrap": {
            "method": "class-stratified paired nonparametric percentile",
            "equivalence": (
                "Multinomial counts over paired correctness cells resample message pairs."
            ),
            "replicates": replicates,
            "seed": seed,
            "confidence": 0.95,
            "direction": "multinomial_minus_bernoulli",
            "quantile_method": "linear",
            "differences": {
                key: {
                    "estimate": estimates[key],
                    "lower": float(np.quantile(values, 0.025, method="linear")),
                    "upper": float(np.quantile(values, 0.975, method="linear")),
                }
                for key, values in differences.items()
            },
        },
    }


def association(a, b, c, d):
    if min(a, b, c, d) <= 0:
        raise ValueError("positive_cells_required_for_log_odds_interval")
    n = a + b + c + d
    expected = [
        (a + b) * (a + c) / n,
        (a + b) * (b + d) / n,
        (c + d) * (a + c) / n,
        (c + d) * (b + d) / n,
    ]
    chi = sum((o - e) ** 2 / e for o, e in zip((a, b, c, d), expected, strict=True))
    odds_ratio = a * d / (b * c)
    error = NormalDist().inv_cdf(0.975) * math.sqrt(sum(1 / x for x in (a, b, c, d)))
    return {
        "observed": [[a, b], [c, d]],
        "expected": expected,
        "chi_square": chi,
        "degrees_of_freedom": 1,
        "p_value": math.erfc(math.sqrt(chi / 2)),
        "phi": math.sqrt(chi / n),
        "odds_ratio": odds_ratio,
        "odds_ratio_interval": [
            math.exp(math.log(odds_ratio) - error),
            math.exp(math.log(odds_ratio) + error),
        ],
        "interval_method": "95% normal approximation on log odds ratio",
        "p_spam_given_present": a / (a + c),
        "p_spam_given_absent": b / (b + d),
    }


def build():
    tracked = [ROOT / "data/processed/messages.csv", *(ROOT / "artifacts/models").glob("*")]
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked if p.is_file()}
    loaded = load_models(ROOT)
    rows, split = load_split_dataset(ROOT, "test")
    assert [row["message_id"] for row in rows] == split["test_ids"]
    x = loaded.vectorizer.transform([row["model_text"] for row in rows])
    actual = [row["label"] for row in rows]
    predicted = {
        name: model.predict((x > 0).astype(np.int64) if name == "bernoulli" else x).tolist()
        for name, model in loaded.models.items()
    }
    evaluation_bytes = (ROOT / "artifacts/reports/evaluation.json").read_bytes()
    evaluation = json.loads(evaluation_bytes)
    assert evaluation["artifact_id"] == loaded.metadata["artifact_id"]
    assert evaluation["test_ids_sha256"] == split["test_ids_sha256"]
    model_results = {}
    for name, values in predicted.items():
        table = Counter(zip(actual, values, strict=True))
        tn, fp, fn, tp = [
            table[pair]
            for pair in (("ham", "ham"), ("ham", "spam"), ("spam", "ham"), ("spam", "spam"))
        ]
        matrix = dict(tn=tn, fp=fp, fn=fn, tp=tp)
        assert matrix == evaluation["models"][name]["confusion_matrix"]
        model_results[name] = {
            "confusion_matrix": matrix,
            "accuracy": wilson(tp + tn, len(rows)),
            "precision": wilson(tp, tp + fp),
            "recall": wilson(tp, tp + fn),
            "false_positive_rate": wilson(fp, fp + tn),
            "f1": 2 * tp / (2 * tp + fp + fn),
        }
    numerical = json.loads((ROOT / "artifacts/reports/statistics_verification.json").read_text())
    assert numerical["measured"]["dataset_id"] == split["dataset_id"]
    assert numerical["measured"]["split_id"] == split["split_id"]
    counts = numerical["measured"]["scopes"]["all"]["free_word"]["counts"]
    word = association(
        *[counts[key] for key in ("spam_present", "spam_absent", "ham_present", "ham_absent")]
    )
    assert math.isclose(
        word["chi_square"],
        numerical["measured"]["scopes"]["all"]["free_chi_square"]["chi_square"],
        rel_tol=1e-12,
    )
    assert all(hashlib.sha256(p.read_bytes()).hexdigest() == sha for p, sha in before.items())
    return {
        "task": "MSE-607",
        "analysis_version": "paper-secondary-v1",
        "result": "pass",
        "protocol": "Exploratory extension of inspected v1.0 holdout; no fitting or tuning.",
        "dataset_id": split["dataset_id"],
        "split_id": split["split_id"],
        "artifact_id": loaded.metadata["artifact_id"],
        "test_ids_sha256": split["test_ids_sha256"],
        "evaluation_sha256": hashlib.sha256(evaluation_bytes).hexdigest(),
        "test_count": len(rows),
        "test_counts": dict(Counter(actual)),
        "models": model_results,
        "cost_sensitivity": {
            "false_negative_unit_cost": 1,
            "observed_break_even_false_positive_cost": 56,
            "loss_difference_multinomial_minus_bernoulli": "lambda - 56",
            "examples": {
                str(cost): {
                    name: values["confusion_matrix"]["fp"] * cost + values["confusion_matrix"]["fn"]
                    for name, values in model_results.items()
                }
                for cost in (1, 10, 56, 100)
            },
            "interpretation": "Post-hoc empirical sensitivity; no estimated user costs or tuning.",
        },
        "paired": paired_analysis(actual, predicted["multinomial"], predicted["bernoulli"]),
        "word_association": {"word": "free", "scope": "all", **word},
        "private_artifacts_unchanged": True,
        "limitations": [
            "Intervals/test assume independent messages; threads/near duplicates may violate this.",
            (
                "Bootstrap conditions on trained models and class counts; "
                "no training or temporal variance."
            ),
            "Word and comparison analyses are exploratory, with no modern population inference.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "verify"])
    args = parser.parse_args()
    report = build()
    path = ROOT / REPORT
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
        raise ValueError("invalid_report_path")
    if args.command == "run":
        path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    else:
        assert json.loads(path.read_text()) == report, "paper_analysis_mismatch"
    print(
        "Frozen paired predictions, exact test, bootstrap intervals and association effects: PASS"
    )
    print(json.dumps(report["paired"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
