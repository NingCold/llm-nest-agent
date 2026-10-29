"""Validate this Agent repository version and optional release tag."""
import os
from pathlib import Path
import re
import tomllib

root = Path(__file__).resolve().parents[1]
version = tomllib.loads((root / "Cargo.toml").read_text(encoding="utf-8"))["workspace"]["package"]["version"]
if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?", version):
    raise SystemExit("Invalid Agent version")
tag = os.environ.get("RELEASE_TAG")
if tag and tag != "v" + version:
    raise SystemExit(f"Tag {tag} does not match Agent version {version}")
print(f"Agent version {version}: OK")
