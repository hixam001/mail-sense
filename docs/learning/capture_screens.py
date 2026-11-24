"""Capture guide screenshots with real production readiness and synthetic input."""

import argparse
import importlib.util
import os
import signal
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", help="Optional trusted local Chromium executable.")
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location(
        "browser_check", ROOT / "scripts/browser_check.py"
    )
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    owned = []
    try:
        helper.ensure_server(
            "http://127.0.0.1:8000/api/v1/health",
            [str(ROOT / "backend/.venv/bin/python"), "-m", "scripts.serve"],
            owned,
            cwd=ROOT / "backend",
        )
        helper.ensure_server(
            "http://localhost:5173/",
            [
                sys.executable,
                str(ROOT / "scripts/node.py"),
                "npm",
                "--prefix",
                "frontend",
                "run",
                "preview",
            ],
            owned,
            production=True,
        )
        env = dict(os.environ)
        if args.browser:
            env["MAILSENSE_BROWSER"] = args.browser
        subprocess.run(
            [
                sys.executable,
                "scripts/node.py",
                "node",
                "docs/learning/capture_screens.mjs",
            ],
            cwd=ROOT,
            env=env,
            check=True,
            timeout=180,
        )
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
    main()
