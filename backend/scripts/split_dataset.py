"""Prepare or verify deterministic stratified split metadata; print aggregates only."""

import argparse
import sys
from pathlib import Path

from app.services.corpus_dataset import DatasetError
from app.services.corpus_ingest import IngestionError
from app.services.corpus_split import SplitError, prepare_split, verify_split

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "verify"])
    args = parser.parse_args()
    try:
        manifest = {"run": prepare_split, "verify": verify_split}[args.command](ROOT)
    except (SplitError, DatasetError, IngestionError) as error:
        print(f"Split preparation failed: {error}", file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError):
        print("Split preparation failed: missing_or_invalid_artifacts", file=sys.stderr)
        return 1
    print(
        f"Verified {manifest['train_records']:,} train / {manifest['test_records']:,} test; "
        f"{manifest['total_records']:,} retained records; seed {manifest['seed']}."
    )
    for subset in ("train", "test"):
        counts = manifest[f"{subset}_counts"]
        print(f"{subset.capitalize()}: {counts['ham']:,} ham / {counts['spam']:,} spam.")
    print("Manifest: data/processed/split_manifest.json; no vocabulary or model fitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
