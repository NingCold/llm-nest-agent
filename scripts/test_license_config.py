"""Check reviewed cargo-about native clarification inputs and release entry point."""
from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LicenseConfigTests(unittest.TestCase):
    def test_missing_archive_licenses_use_reviewed_git_content(self):
        config = tomllib.loads((ROOT / "scripts/licenses/about.toml").read_text(encoding="utf-8"))
        ruma = "89807acf2309bd285f033404ee78581602f3cd9b819a16ac2f0e5f60ff4a473e"
        expected = dict.fromkeys(["ruma", "ruma-client-api", "ruma-common", "ruma-events", "ruma-identifiers-validation", "ruma-macros"], ruma)
        expected["decancer"] = "bbbb3f5f5cb288d63dad6e80ab04eab6c07f28643b79b9c447f629a6f8b37fe7"
        for name, checksum in expected.items():
            clarification = config[name]["clarify"]
            self.assertEqual(clarification, {"license": "MIT", "git": [{"path": "LICENSE", "checksum": checksum}]})
        # No revision overrides: cargo-about must use the published crate's VCS identity.
        self.assertNotIn("override-git-commit", (ROOT / "scripts/licenses/about.toml").read_text())

    def test_supplemental_copyright_covers_locked_component_versions(self):
        import re
        template = (ROOT / "scripts/licenses/third-party-notices.hbs").read_text(encoding="utf-8")
        lock = tomllib.loads((ROOT / "Cargo.lock").read_text(encoding="utf-8"))
        names = {"linux-raw-sys", "rustix", "rand", "rand_core", "rand_chacha", "rand_xoshiro", "unicode-normalization", "utf8_iter"}
        expected = {(p["name"], p["version"]) for p in lock["package"] if p["name"] in names}
        included = set()
        for line in re.findall(r"^Supplemental upstream COPYRIGHT: (.+)$", template, re.M):
            included.update(tuple(value.split()) for value in line.split(", "))
        self.assertEqual(included, expected)
        self.assertEqual(len(re.findall(r"^Supplemental upstream COPYRIGHT:", template, re.M)), 6)

    def test_release_uses_native_config_before_packaging(self):
        workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        self.assertIn("--config scripts/licenses/about.toml", workflow)
        self.assertLess(workflow.index("cargo-about generate"), workflow.index("python scripts/package-agent.py --binary"))


if __name__ == "__main__":
    unittest.main()
