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
            with patch.object(module.subprocess, "check_output", return_value="llmn-agent 0.1.2\n"):
                artifact = module.package(binary, root / "out", "0.1.2", "x86_64-pc-windows-msvc")
            manifest = json.loads((root / "out/agent-manifest.json").read_text())
            self.assertEqual(artifact.read_bytes(), binary.read_bytes())
            self.assertEqual(manifest["agentVersion"], "0.1.2")
            self.assertEqual(manifest["artifacts"]["x86_64-pc-windows-msvc"], {
                "file": artifact.name, "sha256": hashlib.sha256(binary.read_bytes()).hexdigest()})

    def test_wrong_binary_version_produces_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(module.subprocess, "check_output", return_value="llmn-agent 0.1.1"):
                with self.assertRaisesRegex(ValueError, "version mismatch"):
                    module.package(root / "agent", root / "out", "0.1.2", "x86_64-unknown-linux-gnu")
            self.assertFalse((root / "out").exists())


if __name__ == "__main__":
    unittest.main()
