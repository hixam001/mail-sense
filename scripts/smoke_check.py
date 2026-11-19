#!/usr/bin/env python3
"""Measure local HTTP performance and verify privacy under internet-denial guards."""

import argparse
import hashlib
import json
import math
import os
import platform
import signal
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from browser_check import ROOT, ensure_server

API = "http://127.0.0.1:8000"
MARKER = "dummyprivacy@example.invalid"


def request(path, body=None, headers=None):
    data = (
        body
        if isinstance(body, bytes)
        else json.dumps(body, ensure_ascii=False).encode()
        if body is not None
        else None
    )
    values = {"Origin": "http://localhost:5173", **(headers or {})}
    if data is not None:
        values["Content-Type"] = "application/json"
    try:
        response = urlopen(Request(API + path, data=data, headers=values), timeout=15)
    except HTTPError as error:
        response = error
    with response:
        return response.status, dict(response.headers), json.load(response)


def files_snapshot():
    result = {}
    for directory in ("data/raw", "data/processed", "artifacts/models"):
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file():
                with path.open("rb") as stream:
                    result[path.relative_to(ROOT).as_posix()] = hashlib.file_digest(
                        stream, "sha256"
                    ).hexdigest()
    return result


def timings(path, body=None):
    for _ in range(3):
        assert request(path, body)[0] == 200
    samples = []
    for _ in range(30):
        start = time.perf_counter()
        assert request(path, body)[0] == 200
        samples.append(time.perf_counter() - start)
    return {
        "requests": len(samples),
        "warmups": 3,
        "seconds": samples,
        "median_seconds": statistics.median(samples),
        "p95_seconds": sorted(samples)[math.ceil(0.95 * len(samples)) - 1],
        "maximum_seconds": max(samples),
        "percentile_method": "nearest_rank",
    }


