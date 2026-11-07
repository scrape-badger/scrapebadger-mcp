from unittest.mock import AsyncMock

import pytest


@pytest.fixture(autouse=True)
def live_catalog(monkeypatch):
    from scrapebadger import ScrapeBadger

    from scrapebadger_mcp.server import TOOL_PATHS

    rows = [
        {"method": "GET", "path": path, "api": path.split("/")[2], "status": "active"}
        for path in TOOL_PATHS.values()
    ]
    monkeypatch.setattr(ScrapeBadger, "endpoints", AsyncMock(return_value=rows))
    monkeypatch.setenv("SCRAPEBADGER_API_KEY", "test")
