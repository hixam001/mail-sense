"""Regression checks for the runtime bootstrap's failure and extraction boundaries."""

import hashlib
import importlib.util
import io
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "node_bootstrap", Path(__file__).parents[1] / "node.py"
)
node = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(node)


class NodeBootstrapTests(unittest.TestCase):
    def test_checksum_rejects_modified_download(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "archive"
            archive.write_bytes(b"verified fixture")
            expected = hashlib.sha256(archive.read_bytes()).hexdigest()
            node.verify_archive(archive, expected)
            archive.write_bytes(b"modified download")
            with self.assertRaisesRegex(RuntimeError, "SHA-256 mismatch"):
                node.verify_archive(archive, expected)

    def test_archive_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "archive.tar"
            with tarfile.open(archive, "w") as stream:
                member = tarfile.TarInfo("release/../../escaped")
                member.size = 1
                stream.addfile(member, io.BytesIO(b"x"))
            with self.assertRaisesRegex(RuntimeError, "Unexpected path"):
                node.extract_archive(archive, root / "output", "release")
            self.assertFalse((root / "escaped").exists())

    def test_escaping_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "archive.tar"
            with tarfile.open(archive, "w") as stream:
                member = tarfile.TarInfo("release/bin/node")
                member.type = tarfile.SYMTYPE
                member.linkname = "../../../outside"
                stream.addfile(member)
            with self.assertRaises(tarfile.FilterError):
                node.extract_archive(archive, root / "output", "release")

    def test_unsupported_platform_fails_without_system_node_fallback(self):
        with patch.object(node.platform, "system", return_value="Windows"):
            with self.assertRaisesRegex(RuntimeError, "supports Linux/macOS"):
                node.release()
