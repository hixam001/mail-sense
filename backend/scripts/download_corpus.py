"""Download or verify canonical corpus archives; never extract or display mail."""

import argparse
import urllib.error
from http.client import HTTPException
from pathlib import Path

from app.services.corpus_sources import download_sources, verify_sources

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["download", "verify"])
    args = parser.parse_args()
    try:
        manifest = {"download": download_sources, "verify": verify_sources}[args.command](ROOT)
    except (OSError, ValueError, HTTPException, urllib.error.URLError) as error:
        print(f"Corpus acquisition failed: {error}")
        return 1
    total = sum(record.size_bytes for record in manifest.archives)
    print(f"Verified {len(manifest.archives)} canonical archives ({total:,} bytes).")
    print("Manifest: data/processed/source_manifest.json; raw archives stay local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
