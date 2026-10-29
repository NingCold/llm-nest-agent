"""Merge both platform artifacts after verifying their versions and bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

TARGETS = {"x86_64-pc-windows-msvc", "x86_64-unknown-linux-gnu"}


def merge(inputs, output, tag=None, repository="NingCold/llm-nest-agent"):
    manifests = sorted(inputs.glob("*/agent-manifest.json"))
    if len(manifests) != 2:
        raise ValueError("Exactly two platform manifests are required")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Invalid GitHub repository")
    version = None
    artifacts = {}
    sources = {}
    own_licenses = {}
    for manifest_path in manifests:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        current = manifest["agentVersion"]
        if manifest["schemaVersion"] != 1 or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?", current):
            raise ValueError("Invalid platform manifest")
        if version is not None and current != version:
            raise ValueError("Platform versions differ")
        version = current
        if len(manifest["artifacts"]) != 1:
            raise ValueError("One target required per platform manifest")
        for target, entry in manifest["artifacts"].items():
            if target not in TARGETS or target in artifacts:
                raise ValueError("Unexpected or duplicate target")
            name = f"llmn-agent-{version}-{target}" + (".exe" if "windows" in target else "")
            if entry["file"] != name:
                raise ValueError("Unexpected artifact filename")
            source = manifest_path.parent / name
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if digest != entry["sha256"]:
                raise ValueError("Artifact checksum mismatch")
            notice_name = f"THIRD_PARTY_NOTICES-{version}-{target}.txt"
            notice = entry["notices"]
            if notice["file"] != notice_name:
                raise ValueError("Unexpected notices filename")
            notice_source = manifest_path.parent / notice_name
            notice_digest = hashlib.sha256(notice_source.read_bytes()).hexdigest()
            if notice_digest != notice["sha256"]:
                raise ValueError("Notices checksum mismatch")
            artifacts[target] = {"file": name, "sha256": digest,
                                 "notices": {"file": notice_name, "sha256": notice_digest}}
            sources[name] = source
            sources[notice_name] = notice_source
            for license_name in ("LICENSE", "NOTICE"):
                license_source = manifest_path.parent / license_name
                data = license_source.read_bytes()
                if license_name in own_licenses and own_licenses[license_name] != data:
                    raise ValueError("Platform product license materials differ")
                own_licenses[license_name] = data
                sources[license_name] = license_source
    if set(artifacts) != TARGETS:
        raise ValueError("Both supported targets are required")
    if tag:
        if tag != "v" + version:
            raise ValueError("Release tag does not match Agent version")
        for entry in artifacts.values():
            entry["url"] = f"https://github.com/{repository}/releases/download/{tag}/{entry['file']}"
            entry["notices"]["url"] = f"https://github.com/{repository}/releases/download/{tag}/{entry['notices']['file']}"
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output directory must be empty")
    output.mkdir(parents=True, exist_ok=True)
    for name, source in sources.items():
        shutil.copy2(source, output / name)
    combined = {"schemaVersion": 1, "agentVersion": version, "artifacts": artifacts}
    manifest_path = output / "agent-manifest.json"
    manifest_path.write_text(json.dumps(combined, indent=2) + "\n", encoding="utf-8")
    checksums = {name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in sources}
    checksums[manifest_path.name] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    (output / "SHA256SUMS.txt").write_text("".join(f"{digest}  {name}\n" for name, digest in sorted(checksums.items())), encoding="utf-8")
    return combined


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--release-tag")
    parser.add_argument("--repository", default="NingCold/llm-nest-agent")
    args = parser.parse_args()
    merge(args.inputs, args.output, args.release_tag, args.repository)
