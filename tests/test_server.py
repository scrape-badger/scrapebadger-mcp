"""Tests for the MCP server."""

from __future__ import annotations

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from scrapebadger_mcp.server import (
    GetUserProfileArgs,
    SearchGoogleArgs,
    SearchTweetsArgs,
    _get_api_key,
    call_tool,
    list_tools,
)


class TestApiKey:
    """Tests for API key handling."""

    def test_get_api_key_from_env(self) -> None:
        """Test getting API key from environment."""
        with patch.dict(os.environ, {"SCRAPEBADGER_API_KEY": "test_key"}):
            assert _get_api_key() == "test_key"

    def test_get_api_key_missing(self) -> None:
        """Test error when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove the key if it exists
            os.environ.pop("SCRAPEBADGER_API_KEY", None)
            with pytest.raises(ValueError, match="SCRAPEBADGER_API_KEY"):
                _get_api_key()


class TestToolArgs:
    """Tests for tool argument models."""

    def test_get_user_profile_args(self) -> None:
        """Test GetUserProfileArgs validation."""
        args = GetUserProfileArgs(username="elonmusk")
        assert args.username == "elonmusk"

    def test_search_tweets_args_defaults(self) -> None:
        """Test SearchTweetsArgs with defaults."""
        args = SearchTweetsArgs(query="python")
        assert args.query == "python"
        assert args.max_results == 20

    def test_search_tweets_args_custom(self) -> None:
        """Test SearchTweetsArgs with custom values."""
        args = SearchTweetsArgs(query="python", max_results=50)
        assert args.max_results == 50

    def test_search_google_args_defaults(self) -> None:
        args = SearchGoogleArgs(q="python")
        assert (args.gl, args.hl, args.start) == ("us", "en", 0)
        assert args.ai_overview is False
        assert args.expand_related_questions is None

    @pytest.mark.parametrize("value", [True, False, 0, 2, 99])
    def test_search_google_expand_related_questions_accepts(self, value: bool | int) -> None:
        args = SearchGoogleArgs(q="python", expand_related_questions=value)
        assert args.expand_related_questions == value
        assert type(args.expand_related_questions) is type(value)

    @pytest.mark.parametrize("value", [-1, 100])
    def test_search_google_expand_related_questions_range(self, value: int) -> None:
        with pytest.raises(ValidationError):
            SearchGoogleArgs(q="python", expand_related_questions=value)


class TestListTools:
    """Tests for tool listing."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_tools(self) -> None:
        """Test that list_tools returns expected tools."""
        tools = await list_tools()

        # Check we have the expected number of tools
        assert len(tools) == 26

        # Check specific tools exist
        tool_names = [t.name for t in tools]
        assert "get_twitter_user_profile" in tool_names
        assert "search_twitter_tweets" in tool_names
        assert "get_twitter_trends" in tool_names
        assert "get_twitter_followers" in tool_names
        assert "search_google" in tool_names

    @pytest.mark.asyncio
    async def test_search_google_schema_has_expand_related_questions(self) -> None:
        tools = {t.name: t for t in await list_tools()}
        props = tools["search_google"].inputSchema["properties"]
        assert "expand_related_questions" in props
        assert tools["search_google"].inputSchema["required"] == ["q"]

    @pytest.mark.asyncio
    async def test_list_tools_have_descriptions(self) -> None:
        """Test that all tools have descriptions."""
        tools = await list_tools()

        for tool in tools:
            assert tool.description
            assert len(tool.description) > 10

    @pytest.mark.asyncio
    async def test_list_tools_have_schemas(self) -> None:
        """Test that all tools have input schemas."""
        tools = await list_tools()

        for tool in tools:
            assert tool.inputSchema
            assert "properties" in tool.inputSchema or "type" in tool.inputSchema


class TestCallTool:
    """Tests for tool dispatch."""

    @pytest.mark.asyncio
    async def test_search_google_forwards_expand_related_questions(self) -> None:
        client = MagicMock()
        client.google.search.search = AsyncMock(
            return_value={"related_questions": [{"question": "q?", "text_blocks": []}]}
        )
        with patch("scrapebadger_mcp.server._get_client", AsyncMock(return_value=client)):
            out = await call_tool(
                "search_google",
                {"q": "noise cancelling headphones", "expand_related_questions": 2},
            )
        client.google.search.search.assert_awaited_once_with(
            q="noise cancelling headphones",
            gl="us",
            hl="en",
            start=0,
            ai_overview=False,
            expand_related_questions=2,
            no_cache=False,
        )
        assert json.loads(out[0].text)["related_questions"][0]["question"] == "q?"

    @pytest.mark.asyncio
    async def test_search_google_forwards_targeting_and_returns_html(self) -> None:
        client = MagicMock()
        client.google.search.search = AsyncMock(return_value="<html>kavinė</html>")
        params = {
            "oq": "vinted café + api&gl=fr",
            "sourceid": "",
            "ie": "UTF-8",
            "q": "vinted api",
            "location": "New York, USA",
            "no_cache": True,
            "as_epq": "vinted api",
            "color_scheme": "dark",
            "output": "html",
        }
        with patch("scrapebadger_mcp.server._get_client", AsyncMock(return_value=client)):
            out = await call_tool("search_google", params)
        sent = client.google.search.search.await_args.kwargs
        assert {key: sent[key] for key in params} == params
        assert json.loads(out[0].text) == {"data": "<html>kavinė</html>"}


@pytest.mark.asyncio
async def test_lifecycle_hides_and_marks_tools(monkeypatch):
    from unittest.mock import AsyncMock

    from scrapebadger import ScrapeBadger

    monkeypatch.setattr(
        ScrapeBadger,
        "endpoints",
        AsyncMock(
            return_value=[
                {
                    "method": "GET",
                    "path": "/v1/google/search",
                    "api": "google",
                    "status": "deprecated",
                }
            ]
        ),
    )
    tools = await list_tools()
    assert [tool.name for tool in tools] == ["search_google"]
    assert tools[0].description.startswith("Deprecated.")
    monkeypatch.setattr(ScrapeBadger, "endpoints", AsyncMock(return_value=[]))
    assert await list_tools() == []


@pytest.mark.asyncio
async def test_linkedin_full_profile_tool_dispatch() -> None:
    client = MagicMock()
    client.linkedin.get_full_profile = AsyncMock(
        return_value={"public_id": "williamhgates", "access_scope": "authenticated"}
    )
    with patch("scrapebadger_mcp.server._get_client", AsyncMock(return_value=client)):
        out = await call_tool("linkedin_get_full_profile", {"public_id": "williamhgates"})

    client.linkedin.get_full_profile.assert_awaited_once_with("williamhgates", country="us")
    assert json.loads(out[0].text)["access_scope"] == "authenticated"
