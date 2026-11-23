"""Check independent Agent workspace and dependency boundaries without fetching."""
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def main():
    workspace = tomllib.loads((ROOT / "Cargo.toml").read_text(encoding="utf-8"))["workspace"]
    members = {"node", "crates/common", "crates/ai-client", "crates/core", "crates/crypto"}
    assert set(workspace["members"]) == members, "Agent workspace must contain exactly five packages"
    dependencies = workspace["dependencies"]
    lock = tomllib.loads((ROOT / "Cargo.lock").read_text(encoding="utf-8"))
    for name, repo in (("social", "llm-nest-server"), ("connector", "llm-nest-connect")):
        dependency = dependencies[name]
        url = f"https://github.com/NingCold/{repo}.git"
        assert dependency["git"] == url
        revision = dependency["rev"]
        assert re.fullmatch(r"[0-9a-f]{40}", revision), f"Exact {repo} revision required"
        assert not {"path", "branch", "tag"} & dependency.keys()
        assert [p.get("source") for p in lock["package"] if p["name"] == name] == [
            f"git+{url}?rev={revision}#{revision}"
        ], f"Locked {name} source must match its declared revision"
    forbidden = {"runtime", "storage", "social-feature", "web-server", "cloud-server", "tauri-frontend", "tools"}
    for member in sorted(members):
        manifest = ROOT / member / "Cargo.toml"
        package = tomllib.loads(manifest.read_text(encoding="utf-8"))
        for section in ("dependencies", "dev-dependencies", "build-dependencies"):
            for name, dependency in package.get(section, {}).items():
                assert name not in forbidden, f"Forbidden dependency: {member} -> {name}"
                if member == "crates/core":
                    assert name not in {"connector", "rusqlite", "llmn-crypto"}
                if member == "crates/crypto":
                    assert name not in {"connector", "ai-client", "builtin-agent", "agent-node"}
                if isinstance(dependency, dict) and "path" in dependency:
                    assert (manifest.parent / dependency["path"]).resolve().is_relative_to(ROOT), "External path dependency"
        print(f"{member}: dependency boundary OK")
    for dependency in dependencies.values():
        if isinstance(dependency, dict) and "path" in dependency:
            assert (ROOT / dependency["path"]).resolve().is_relative_to(ROOT), "External workspace path"


if __name__ == "__main__":
    main()
