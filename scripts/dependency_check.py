#!/usr/bin/env python3
"""Query public advisory feeds for the exact installed/locked dependency sets."""

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime

from browser_check import ROOT


def main():
    local = ROOT / "test-results"
    local.mkdir(exist_ok=True)
    python_report = local / "python-audit.json"
    try:
        npm = subprocess.run(
            [
                sys.executable,
                "scripts/node.py",
                "npm",
                "--prefix",
                "frontend",
                "audit",
                "--json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=120,
        )
        npm_data = json.loads(npm.stdout)
        python = subprocess.run(
            [
                "uvx",
                "--from",
                "pip-audit==2.10.1",
                "pip-audit",
                "--path",
                "backend/.venv/lib/python3.12/site-packages",
                "--format",
                "json",
                "--output",
                str(python_report),
            ],
            cwd=ROOT,
            timeout=180,
        )
        data = json.loads(python_report.read_text())
        advisories = sum(len(item.get("vulns", [])) for item in data["dependencies"])
        skipped = [
            item["name"] for item in data["dependencies"] if "skip_reason" in item
        ]
        npm_count = npm_data["metadata"]["vulnerabilities"]["total"]
        passed = (
            npm.returncode == python.returncode == 0
            and npm_count == advisories == 0
            and not skipped
        )
        report = {
            "checked_at": datetime.now(UTC).isoformat(),
            "task": "MSE-602",
            "npm_audit": {
                "reported_dependencies": npm_data["metadata"]["dependencies"]["total"],
                "advisories": npm_count,
            },
            "pip_audit": {
                "version": "2.10.1",
                "packages": len(data["dependencies"]),
                "advisories": advisories,
                "skipped": skipped,
            },
            "locks": {
                name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                for name in ("frontend/package-lock.json", "backend/uv.lock")
            },
            "limitations": (
                "Advisory feeds at this timestamp; "
                "absence of known advisories is not proof of security."
            ),
            "result": "pass" if passed else "fail",
        }
        (ROOT / "artifacts/reports/dependency_audit.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        )
        print(
            f"Dependency advisories: npm={npm_count}, Python={advisories}, skipped={len(skipped)}"
        )
        return 0 if passed else 1
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"Dependency advisory check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
