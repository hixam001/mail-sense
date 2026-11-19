"""Independent release arithmetic/refit over fixed local inputs; never prints mail."""

import argparse
import csv
import hashlib
import io
import json
import math
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import BernoulliNB, MultinomialNB

ROOT = Path(__file__).resolve().parents[2]
REPORT = "artifacts/reports/reproducibility.json"


def checked_bytes(name, limit):
    path = ROOT
    for part in Path(name).parts:
        path /= part
        assert not path.is_symlink(), "linked_input"
    assert path.resolve().is_relative_to(ROOT) and path.is_file(), "invalid_input"
    with path.open("rb") as stream:
        value = stream.read(limit + 1)
    assert len(value) <= limit, "input_limit"
    return value


def digest(value):
    return hashlib.sha256(value).hexdigest()


def rates(tn, fp, fn, tp):
    def divide(n, d):
        return n / d if d else None

    return dict(
        accuracy=divide(tn + tp, tn + fp + fn + tp),
        precision=divide(tp, tp + fp),
        recall=divide(tp, tp + fn),
        f1=divide(2 * tp, 2 * tp + fp + fn),
        false_positive_rate=divide(fp, fp + tn),
    )


def hand_math(reference):
    values = [2, 4, 4, 6]
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    assert mean == 4 and math.isclose(variance, 8 / 3)
    observed = [[180, 120], [70, 630]]
    expected = [[75, 225], [175, 525]]
    terms = [
        (observed[i][j] - expected[i][j]) ** 2 / expected[i][j] for i in range(2) for j in range(2)
    ]
    assert terms == [147, 49, 63, 21] and sum(terms) == 280
    p_value = math.erfc(math.sqrt(sum(terms) / 2))
    synthetic = reference["synthetic_examples"]
    descriptive = dict(
        mean=mean,
        median=(values[1] + values[2]) / 2,
        mode=4,
        q1=2 + 0.75 * (4 - 2),
        q3=4 + 0.25 * (6 - 4),
        sample_variance=variance,
        sample_std=math.sqrt(variance),
    )
    for key, value in descriptive.items():
        assert math.isclose(value, synthetic["descriptive"][key], rel_tol=1e-14)
    assert math.isclose(p_value, synthetic["chi_square"]["p_value"], rel_tol=1e-12)
    posterior = (180 / 300) * (300 / 1000) / (250 / 1000)
    assert posterior == 0.72
    assert synthetic["contingency"]["probabilities"]["p_spam_given_word"]["value"] == posterior
    low, high = 0.0, 10.0
    for _ in range(70):
        middle = (low + high) / 2
        if (1 + math.erf(middle / math.sqrt(2))) / 2 < 0.975:
            low = middle
        else:
            high = middle
    z = (low + high) / 2
    p, n = 0.3, 1000
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    bounds = [center - half, center + half]
    for name, value in zip(("lower", "upper"), bounds, strict=True):
        assert math.isclose(value, synthetic["wilson"][name], rel_tol=1e-12)
    pmf = math.comb(10, 1) * 0.25 * 0.75**9
    assert math.isclose(pmf, 0.1877117156982422, rel_tol=1e-14)
    assert math.isclose(pmf, synthetic["binomial"]["binomial_pmf"], rel_tol=1e-14)
    return dict(
        mean=mean,
        median=4,
        mode=4,
        q1=3.5,
        q3=4.5,
        sample_variance=variance,
        sample_std=math.sqrt(variance),
        posterior=posterior,
        chi_square_terms=terms,
        chi_square_p=p_value,
        wilson_z=z,
        wilson_bounds=bounds,
        binomial_pmf=pmf,
        metric_fixture=rates(135, 5, 10, 50),
    )


