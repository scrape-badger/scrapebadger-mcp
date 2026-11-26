from unittest.mock import AsyncMock, MagicMock

from scrapebadger_mcp import server


async def test_google_schema_and_dispatch_support_deferred_links(monkeypatch):
    assert "defer_links" in server.SearchGoogleArgs.model_json_schema()["properties"]
    client = MagicMock()
    client.google.search.search = AsyncMock(return_value={"organic_results": []})
    monkeypatch.setattr(server, "_get_client", AsyncMock(return_value=client))
    await server.call_tool("search_google", {"q": "cats", "defer_links": True})
    client.google.search.search.assert_awaited_once()
    assert client.google.search.search.await_args.kwargs["defer_links"] is True
    assert client.google.search.search.await_args.kwargs["q"] == "cats"
