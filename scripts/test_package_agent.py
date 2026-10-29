"""Verify packaged bytes, manifest metadata and version mismatch handling."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("package_agent", Path(__file__).with_name("package-agent.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PackageTests(unittest.TestCase):
    def test_manifest_binds_exact_binary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "agent.exe"
            binary.write_bytes(b"fixture Agent bytes")
            notices = root / "notices.txt"
            notices.write_text("Upstream MIT license fixture", encoding="utf-8")
            with patch.object(module.subprocess, "check_output", return_value="llmn-agent 0.1.2\n"):
                artifact = module.package(binary, root / "out", "0.1.2", "x86_64-pc-windows-msvc", notices)
            manifest = json.loads((root / "out/agent-manifest.json").read_text())
            self.assertEqual(artifact.read_bytes(), binary.read_bytes())
            self.assertEqual(manifest["agentVersion"], "0.1.2")
            self.assertEqual(manifest["artifacts"]["x86_64-pc-windows-msvc"], {
                "file": artifact.name, "sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                "notices": {"file": "THIRD_PARTY_NOTICES-0.1.2-x86_64-pc-windows-msvc.txt",
                            "sha256": hashlib.sha256(notices.read_bytes()).hexdigest()}})
            self.assertEqual((root / "out/THIRD_PARTY_NOTICES-0.1.2-x86_64-pc-windows-msvc.txt").read_bytes(), notices.read_bytes())
            self.assertTrue((root / "out/LICENSE").is_file())
            self.assertTrue((root / "out/NOTICE").is_file())

    def test_missing_or_empty_notices_do_not_package(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            notices = root / "notices.txt"
            with patch.object(module.subprocess, "check_output", return_value="llmn-agent 0.1.2"):
                with self.assertRaises(FileNotFoundError):
                    module.package(root / "agent", root / "out", "0.1.2", "x86_64-pc-windows-msvc", notices)
                notices.write_text(" ", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "nonempty"):
                    module.package(root / "agent", root / "out", "0.1.2", "x86_64-pc-windows-msvc", notices)
            self.assertFalse((root / "out").exists())

    def test_wrong_binary_version_produces_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(module.subprocess, "check_output", return_value="llmn-agent 0.1.1"):
                with self.assertRaisesRegex(ValueError, "version mismatch"):
                    module.package(root / "agent", root / "out", "0.1.2", "x86_64-unknown-linux-gnu", root / "notices.txt")
            self.assertFalse((root / "out").exists())


if __name__ == "__main__":
    unittest.main()
