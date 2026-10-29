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
    social, connector = (dependencies[name] for name in ("social", "connector"))
    for dependency in (social, connector):
        assert dependency["git"] == "https://github.com/NingCold/llm-nest-server.git"
        assert re.fullmatch(r"[0-9a-f]{40}", dependency["rev"]), "Exact server revision required"
        assert not {"path", "branch", "tag"} & dependency.keys()
    assert social["rev"] == connector["rev"], "Protocol packages must share a revision"
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
