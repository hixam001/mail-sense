#!/usr/bin/env python3
"""Execute T01–T08 using known-answer tests, verified artifacts and real UI failures."""

import argparse
import json
import os
import signal
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import UTC, datetime

from browser_check import ROOT, ensure_server

SCENARIOS = {
    "T01": ["test_corpus_sources", "test_corpus_ingest", "test_mail_parser"],
    "T02": ["test_corpus_dataset", "test_corpus_split"],
    "T03": ["test_descriptive"],
    "T04": ["test_probability"],
    "T05": ["test_inference", "test_wilson", "test_numerical_verification"],
    "T06": [
        "test_model_features",
        "test_multinomial",
        "test_bernoulli",
        "test_model_store",
        "test_evaluation",
    ],
    "T07": ["test_prediction", "test_api_models"],
    "T08": ["test_api_health", "test_api_contract"],
}


def run(arguments, *, cwd=ROOT, env=None):
    subprocess.run(
        [str(value) for value in arguments], cwd=cwd, env=env, check=True, timeout=240
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", help="Optional trusted local Chromium executable.")
    args = parser.parse_args()
    python = ROOT / "backend/.venv/bin/python"
    node = [sys.executable, "scripts/node.py"]
    local = ROOT / "test-results"
    local.mkdir(exist_ok=True)
    owned = []
    try:
        run(
            [
                python,
                "-m",
                "pytest",
                "-c",
                "backend/pyproject.toml",
                "backend/tests",
                "scripts/tests",
                "-q",
                f"--junitxml={local / 'release.xml'}",
            ]
        )
        cases = ET.parse(local / "release.xml").findall(".//testcase")
        assert cases and not any(
            case.find(tag) is not None
            for case in cases
            for tag in ("failure", "error", "skipped")
        )
        modules = Counter(case.attrib["classname"].split(".")[-1] for case in cases)
        scenarios = {}
        for ticket, names in SCENARIOS.items():
            count = sum(modules[name] for name in names)
            assert count > 0 and all(modules[name] > 0 for name in names), ticket
            scenarios[ticket] = {
                "result": "pass",
                "unit_cases": count,
                "modules": names,
            }
        print(
            f"Known-answer/provenance/API regression: {len(cases)} cases passed.",
            flush=True,
        )
        for module in (
            "download_corpus",
            "ingest_corpus",
            "prepare_dataset",
            "split_dataset",
            "verify_statistics",
            "train_models",
            "evaluate_models",
        ):
            run([python, "-m", f"scripts.{module}", "verify"], cwd=ROOT / "backend")
        run([*node, "npm", "--prefix", "frontend", "test"])
        run([*node, "npm", "--prefix", "frontend", "run", "build"])
        ensure_server(
            "http://localhost:5173/",
            [*node, "npm", "--prefix", "frontend", "run", "preview"],
            owned,
            production=True,
        )
        browser_result = ROOT / "frontend/test-results/release-browser.json"
        browser_result.unlink(missing_ok=True)
        env = dict(os.environ)
        if args.browser:
            env["MAILSENSE_BROWSER"] = args.browser
        run([*node, "node", "frontend/tests/failures.mjs"], env=env)
        browser = json.loads(browser_result.read_text())
        assert browser["T07"] == browser["T08"] == "pass"
        scenarios["T07"]["browser"] = (
            "Valid/blank/overlimit/50000 input; private staging unchanged."
        )
        scenarios["T08"]["browser"] = (
            "Actual API stop/restart and missing model; analytics usable; retry recovers."
        )
        evaluation = json.loads(
            (ROOT / "artifacts/reports/evaluation.json").read_text()
        )
        report = {
            "task": "MSE-601",
            "checked_at": datetime.now(UTC).isoformat(),
            "base_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "unit_cases_passed": len(cases),
            "scenarios": scenarios,
            "browser": browser,
            "dataset_id": evaluation["dataset_id"],
            "split_id": evaluation["split_id"],
            "artifact_id": evaluation["artifact_id"],
            "actual_test_count": evaluation["test_count"],
            "offline_artifact_verifiers": 7,
            "result": "pass",
        }
        (ROOT / "artifacts/reports/acceptance.json").write_text(
            json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
        print("T01–T08 release acceptance: PASS", flush=True)
        return 0
    except (OSError, AssertionError, ValueError, subprocess.SubprocessError) as error:
        print(f"Release acceptance failed: {error}", file=sys.stderr)
        return 1
    finally:
        for process in reversed(owned):
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()


if __name__ == "__main__":
    raise SystemExit(main())