def hardware():
    cpu = "unknown"
    source = Path("/proc/cpuinfo")
    if source.exists():
        cpu = next(
            (
                line.split(":", 1)[1].strip()
                for line in source.read_text().splitlines()
                if line.startswith("model name")
            ),
            "unknown",
        )
    memory_limit = Path("/sys/fs/cgroup/memory.max")
    return {
        "system": platform.system(),
        "kernel": platform.release(),
        "machine": platform.machine(),
        "cpu": cpu,
        "logical_cpus_visible": os.cpu_count(),
        "cpu_affinity_count": len(os.sched_getaffinity(0))
        if hasattr(os, "sched_getaffinity")
        else None,
        "cgroup_memory_max": memory_limit.read_text().strip()
        if memory_limit.exists()
        else "unavailable",
        "client_python": platform.python_version(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", help="Optional trusted local Chromium executable.")
    args = parser.parse_args()
    node = [sys.executable, "scripts/node.py"]
    owned = []
    local = ROOT / "test-results"
    local.mkdir(exist_ok=True)
    log_path = local / "security-server.log"
    log = None
    try:
        try:
            with urlopen(API + "/api/v1/health", timeout=2):
                raise RuntimeError(
                    "Stop the existing API before the guarded smoke check."
                )
        except OSError:
            pass
        before = files_snapshot()
        log = os.fdopen(
            os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w"
        )
        env = {**os.environ, "PYTHONPATH": str(ROOT / "backend")}
        process = subprocess.Popen(
            [str(ROOT / "backend/.venv/bin/python"), "backend/tests/offline_api.py"],
            cwd=ROOT,
            env=env,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
        owned.append(process)
        for _ in range(100):
            try:
                if request("/api/v1/health")[2]["status"] == "ready":
                    break
            except OSError:
                if process.poll() is not None:
                    raise RuntimeError("Guarded API exited before readiness.") from None
                time.sleep(0.1)
        else:
            raise RuntimeError("Guarded API failed readiness.")
        origin_checks = {}
        for label, path, body, headers, expected in (
            (
                "foreign_origin",
                "/api/v1/health",
                None,
                {"Origin": "https://foreign.invalid"},
                403,
            ),
            ("foreign_host", "/api/v1/health", None, {"Host": "foreign.invalid"}, 400),
            ("body_limit", "/api/v1/predict", b"x" * 524289, {}, 413),
            ("query_limit", "/api/v1/health?word=" + "x" * 4100, None, {}, 414),
            ("unexpected", "/test/unexpected", {"text": MARKER}, {}, 500),
            ("unknown_path", "/private/" + MARKER, None, {}, 404),
        ):
            status, response_headers, result = request(path, body, headers)
            assert status == expected and MARKER not in json.dumps(result), label
            assert response_headers.get("cache-control") == "no-store", label
            if label != "foreign_origin":
                assert (
                    response_headers.get("access-control-allow-origin")
                    == "http://localhost:5173"
                ), label
            else:
                assert "access-control-allow-origin" not in response_headers
            origin_checks[label] = status
        subprocess.run(
            [*node, "npm", "--prefix", "frontend", "run", "build"], cwd=ROOT, check=True
        )
        ensure_server(
            "http://localhost:5173/",
            [*node, "npm", "--prefix", "frontend", "run", "preview"],
            owned,
            production=True,
        )
        browser_env = dict(os.environ)
        if args.browser:
            browser_env["MAILSENSE_BROWSER"] = args.browser
        subprocess.run(
            [*node, "node", "frontend/tests/offline.mjs"],
            cwd=ROOT,
            env=browser_env,
            check=True,
            timeout=120,
        )
        browser = json.loads((ROOT / "frontend/test-results/offline.json").read_text())
        text = (
            "Subject: Synthetic timing example\n"
            "Please review the project agenda before our team meeting tomorrow."
        )
        prediction = timings("/api/v1/predict", {"text": text})
        summary = timings("/api/v1/dataset/summary")
        assert prediction["p95_seconds"] <= 3 and summary["p95_seconds"] <= 5
        assert request("/test/network-policy")[2]["runtime_denials"] == 0
        assert files_snapshot() == before
        for item in reversed(owned):
            if item.poll() is None:
                os.killpg(item.pid, signal.SIGTERM)
                item.wait(timeout=10)
        log.close()
        assert log_path.stat().st_size <= 65536
        assert MARKER not in log_path.read_text()
        evaluation = json.loads(
            (ROOT / "artifacts/reports/evaluation.json").read_text()
        )
        report = {
            "task": "MSE-602",
            "checked_at": datetime.now(UTC).isoformat(),
            "hardware": hardware(),
            "scope": (
                "Focused local runtime/privacy/offline/performance smoke; "
                "not a comprehensive penetration test."
            ),
            "offline_browser": browser,
            "http_boundaries": origin_checks,
            "input_absent_from_server_logs": True,
            "artifact_bytes_unchanged": True,
            "prediction": {
                **prediction,
                "input_characters": len(text),
                "input_kind": "synthetic",
                "target_seconds": 3,
            },
            "cached_summary": {**summary, "target_seconds": 5},
            "dataset_id": evaluation["dataset_id"],
            "split_id": evaluation["split_id"],
            "result": "pass",
            "limitations": [
                "Browser interception and Python socket guards, "
                "not OS-level internet disconnection.",
                "Measured on the recorded development hardware; "
                "other machines and browsers are unmeasured.",
            ],
        }
        (ROOT / "artifacts/reports/runtime_smoke.json").write_text(
            json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
        print(
            f"Privacy/offline smoke: PASS; prediction p95={prediction['p95_seconds']:.4f}s; "
            f"cached summary p95={summary['p95_seconds']:.4f}s"
        )
        return 0
    except (
        OSError,
        ValueError,
        AssertionError,
        RuntimeError,
        subprocess.SubprocessError,
    ) as error:
        print(f"Runtime smoke failed: {error}", file=sys.stderr)
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
        if log and not log.closed:
            log.close()


if __name__ == "__main__":
    raise SystemExit(main())
