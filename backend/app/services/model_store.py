"""Checksum-verified, project-created local model artifacts. Never load user uploads."""

import hashlib
import io
import json
import platform
import re
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import joblib
import numpy as np
import scipy
import sklearn
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import BernoulliNB, MultinomialNB

from app.services.corpus_ingest import publish_artifacts
from app.services.corpus_sources import corpus_lock
from app.services.corpus_split import SPLIT_FILE, verify_split
from app.services.model_features import build_features, feature_metadata, vocabulary_hash
from app.services.text_features import TOKEN_PATTERN
from app.services.training import train_bernoulli, train_multinomial

MODEL_DIR = "artifacts/models"
MODEL_FILES = {
    "vectorizer": "vectorizer.joblib",
    "multinomial": "multinomial.joblib",
    "bernoulli": "bernoulli.joblib",
}
METADATA_FILE = "metadata.json"
MAX_ARTIFACT_BYTES = 64 * 1024 * 1024
MAX_METADATA_BYTES = 128 * 1024


class ModelArtifactError(ValueError):
    """Fixed public artifact failure code; no private file/message content."""


@dataclass
class LoadedModels:
    vectorizer: CountVectorizer
    models: dict
    metadata: dict


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _digest(data):
    return {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}


def _paths(root):
    root = Path(root).resolve()
    folder = root / MODEL_DIR
    paths = [folder / name for name in (*MODEL_FILES.values(), METADATA_FILE)]
    if folder.is_symlink() or not folder.resolve().is_relative_to(root):
        raise ModelArtifactError("invalid_model_path")
    for path in paths:
        if path.is_symlink() or path.is_dir() or not path.resolve().is_relative_to(root):
            raise ModelArtifactError("invalid_model_path")
    return root, folder


def _read(path, maximum):
    if path.is_symlink() or not path.is_file():
        raise ModelArtifactError("missing_model_artifact")
    with path.open("rb") as stream:
        data = stream.read(maximum + 1)
    if not data or len(data) > maximum:
        raise ModelArtifactError("model_artifact_limit")
    return data


def _context(root, manifest):
    return {
        "schema_version": 1,
        "pipeline_version": "nb-v1",
        "dataset_id": manifest["dataset_id"],
        "split_id": manifest["split_id"],
        "train_ids_sha256": manifest["train_ids_sha256"],
        "test_ids_sha256": manifest["test_ids_sha256"],
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "sklearn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "inputs": {
            **manifest["inputs"],
            SPLIT_FILE: _digest(_read(root / SPLIT_FILE, MAX_ARTIFACT_BYTES)),
        },
    }


def _payload(root, manifest, features, files):
    context = _context(root, manifest)
    descriptors = {}
    for name, algorithm in (("multinomial", "MultinomialNB"), ("bernoulli", "BernoulliNB")):
        descriptors[name] = dict(
            algorithm=algorithm,
            alpha=1.0,
            classes=["ham", "spam"],
            dataset_id=manifest["dataset_id"],
            split_id=manifest["split_id"],
            vocabulary_sha256=features["vocabulary_sha256"],
            feature_count=features["feature_count"],
            training_record_count=manifest["train_records"],
            artifact_sha256=files[name]["sha256"],
        )
    return {**context, "features": features, "files": files, "models": descriptors}


def _validated_metadata(root, folder, manifest):
    metadata = json.loads(_read(folder / METADATA_FILE, MAX_METADATA_BYTES))
    try:
        if not isinstance(metadata, dict):
            raise ValueError
        features, files = metadata["features"], metadata["files"]
        if (
            not isinstance(features, dict)
            or not isinstance(files, dict)
            or set(files) != set(MODEL_FILES)
        ):
            raise ValueError
        for info in files.values():
            if (
                not isinstance(info, dict)
                or set(info) != {"sha256", "size_bytes"}
                or not isinstance(info["sha256"], str)
                or not re.fullmatch(r"[a-f0-9]{64}", info["sha256"])
                or type(info["size_bytes"]) is not int
                or not 0 < info["size_bytes"] <= MAX_ARTIFACT_BYTES
            ):
                raise ValueError
        if (
            type(features["feature_count"]) is not int
            or not 1 <= features["feature_count"] <= 1_000_000
            or not re.fullmatch(r"[a-f0-9]{64}", features["vocabulary_sha256"])
        ):
            raise ValueError
        expected_features = dict(
            tokenizer=manifest["tokenizer"],
            feature_count=features["feature_count"],
            vocabulary_sha256=features["vocabulary_sha256"],
            training_record_count=manifest["train_records"],
            test_record_count=manifest["test_records"],
        )
        payload = _payload(root, manifest, expected_features, files)
        acquired = datetime.fromisoformat(metadata["trained_at"])
        if acquired.utcoffset() != timedelta(0):
            raise ValueError
        expected = {
            **payload,
            "trained_at": metadata["trained_at"],
            "artifact_id": hashlib.sha256(_json(payload)).hexdigest(),
        }
        if _json(expected) != _json(metadata):
            raise ValueError
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        raise ModelArtifactError("model_metadata_mismatch") from error
    return metadata


