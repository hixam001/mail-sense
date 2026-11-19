"""Run or verify bounded extraction/MIME parsing; print aggregate counts only."""

import argparse
import json
import sys
from pathlib import Path

from app.services.corpus_ingest import IngestionError, ingest_sources, verify_parsed_sources

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "verify"])
    args = parser.parse_args()
    try:
        report = {"run": ingest_sources, "verify": verify_parsed_sources}[args.command](ROOT)
    except IngestionError as error:
        print(f"Ingestion failed: {error}", file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        print("Ingestion failed: missing_or_invalid_preparation_artifacts", file=sys.stderr)
        return 1
    print(
        f"Verified {report['files_accepted']:,} accepted / {report['files_seen']:,} candidates; "
        f"{report['files_rejected']:,} rejected; "
        f"{report['metadata_files_ignored']:,} metadata files ignored."
    )
    print("Private parsed text: data/processed/messages.parsed.jsonl (ignored).")
    print("Report: data/processed/parsing_report.json; parsed stage precedes deduplication/split.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