def build():
    sources = json.loads(checked_bytes("data/processed/source_manifest.json", 131072))
    archives = []
    groups = {item["source_group"]: item for item in sources["archives"]}
    assert set(groups) == {"easy_ham", "easy_ham_2", "hard_ham", "spam", "spam_2"}
    for archive in sources["archives"]:
        name = archive["archive_name"]
        assert archive["source_url"] == "https://spamassassin.apache.org/old/publiccorpus/" + name
        value = checked_bytes("data/raw/" + name, 32 * 1024 * 1024)
        assert digest(value) == archive["sha256"] and len(value) == archive["size_bytes"]
        archives.append(dict(name=name, sha256=digest(value), size_bytes=len(value)))
    dataset_bytes = checked_bytes("data/processed/messages.csv", 512 * 1024 * 1024)
    csv.field_size_limit(1_000_000)
    rows = sorted(
        csv.DictReader(io.StringIO(dataset_bytes.decode("utf-8"))),
        key=lambda row: row["message_id"],
    )
    dedup = json.loads(checked_bytes("data/processed/deduplication_report.json", 32 * 1024 * 1024))
    assert digest(dataset_bytes) == dedup["records_sha256"]
    assert dedup["input_records"] == sum(item["files_accepted"] for item in groups.values())
    assert dedup["parse_rejections"] == sum(item["files_rejected"] for item in groups.values())
    assert len(rows) == dedup["retained_records"] == 5862
    assert dedup["input_records"] - dedup["duplicate_records_excluded"] - dedup[
        "conflicting_records_excluded"
    ] == len(rows)
    assert (
        len({row["message_id"] for row in rows})
        == len({row["content_sha256"] for row in rows})
        == len(rows)
    )
    tokenizer = re.compile(r"(?u)\b\w\w+\b")
    for row in rows:
        text = row["model_text"]
        assert digest(text.encode()) == row["content_sha256"]
        assert len(text) == int(row["character_count"])
        assert len(tokenizer.findall(text.lower())) == int(row["token_count"])
        assert row["source_group"] in groups
        assert row["label"] == groups[row["source_group"]]["label"]
        assert row["source_archive"] == groups[row["source_group"]]["archive_name"]
    split = json.loads(checked_bytes("data/processed/split_manifest.json", 16 * 1024 * 1024))
    train_ids, test_ids = set(split["train_ids"]), set(split["test_ids"])
    assert not train_ids & test_ids and train_ids | test_ids == {row["message_id"] for row in rows}
    partitions = train_test_split(
        [row["message_id"] for row in rows],
        test_size=0.2,
        random_state=42,
        stratify=[row["label"] for row in rows],
    )
    assert set(partitions[0]) == train_ids and set(partitions[1]) == test_ids
    for subset in ("train", "test"):
        assert (
            digest("".join(item + "\n" for item in split[subset + "_ids"]).encode())
            == split[subset + "_ids_sha256"]
        )
    train = [row for row in rows if row["message_id"] in train_ids]
    test = [row for row in rows if row["message_id"] in test_ids]
    assert not {row["content_sha256"] for row in train} & {row["content_sha256"] for row in test}
    names = dict(
        vectorizer="vectorizer.joblib",
        multinomial="multinomial.joblib",
        bernoulli="bernoulli.joblib",
    )
    metadata_bytes = checked_bytes("artifacts/models/metadata.json", 131072)
    metadata = json.loads(metadata_bytes)
    assert metadata["dataset_id"] == split["dataset_id"] == dedup["dataset_id"]
    assert metadata["split_id"] == split["split_id"]
    assert all(
        metadata[name + "_ids_sha256"] == split[name + "_ids_sha256"] for name in ("train", "test")
    )
    blobs = {
        key: checked_bytes("artifacts/models/" + name, 64 * 1024 * 1024)
        for key, name in names.items()
    }
    for name, blob in blobs.items():
        assert digest(blob) == metadata["files"][name]["sha256"]
        assert len(blob) == metadata["files"][name]["size_bytes"]
    stored = {key: joblib.load(io.BytesIO(value)) for key, value in blobs.items()}
    vectorizer = CountVectorizer(
        lowercase=True,
        token_pattern=r"(?u)\b\w\w+\b",
        strip_accents=None,
        stop_words=None,
        ngram_range=(1, 1),
        min_df=1,
        max_df=1.0,
        dtype=np.int64,
    )
    x_train = vectorizer.fit_transform([row["model_text"] for row in train])
    x_test = vectorizer.transform([row["model_text"] for row in test])
    assert vectorizer.vocabulary_ == stored["vectorizer"].vocabulary_
    vocabulary_hash = digest(
        json.dumps(
            [[word, int(index)] for word, index in sorted(vectorizer.vocabulary_.items())],
            separators=(",", ":"),
        ).encode()
    )
    assert vocabulary_hash == metadata["features"]["vocabulary_sha256"]
    assert len(vectorizer.vocabulary_) == metadata["features"]["feature_count"]
    train_words = {word for row in train for word in tokenizer.findall(row["model_text"].lower())}
    test_words = {word for row in test for word in tokenizer.findall(row["model_text"].lower())}
    assert train_words == set(vectorizer.vocabulary_) and not (test_words - train_words) & set(
        vectorizer.vocabulary_
    )
    labels = [row["label"] for row in train]
    expected = json.loads(checked_bytes("artifacts/reports/evaluation.json", 131072))
    assert expected["artifact_id"] == metadata["artifact_id"]
    assert expected["split_id"] == split["split_id"] and expected["test_count"] == len(test)
    metrics = {}
    for name, estimator, training, testing in (
        ("multinomial", MultinomialNB(alpha=1, force_alpha=True, fit_prior=True), x_train, x_test),
        (
            "bernoulli",
            BernoulliNB(alpha=1, force_alpha=True, fit_prior=True, binarize=None),
            (x_train > 0).astype(np.int64),
            (x_test > 0).astype(np.int64),
        ),
    ):
        estimator.fit(training, labels)
        for attribute in (
            "class_count_",
            "class_log_prior_",
            "feature_count_",
            "feature_log_prob_",
        ):
            assert np.array_equal(
                getattr(estimator, attribute), getattr(stored[name], attribute)
            ), "refit_mismatch"
        predicted = estimator.predict(testing).tolist()
        assert predicted == stored[name].predict(testing).tolist()
        counts = Counter(
            (row["label"], prediction) for row, prediction in zip(test, predicted, strict=True)
        )
        matrix = dict(
            tn=counts["ham", "ham"],
            fp=counts["ham", "spam"],
            fn=counts["spam", "ham"],
            tp=counts["spam", "spam"],
        )
        measured = rates(**matrix)
        assert matrix == expected["models"][name]["confusion_matrix"]
        for key, value in measured.items():
            assert math.isclose(value, expected["models"][name][key], rel_tol=1e-14)
        metrics[name] = dict(confusion_matrix=matrix, **measured)
    assert checked_bytes("artifacts/models/metadata.json", 131072) == metadata_bytes
    assert all(
        checked_bytes("artifacts/models/" + names[key], 64 * 1024 * 1024) == value
        for key, value in blobs.items()
    )
    numerical = json.loads(checked_bytes("artifacts/reports/statistics_verification.json", 131072))
    free = Counter(
        row["label"] for row in rows if "free" in set(tokenizer.findall(row["model_text"].lower()))
    )
    for scope, selected in (("all", rows), ("train", train), ("test", test)):
        table = Counter(
            (row["label"], "free" in set(tokenizer.findall(row["model_text"].lower())))
            for row in selected
        )
        counts = {
            f"{label}_{'present' if present else 'absent'}": table[label, present]
            for label in ("spam", "ham")
            for present in (True, False)
        }
        known = numerical["measured"]["scopes"][scope]["free_word"]
        assert counts == known["counts"]
        assert (
            counts["spam_present"] / (counts["spam_present"] + counts["ham_present"])
            == known["probabilities"]["p_spam_given_word"]["value"]
        )
    assert checked_bytes("data/processed/messages.csv", 512 * 1024 * 1024) == dataset_bytes
    sample = (
        "Subject: Project meeting\nHello team, please review the project notes "
        "before our meeting tomorrow. Thank you."
    )
    sample_counts = stored["vectorizer"].transform([sample])
    sample_models = {}
    for name in ("multinomial", "bernoulli"):
        values = (sample_counts > 0).astype(np.int64) if name == "bernoulli" else sample_counts
        model = stored[name]
        spam_index = model.classes_.tolist().index("spam")
        sample_models[name] = dict(
            prediction=str(model.predict(values)[0]),
            spam_probability=float(model.predict_proba(values)[0, spam_index]),
        )
    return dict(
        task="MSE-603",
        verification="independent-v1",
        archive_hashes=archives,
        dataset_id=split["dataset_id"],
        split_id=split["split_id"],
        artifact_id=metadata["artifact_id"],
        retained_records=len(rows),
        classes=dict(Counter(row["label"] for row in rows)),
        train_records=len(train),
        test_records=len(test),
        training_features=len(train_words),
        held_out_only_tokens_excluded=len(test_words - train_words),
        vocabulary_sha256=vocabulary_hash,
        free_document_counts=dict(free),
        synthetic_example=dict(
            kind="authored_teaching_text",
            text=sample,
            intended_class="ham",
            models=sample_models,
            included_in_held_out_metrics=False,
        ),
        hand_math=hand_math(numerical),
        models=metrics,
        checks=dict(
            archive_checksums=True,
            exact_deduplication=True,
            split_reproduced=True,
            train_test_ids_and_content_disjoint=True,
            all_record_hashes_and_counts=True,
            training_only_vocabulary=True,
            independent_refit_arrays_identical=True,
            held_out_predictions_and_metrics_identical=True,
            private_artifacts_unchanged=True,
        ),
        result="pass",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "verify"])
    args = parser.parse_args()
    try:
        report = build()
        path = ROOT / REPORT
        assert not path.is_symlink() and path.resolve().is_relative_to(ROOT)
        if args.command == "run":
            report["checked_at"] = datetime.now(UTC).isoformat()
            path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
        else:
            existing = json.loads(path.read_text())
            stamp = datetime.fromisoformat(existing.pop("checked_at"))
            assert stamp.tzinfo is not None and stamp.utcoffset().total_seconds() == 0
            assert existing == report
    except (OSError, ValueError, KeyError, TypeError, AssertionError, csv.Error):
        print("Independent scientific verification failed: mismatch_or_invalid_local_inputs")
        return 1
    print(
        "Independent arithmetic, corpus provenance, split, "
        "train-only refits and held-out metrics: PASS"
    )
    print(f"Public aggregate report: {REPORT}; private inputs/artifacts unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