def _validate_loaded(vectorizer, models, metadata, manifest):
    if type(vectorizer) is not CountVectorizer:
        raise ModelArtifactError("invalid_vectorizer")
    params = vectorizer.get_params()
    required = dict(
        lowercase=True,
        token_pattern=TOKEN_PATTERN,
        strip_accents=None,
        stop_words=None,
        ngram_range=(1, 1),
        min_df=1,
        max_df=1.0,
        max_features=None,
        tokenizer=None,
        preprocessor=None,
        vocabulary=None,
    )
    if any(params[key] != value for key, value in required.items()):
        raise ModelArtifactError("invalid_vectorizer_configuration")
    n = metadata["features"]["feature_count"]
    if (
        len(vectorizer.vocabulary_) != n
        or set(vectorizer.vocabulary_.values()) != set(range(n))
        or vocabulary_hash(vectorizer) != metadata["features"]["vocabulary_sha256"]
    ):
        raise ModelArtifactError("vocabulary_mismatch")
    for name, model in models.items():
        expected_type = MultinomialNB if name == "multinomial" else BernoulliNB
        counts = [manifest["train_counts"][label] for label in ("ham", "spam")]
        if (
            type(model) is not expected_type
            or model.alpha != 1.0
            or not model.fit_prior
            or list(model.classes_) != ["ham", "spam"]
            or model.n_features_in_ != n
            or model.feature_log_prob_.shape != (2, n)
            or not np.isfinite(model.feature_log_prob_).all()
            or not np.array_equal(model.class_count_, counts)
            or not np.allclose(np.exp(model.class_log_prior_), np.array(counts) / sum(counts))
            or (name == "bernoulli" and model.binarize is not None)
        ):
            raise ModelArtifactError("incompatible_model")


def load_models(root):
    root, folder = _paths(root)
    manifest = verify_split(root)
    metadata = _validated_metadata(root, folder, manifest)
    data = {}
    for name, filename in MODEL_FILES.items():
        data[name] = _read(folder / filename, MAX_ARTIFACT_BYTES)
        if _digest(data[name]) != metadata["files"][name]:
            raise ModelArtifactError("model_checksum_mismatch")
    # Every file is checked before any deserialization. Load these exact bytes,
    # not paths that could be replaced between hashing and deserialization.
    try:
        loaded = {name: joblib.load(io.BytesIO(value)) for name, value in data.items()}
        models = {name: loaded[name] for name in ("multinomial", "bernoulli")}
        _validate_loaded(loaded["vectorizer"], models, metadata, manifest)
    except ModelArtifactError:
        raise
    except Exception as error:
        raise ModelArtifactError("invalid_trusted_model_artifact") from error
    return LoadedModels(loaded["vectorizer"], models, metadata)


def prepare_models(root):
    root, folder = _paths(root)
    folder.mkdir(parents=True, exist_ok=True)
    with corpus_lock(root / "data/raw"):
        features, manifest = build_features(root)
        objects = {
            "vectorizer": features.vectorizer,
            "multinomial": train_multinomial(features),
            "bernoulli": train_bernoulli(features),
        }
        with tempfile.TemporaryDirectory(prefix=".models-", dir=folder) as temporary:
            staging = Path(temporary)
            files, pairs = {}, []
            for name, filename in MODEL_FILES.items():
                path = staging / filename
                joblib.dump(objects[name], path, compress=3)
                path.chmod(0o600)
                files[name] = _digest(_read(path, MAX_ARTIFACT_BYTES))
                pairs.append((path, folder / filename))
            payload = _payload(root, manifest, feature_metadata(features), files)
            artifact_id = hashlib.sha256(_json(payload)).hexdigest()
            if (folder / METADATA_FILE).exists():
                try:
                    existing = load_models(root)
                except (OSError, ValueError):
                    existing = None
                if existing is not None and existing.metadata["artifact_id"] == artifact_id:
                    return existing  # Preserve original training provenance on an identical fit.
            metadata = {
                **payload,
                "artifact_id": artifact_id,
                "trained_at": datetime.now(UTC).isoformat(),
            }
            output = staging / METADATA_FILE
            output.write_text(
                json.dumps(metadata, indent=2, sort_keys=True, allow_nan=False) + "\n",
                encoding="utf-8",
            )
            output.chmod(0o600)
            pairs.append((output, folder / METADATA_FILE))
            return publish_artifacts(pairs, staging, lambda: load_models(root))
