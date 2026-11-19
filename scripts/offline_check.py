#!/usr/bin/env python3
"""Run the local smoke suite in an isolated Linux child network namespace."""

import argparse
import errno
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from browser_check import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", help="Optional trusted local Chromium executable.")
    parser.add_argument("--inside", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if platform.system() != "Linux":
            raise RuntimeError("OS-level offline verification requires Linux namespaces.")
        current = os.readlink("/proc/self/ns/net")
        if args.inside is None:
            unshare = shutil.which("unshare")
            if not unshare:
                raise RuntimeError("Install unshare (util-linux) for this optional release check.")
            command = [
                unshare,
                "--user",
                "--map-root-user",
                "--net",
                sys.executable,
                str(Path(__file__).resolve()),
                "--inside",
                current,
            ]
            if args.browser:
                command.extend(["--browser", args.browser])
            subprocess.run(command, cwd=ROOT, check=True, timeout=240)
            if os.readlink("/proc/self/ns/net") != current:
                raise RuntimeError("Parent network namespace changed unexpectedly.")
            print("OS-level offline acceptance; parent network unchanged: PASS", flush=True)
            return 0

        if current == args.inside:
            raise RuntimeError("Refusing to alter the parent network namespace.")
        ip = shutil.which("ip")
        if not ip:
            raise RuntimeError("Install ip (iproute2) to enable isolated loopback.")
        interfaces = sorted(name for _, name in socket.if_nameindex())
        routes = subprocess.check_output([ip, "route", "show"], text=True).strip()
        if interfaces != ["lo"] or routes:
            raise RuntimeError("Expected only loopback with no IPv4 routes.")
        subprocess.run([ip, "link", "set", "lo", "up"], check=True)
        try:
            with socket.create_connection(("192.0.2.1", 443), timeout=1):
                raise RuntimeError("External probe unexpectedly connected.")
        except OSError as error:
            if error.errno != errno.ENETUNREACH:
                raise RuntimeError("External probe did not confirm no network route.") from error

        command = [sys.executable, "scripts/smoke_check.py"]
        if args.browser:
            command.extend(["--browser", args.browser])
        subprocess.run(command, cwd=ROOT, check=True, timeout=180)
        runtime = ROOT / "artifacts/reports/runtime_smoke.json"
        evidence = json.loads(runtime.read_text())
        if evidence["result"] != "pass":
            raise RuntimeError("Runtime smoke report did not pass.")
        report = {
            "task": "MSE-606",
            "checked_at": datetime.now(UTC).isoformat(),
            "system": platform.system(),
            "machine": platform.machine(),
            "kernel": platform.release(),
            "separate_child_network_namespace": True,
            "interfaces": interfaces,
            "ipv4_routes": [],
            "external_probe": "192.0.2.1:443 blocked by kernel ENETUNREACH",
            "runtime_smoke_sha256": hashlib.sha256(runtime.read_bytes()).hexdigest(),
            "dataset_id": evidence["dataset_id"],
            "split_id": evidence["split_id"],
            "core_routes": evidence["offline_browser"]["core_routes"],
            "browser": evidence["offline_browser"]["browser"],
            "artifact_bytes_unchanged": evidence["artifact_bytes_unchanged"],
            "result": "pass",
            "limitations": (
                "Linux only; requires unprivileged user/network namespaces and iproute2."
            ),
        }
        (ROOT / "artifacts/reports/offline_namespace.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        )
        print("Six core routes and both models without OS internet routes: PASS", flush=True)
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"OS-level offline verification failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
