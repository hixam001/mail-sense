"""Run/verify numerical examples and measured aggregates, without models or UI."""

import argparse
import json
import sys
import tempfile
from pathlib import Path

from app.services.corpus_sources import corpus_lock
from app.services.numerical_verification import build_verification

ROOT = Path(__file__).resolve().parents[2]
REPORT = "artifacts/reports/statistics_verification.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "verify"])
    args = parser.parse_args()
    try:
        root = ROOT.resolve()
        target = root / REPORT
        if target.is_symlink() or not target.resolve().is_relative_to(root):
            raise ValueError("invalid_report_path")
        with corpus_lock(root / "data/raw"):
            report = build_verification(root)
            if not report["passed"]:
                raise ValueError("numerical_verification_failed")
            data = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
            if args.command == "run":
                target.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryDirectory(
                    prefix=".statistics-", dir=target.parent
                ) as folder:
                    output = Path(folder) / "report.json"
                    output.write_bytes(data)
                    output.replace(target)
            elif target.read_bytes() != data:
                raise ValueError("statistics_report_mismatch")
    except (OSError, ValueError, KeyError, TypeError):
        print("Numerical verification failed: missing_invalid_or_stale_artifacts", file=sys.stderr)
        return 1
    print(
        f"Verified {len(report['checks'])} independent numerical checks; synthetic examples "
        "and measured corpus aggregates are labeled separately."
    )
    print(f"Report: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
