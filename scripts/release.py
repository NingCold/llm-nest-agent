"""Validate this Agent repository version and optional release tag."""
import os
from pathlib import Path
import re
import subprocess
import tomllib

root = Path(__file__).resolve().parents[1]
version = tomllib.loads((root / "Cargo.toml").read_text(encoding="utf-8"))["workspace"]["package"]["version"]
if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?", version):
    raise SystemExit("Invalid Agent version")
tag = os.environ.get("RELEASE_TAG")
if tag and tag != "v" + version:
    raise SystemExit(f"Tag {tag} does not match Agent version {version}")
if tag:
    tagged = subprocess.check_output(["git", "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"], cwd=root, text=True).strip()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if tagged != head:
        raise SystemExit("Checkout does not match the requested release tag")
print(f"Agent version {version}: OK")
