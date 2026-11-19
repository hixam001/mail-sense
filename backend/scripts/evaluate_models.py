"""Create/verify aggregate held-out metrics for both trusted local models."""

import argparse
import sys
from pathlib import Path

from app.services.evaluation import prepare_evaluation, verify_evaluation

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "verify"])
    args = parser.parse_args()
    try:
        report = {"run": prepare_evaluation, "verify": verify_evaluation}[args.command](ROOT)
    except (OSError, ValueError, KeyError, TypeError):
        print("Evaluation failed: missing_invalid_or_incompatible_artifacts", file=sys.stderr)
        return 1
    for name, metrics in report["models"].items():
        print(
            f"{name}: {metrics['test_count']:,} held-out rows; accuracy={metrics['accuracy']:.6f}; "
            f"confusion={metrics['confusion_matrix']}"
        )
    print("Report: artifacts/reports/evaluation.json; historical fixed-split results, no tuning.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
