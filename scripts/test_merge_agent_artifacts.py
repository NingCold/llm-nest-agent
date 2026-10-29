"""Verify combined release manifests bind both platform binaries."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("merge_agent", Path(__file__).with_name("merge-agent-artifacts.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MergeTests(unittest.TestCase):
    def fixture(self, root):
        for target in module.TARGETS:
            directory = root / "inputs" / target
            directory.mkdir(parents=True)
            name = f"llmn-agent-0.1.2-{target}" + (".exe" if "windows" in target else "")
            data = target.encode()
            (directory / name).write_bytes(data)
            notice_name = f"THIRD_PARTY_NOTICES-0.1.2-{target}.txt"
            notice_data = b"fixture third-party license"
            (directory / notice_name).write_bytes(notice_data)
            (directory / "LICENSE").write_text("fixture product license")
            (directory / "NOTICE").write_text("fixture product notice")
            (directory / "agent-manifest.json").write_text(json.dumps({
                "schemaVersion": 1, "agentVersion": "0.1.2", "artifacts": {
                    target: {"file": name, "sha256": hashlib.sha256(data).hexdigest(),
                             "notices": {"file": notice_name, "sha256": hashlib.sha256(notice_data).hexdigest()}}}}))

    def test_release_contains_both_fixed_urls_and_checksums(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            combined = module.merge(root / "inputs", root / "out", "v0.1.2")
            self.assertEqual(set(combined["artifacts"]), module.TARGETS)
            for entry in combined["artifacts"].values():
                self.assertEqual(entry["url"], "https://github.com/NingCold/llm-nest-agent/releases/download/v0.1.2/" + entry["file"])
                self.assertEqual(entry["notices"]["url"], "https://github.com/NingCold/llm-nest-agent/releases/download/v0.1.2/" + entry["notices"]["file"])
            lines = (root / "out/SHA256SUMS.txt").read_text().splitlines()
            self.assertEqual(len(lines), 7)
            for line in lines:
                digest, name = line.split("  ")
                self.assertEqual(digest, hashlib.sha256((root / "out" / name).read_bytes()).hexdigest())

    def test_untagged_manifest_has_no_published_urls(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            combined = module.merge(root / "inputs", root / "out")
            self.assertTrue(all("url" not in entry for entry in combined["artifacts"].values()))

    def test_changed_binary_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            binary = next((root / "inputs").glob("*/llmn-agent-*"))
            binary.write_bytes(b"modified")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                module.merge(root / "inputs", root / "out", "v0.1.2")
            self.assertFalse((root / "out").exists())

    def test_changed_notices_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            notice = next((root / "inputs").glob("*/THIRD_PARTY_NOTICES-*.txt"))
            notice.write_bytes(b"altered license text")
            with self.assertRaisesRegex(ValueError, "Notices checksum mismatch"):
                module.merge(root / "inputs", root / "out", "v0.1.2")
            self.assertFalse((root / "out").exists())

    def test_mismatched_version_or_tag_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            with self.assertRaisesRegex(ValueError, "tag"):
                module.merge(root / "inputs", root / "out", "v0.1.3")
            manifest = next((root / "inputs").glob("*/agent-manifest.json"))
            data = json.loads(manifest.read_text())
            data["agentVersion"] = "0.1.3"
            manifest.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                module.merge(root / "inputs", root / "out", "v0.1.2")
            self.assertFalse((root / "out").exists())


if __name__ == "__main__":
    unittest.main()
