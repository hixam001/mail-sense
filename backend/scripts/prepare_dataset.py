"""Prepare or verify retained corpus records; report aggregate counts only."""

import argparse
import sys
from pathlib import Path

from app.services.corpus_dataset import DatasetError, prepare_dataset, verify_dataset
from app.services.corpus_ingest import IngestionError

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "verify"])
    args = parser.parse_args()
    try:
        report = {"run": prepare_dataset, "verify": verify_dataset}[args.command](ROOT)
    except (DatasetError, IngestionError) as error:
        print(f"Dataset preparation failed: {error}", file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError):
        print("Dataset preparation failed: missing_or_invalid_artifacts", file=sys.stderr)
        return 1
    print(
        f"Verified {report['retained_records']:,} retained / {report['input_records']:,} parsed; "
        f"{report['duplicate_records_excluded']:,} duplicates and "
        f"{report['conflicting_records_excluded']:,} label-conflict rows excluded."
    )
    print(
        f"Retained classes: {report['class_counts']['ham']:,} ham / "
        f"{report['class_counts']['spam']:,} spam. Split assignment remains pending."
    )
    print("Private records: data/processed/messages.csv (ignored).")
    print("Report: data/processed/deduplication_report.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
