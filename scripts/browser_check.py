#!/usr/bin/env python3
"""Run reproducible local browser checks, owning only servers started here."""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def ensure_server(url, command, owned, *, production=False, cwd=ROOT):
    try:
        with urlopen(url, timeout=3) as response:
            page = response.read(4096)
        if production and b"/@vite/client" in page:
            raise RuntimeError(
                "Stop the development UI before checking the production preview."
            )
        return
    except OSError:
        pass
    process = subprocess.Popen(command, cwd=cwd, start_new_session=True)
    owned.append(process)
    for _ in range(100):
        try:
            with urlopen(url, timeout=3):
                return
        except OSError:
            if process.poll() is not None:
                raise RuntimeError("Local server exited before readiness.") from None
            time.sleep(0.1)
    raise RuntimeError("Local server did not become ready.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--production", action="store_true")
    parser.add_argument("--browser", help="Optional trusted local Chromium executable.")
    args = parser.parse_args()
    node = [sys.executable, "scripts/node.py", "npm", "--prefix", "frontend"]
    owned = []
    try:
        if args.production:
            subprocess.run([*node, "run", "build"], cwd=ROOT, check=True)
        ensure_server(
            "http://127.0.0.1:8000/api/v1/health",
            [str(ROOT / "backend/.venv/bin/python"), "-m", "scripts.serve"],
            owned,
            cwd=ROOT / "backend",
        )
        ensure_server(
            "http://localhost:5173/",
            [*node, "run", "preview" if args.production else "dev"],
            owned,
            production=args.production,
        )
        env = dict(os.environ)
        if args.browser:
            env["MAILSENSE_BROWSER"] = args.browser
        subprocess.run(
            [*node, "run", "test:e2e"], cwd=ROOT, env=env, check=True, timeout=180
        )
        print("Local browser acceptance: PASS", flush=True)
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Browser checks failed: {error}", file=sys.stderr)
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
