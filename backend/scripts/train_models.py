"""Fit or verify the trusted local vectorizer and both Naive Bayes models."""

import argparse
import sys
from pathlib import Path

from app.services.model_store import load_models, prepare_models

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "verify"])
    args = parser.parse_args()
    try:
        loaded = {"run": prepare_models, "verify": load_models}[args.command](ROOT)
    except (OSError, ValueError, KeyError, TypeError):
        print(
            "Model preparation failed: missing_invalid_or_incompatible_artifacts", file=sys.stderr
        )
        return 1
    features = loaded.metadata["features"]
    print(
        f"Verified both models: {features['training_record_count']:,} training rows, "
        f"{features['feature_count']:,} shared features; alpha=1."
    )
    print("Private artifacts: artifacts/models/ (ignored); held-out evaluation is a separate step.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
