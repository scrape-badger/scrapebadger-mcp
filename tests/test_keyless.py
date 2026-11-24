"""The server starts and lists its tools without an API key (SCR-653).

MCP directories build the image, start the server and list its tools before anyone sets a
key. Without SCRAPEBADGER_API_KEY every tool is listed, the live catalog is not read, and a
tool call returns an MCP error that says how to set the key.
"""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import CallToolResult
from scrapebadger import ScrapeBadger

from scrapebadger_mcp import server as server_module
from scrapebadger_mcp.server import TOOL_PATHS, call_tool, list_tools, main, server

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SCRAPEBADGER_API_KEY", raising=False)
    monkeypatch.setattr(server_module, "_client", None)


def missing_key_error(result: Any) -> dict[str, Any]:
    assert isinstance(result, CallToolResult)
    assert result.isError
    error: dict[str, Any] = json.loads(result.content[0].text)
    assert error["error_type"] == "MissingApiKeyError"
    return error


@pytest.mark.parametrize("value", [None, "", "   "])
async def test_lists_every_tool_without_reading_the_catalog(
    monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    if value is None:
        monkeypatch.delenv("SCRAPEBADGER_API_KEY", raising=False)
    else:
        monkeypatch.setenv("SCRAPEBADGER_API_KEY", value)
    monkeypatch.setattr(server_module, "_client", None)
    names = [tool.name for tool in await list_tools()]
    assert sorted(names) == sorted(TOOL_PATHS)
    ScrapeBadger.endpoints.assert_not_awaited()  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("name", "arguments"),
    [
        ("grok_list_models", {}),
        ("get_twitter_user_profile", {"username": "x"}),
        ("search_google", {}),  # the key error comes before argument validation
    ],
)
async def test_tool_call_without_a_key_says_how_to_set_it(
    no_key: None, name: str, arguments: dict[str, Any]
) -> None:
    with patch("scrapebadger_mcp.server._get_client", AsyncMock()) as get_client:
        error = missing_key_error(await call_tool(name, arguments))
    get_client.assert_not_awaited()
    assert "SCRAPEBADGER_API_KEY is not set" in error["error"]
    assert "https://scrapebadger.com/dashboard/api-keys" in error["error"]
    assert '"env": {"SCRAPEBADGER_API_KEY": "<your key>"}' in error["error"]
    assert "docker run -i --rm -e SCRAPEBADGER_API_KEY=<your key>" in error["error"]


async def test_unknown_tool_without_a_key_is_still_unknown(no_key: None) -> None:
    out = await call_tool("no_such_tool", {})
    assert not isinstance(out, CallToolResult)
    assert json.loads(out[0].text) == {"error": "Unknown tool: no_such_tool"}


async def test_mcp_session_without_a_key(no_key: None) -> None:
    async with create_connected_server_and_client_session(server) as session:
        tools = (await session.list_tools()).tools
        result = await session.call_tool("grok_ask", {"prompt": "Capital of Lithuania?"})
    assert len(tools) == len(TOOL_PATHS)
    missing_key_error(result)
    assert "Traceback" not in result.content[0].text


def test_main_runs_the_server_without_a_key(
    no_key: None, capsys: pytest.CaptureFixture[str]
) -> None:
    serve = MagicMock(return_value="serve()")
    with (
        patch.object(server_module, "serve", serve),
        patch.object(server_module.asyncio, "run") as run,
    ):
        main()
    run.assert_called_once_with("serve()")
    assert "SCRAPEBADGER_API_KEY is not set" in capsys.readouterr().err


async def test_stdio_process_lists_tools_and_explains_the_key(tmp_path: Path) -> None:
    """The real entry point over stdio, as an MCP directory runs it: no key, no network."""
    params = StdioServerParameters(
        command=sys.executable,
        args=["-c", "from scrapebadger_mcp.server import main; main()"],
        env={"SCRAPEBADGER_API_KEY": ""},
    )
    stderr = tmp_path / "stderr.log"
    with stderr.open("w") as errlog:
        async with (
            stdio_client(params, errlog=errlog) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()
            tools = (await session.list_tools()).tools
            result = await session.call_tool("yelp_list_markets", {})
    assert sorted(tool.name for tool in tools) == sorted(TOOL_PATHS)
    missing_key_error(result)
    log = stderr.read_text()
    assert "SCRAPEBADGER_API_KEY is not set" in log
    assert "Traceback" not in log
