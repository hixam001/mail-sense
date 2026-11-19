"""Verified local snapshots cached by content hashes, with truthful degraded readiness."""

import hashlib
import json
from pathlib import Path
from threading import RLock

from app.api.errors import ApiError
from app.services.corpus_dataset import DATASET_FILE, DATASET_REPORT_FILE
from app.services.corpus_ingest import MANIFEST_FILE, RECORD_FILE, REPORT_FILE
from app.services.corpus_sources import CANONICAL
from app.services.corpus_split import SPLIT_FILE, load_split_dataset
from app.services.evaluation import EVALUATION_FILE, evaluate_loaded
from app.services.model_store import METADATA_FILE, MODEL_DIR, MODEL_FILES, load_models

DATA_FILES = [f"data/raw/{filename}" for filename, _ in CANONICAL.values()] + [
    MANIFEST_FILE,
    RECORD_FILE,
    REPORT_FILE,
    DATASET_FILE,
    DATASET_REPORT_FILE,
    SPLIT_FILE,
]
MODEL_PATHS = [f"{MODEL_DIR}/{filename}" for filename in (*MODEL_FILES.values(), METADATA_FILE)]


class ApplicationState:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.lock = RLock()
        self.rows = self.manifest = self.models = self.evaluation = None
        self.dataset_report = self.sources = None
        self._dataset_stamp = self._model_stamp = self._evaluation_stamp = object()

    def _fingerprint(self, names):
        fingerprints = []
        try:
            for name in names:
                path = self.root
                for part in Path(name).parts:
                    path /= part
                    if path.is_symlink():
                        return None
                if not path.is_file() or path.stat().st_size > 512 * 1024 * 1024:
                    return None
                with path.open("rb") as stream:
                    fingerprints.append((name, hashlib.file_digest(stream, "sha256").hexdigest()))
        except OSError:
            return None
        return tuple(fingerprints)

    def _read_json(self, name, limit):
        with (self.root / name).open("rb") as stream:
            content = stream.read(limit + 1)
        if len(content) > limit:
            raise ValueError("metadata_size_limit")
        return json.loads(content)

    def refresh(self):
        with self.lock:
            if (self.root / "data/raw/.acquisition.lock").exists():
                self.rows = self.manifest = self.models = self.evaluation = None
                self._dataset_stamp = self._model_stamp = self._evaluation_stamp = None
                return self
            dataset_stamp = self._fingerprint(DATA_FILES)
            if dataset_stamp != self._dataset_stamp:
                self._dataset_stamp = dataset_stamp
                self.rows = self.manifest = None
                self.dataset_report = self.sources = None
                if dataset_stamp is not None:
                    try:
                        self.rows, self.manifest = load_split_dataset(self.root)
                        self.dataset_report = self._read_json(DATASET_REPORT_FILE, 32 * 1024 * 1024)
                        self.sources = self._read_json(MANIFEST_FILE, 128 * 1024)
                    except (OSError, ValueError, KeyError, TypeError):
                        self.rows = self.manifest = None
            model_stamp = (dataset_stamp, self._fingerprint(MODEL_PATHS)) if self.rows else None
            if model_stamp != self._model_stamp:
                self._model_stamp = model_stamp
                self.models = None
                if model_stamp is not None and model_stamp[1] is not None:
                    try:
                        self.models = load_models(self.root)
                    except (OSError, ValueError, KeyError, TypeError):
                        self.models = None
            evaluation_stamp = (
                (model_stamp, self._fingerprint([EVALUATION_FILE])) if self.models else None
            )
            if evaluation_stamp != self._evaluation_stamp:
                self._evaluation_stamp = evaluation_stamp
                self.evaluation = None
                if evaluation_stamp is not None and evaluation_stamp[1] is not None:
                    try:
                        actual = self._read_json(EVALUATION_FILE, 128 * 1024)
                        expected = evaluate_loaded(
                            self.models,
                            [r for r in self.rows if r["split"] == "test"],
                            self.manifest,
                        )
                        if json.dumps(actual, sort_keys=True) == json.dumps(
                            expected, sort_keys=True
                        ):
                            self.evaluation = expected
                    except (OSError, ValueError, KeyError, TypeError):
                        self.evaluation = None
            return self

    def health(self):
        self.refresh()
        with self.lock:
            dataset_ready, model_ready = bool(self.rows), self.models is not None
            evaluation_ready = self.evaluation is not None
            return dict(
                status="ready"
                if dataset_ready and model_ready and evaluation_ready
                else "degraded",
                dataset_ready=dataset_ready,
                models_ready={name: model_ready for name in ("multinomial", "bernoulli")},
                evaluation_ready=evaluation_ready,
                split_id=self.manifest["split_id"] if self.manifest else None,
            )

    def dataset_snapshot(self):
        self.refresh()
        with self.lock:
            if not self.rows:
                raise ApiError(
                    503, "DATASET_UNAVAILABLE", "Prepare and verify the local corpus first."
                )
            return self.rows, self.manifest, self.dataset_report, self.sources

    def model_snapshot(self):
        self.refresh()
        with self.lock:
            if self.models is None:
                raise ApiError(
                    503, "MODELS_UNAVAILABLE", "Prepare and verify both local models first."
                )
            return self.models

    def evaluation_snapshot(self):
        self.refresh()
        with self.lock:
            if self.evaluation is None:
                raise ApiError(
                    503, "EVALUATION_UNAVAILABLE", "Prepare and verify local evaluation first."
                )
            return self.evaluation
