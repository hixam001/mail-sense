#!/usr/bin/env python3
"""Install/run the pinned local Node/npm without using the system Node."""

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
# Official https://nodejs.org/dist/v22.23.5/SHASUMS256.txt, checked 2026-11-19.
CHECKSUMS = {
    "node-v22.23.5-linux-x64.tar.xz":
        "cdeb8670a0c81f51b4dc4ac61919f9b1ad917b304bf8221eb939570663d240f8",
    "node-v22.23.5-linux-arm64.tar.xz":
        "2babb9eb5264860d540849f4b064a6fbdebcdc323657d9d382ce23d313fd5e09",
    "node-v22.23.5-darwin-x64.tar.gz":
        "c53383238206b9ae4db23c5d8a63645e2e753bec8ab51a49cc81939aa64e9422",
    "node-v22.23.5-darwin-arm64.tar.gz":
        "e7131995759b61a0170b646010d2ad35a5d37b4cb0d471f3e8317eac6f742f3d",
}


def release():
    system = {"Linux": "linux", "Darwin": "darwin"}.get(platform.system())
    arch = {"x86_64": "x64", "AMD64": "x64", "aarch64": "arm64", "arm64": "arm64"}.get(
        platform.machine()
    )
    if not system or not arch:
        raise RuntimeError("Local Node setup supports Linux/macOS x64/arm64; see docs/SETUP.md.")
    version = (ROOT / ".node-version").read_text().strip()
    directory = f"node-v{version}-{system}-{arch}"
    filename = directory + (".tar.xz" if system == "linux" else ".tar.gz")
    if filename not in CHECKSUMS:
        raise RuntimeError("Node version has no pinned archive checksum; update pins together.")
    return version, directory, filename


def verify_archive(path, expected):
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != expected:
        raise RuntimeError("Node archive SHA-256 mismatch; nothing was extracted.")


def extract_archive(path, destination, directory):
    with tarfile.open(path) as archive:
        for member in archive.getmembers():
            parts = PurePosixPath(member.name).parts
            if not parts or parts[0] != directory or ".." in parts:
                raise RuntimeError("Unexpected path in Node archive.")
        archive.extractall(destination, filter="data")


def verify_runtime(directory, version):
    node = directory / "bin/node"
    npm = directory / "lib/node_modules/npm/bin/npm-cli.js"
    expected_npm = json.loads((ROOT / "frontend/package.json").read_text())["packageManager"]
    if subprocess.check_output([node, "--version"], text=True).strip() != f"v{version}":
        raise RuntimeError("Local Node version differs from .node-version.")
    if subprocess.check_output([node, npm, "--version"], text=True).strip() != expected_npm[4:]:
        raise RuntimeError("Local npm version differs from frontend/package.json.")
    return node, npm


def install(version, directory, filename):
    tools = ROOT / ".tools"
    target = tools / directory
    if target.exists():
        verify_runtime(target, version)
        print(f"Pinned Node/npm already installed: {target}")
        return
    tools.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".node-download-", dir=tools) as temporary:
        staging = Path(temporary)
        archive = staging / filename
        url = f"https://nodejs.org/dist/v{version}/{filename}"
        with urllib.request.urlopen(url, timeout=60) as response, archive.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        verify_archive(archive, CHECKSUMS[filename])
        extract_archive(archive, staging, directory)
        verify_runtime(staging / directory, version)
        (staging / directory).rename(target)
    print(f"Installed checksum-verified Node/npm: {target}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["install", "node", "npm"])
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        version, directory, filename = release()
        if args.command == "install":
            if args.arguments:
                parser.error("install accepts no additional arguments")
            install(version, directory, filename)
            return 0
        target = ROOT / ".tools" / directory
        if not target.exists():
            raise RuntimeError("Run python3 scripts/node.py install before using local Node/npm.")
        node, npm = verify_runtime(target, version)
        argv = [str(node), *([str(npm)] if args.command == "npm" else []), *args.arguments]
        env = {**os.environ, "PATH": str(target / "bin") + os.pathsep + os.environ.get("PATH", "")}
        os.execvpe(str(node), argv, env)
    except (OSError, RuntimeError, tarfile.TarError, subprocess.CalledProcessError) as error:
        print(f"Node setup failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
