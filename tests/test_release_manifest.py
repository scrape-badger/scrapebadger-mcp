"""Release metadata agrees across pyproject, the package and the MCP registry manifest."""

from __future__ import annotations

import json
import re
from pathlib import Path

import scrapebadger_mcp

ROOT = Path(__file__).resolve().parents[1]


def test_versions_and_registry_manifest_agree() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text()
    match = re.search(r'^version = "([^"]+)"', pyproject, re.M)
    assert match
    version = match.group(1)
    manifest = json.loads((ROOT / "server.json").read_text())
    assert version == scrapebadger_mcp.__version__ == manifest["version"]
    assert [(p["identifier"], p["version"]) for p in manifest["packages"]] == [
        ("scrapebadger-mcp", version)
    ]
    assert len(manifest["description"]) <= 100  # the registry's limit
    readme = (ROOT / "README.md").read_text()
    assert f"<!-- mcp-name: {manifest['name']} -->" in readme
