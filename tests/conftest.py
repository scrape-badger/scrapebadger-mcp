from unittest.mock import AsyncMock

import pytest


@pytest.fixture(autouse=True)
def live_catalog(monkeypatch):
    from scrapebadger import ScrapeBadger

    from scrapebadger_mcp.server import TOOL_METHODS, TOOL_PATHS

    # One active row per tool, under the tool's own HTTP method (GET unless named).
    rows = [
        {
            "method": TOOL_METHODS.get(name, "GET"),
            "path": path,
            "api": path.split("/")[2],
            "status": "active",
        }
        for name, path in TOOL_PATHS.items()
    ]
    monkeypatch.setattr(ScrapeBadger, "endpoints", AsyncMock(return_value=rows))
    monkeypatch.setenv("SCRAPEBADGER_API_KEY", "test")
