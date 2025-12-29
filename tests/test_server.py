"""Tests for the MCP server."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest

from scrapebadger_mcp.server import (
    GetUserProfileArgs,
    SearchTweetsArgs,
    _get_api_key,
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


class TestListTools:
    """Tests for tool listing."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_tools(self) -> None:
        """Test that list_tools returns expected tools."""
        tools = await list_tools()

        # Check we have the expected number of tools
        assert len(tools) == 17

        # Check specific tools exist
        tool_names = [t.name for t in tools]
        assert "get_twitter_user_profile" in tool_names
        assert "search_twitter_tweets" in tool_names
        assert "get_twitter_trends" in tool_names
        assert "get_twitter_followers" in tool_names

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
