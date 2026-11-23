"""Google result link tool on a POST-only endpoint (SCR-667).

Listing by HTTP method and path through list_tools, dispatch through call_tool with
a mocked client, and the exact API request through the real SDK over an in-process
httpx transport and an in-memory MCP session. Nothing leaves the process.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import CallToolResult, Tool
from scrapebadger import ScrapeBadger

from scrapebadger_mcp.server import TOOL_METHODS, TOOL_PATHS, call_tool, list_tools, server

TOOL = "google_resolve_links"
PATH = "/v1/google/resolve"
GOTO = "https://www.google.com/goto?url=abc"
ROWS = [
    {"position": 1, "title": "A", "link": GOTO, "link_token": "t1", "retry_after_seconds": 0},
    {"position": 2, "title": "B", "link": GOTO, "link_token": "t2", "retry_after_seconds": 6},
    {"position": 3, "title": "C", "link": GOTO, "link_token": "t3", "retry_after_seconds": 0},
]
# One row of each kind: resolved, not ready (with a new token), failed.
RESPONSE = {
    "results": [
        {"position": 1, "title": "A", "link": "https://a.example/page"},
        {"position": 2, "title": "B", "link": GOTO, "link_token": "t2b", "retry_after_seconds": 5},
        {"position": 3, "title": "C", "link": GOTO, "link_token": "t3", "error": "failed"},
    ],
    "retry_after_seconds": 5,
}


def row(method: str, path: str, status: str = "active") -> dict[str, str]:
    """One row of the live endpoint catalog."""
    return {"method": method, "path": path, "api": path.split("/")[2], "status": status}


async def listed(monkeypatch: pytest.MonkeyPatch, rows: list[dict[str, str]]) -> dict[str, Tool]:
    monkeypatch.setattr(ScrapeBadger, "endpoints", AsyncMock(return_value=rows))
    return {tool.name: tool for tool in await list_tools()}


async def dispatched(arguments: dict[str, Any], client: Any) -> Any:
    with patch("scrapebadger_mcp.server._get_client", AsyncMock(return_value=client)):
        out = await call_tool(TOOL, arguments)
    content = out.content if isinstance(out, CallToolResult) else out
    return json.loads(content[0].text)


def mocked_client() -> MagicMock:
    client = MagicMock()
    client.google.search.resolve = AsyncMock(return_value=RESPONSE)
    return client


# ------------------------------------------------------------------ listing


def test_tool_maps_to_the_post_operation() -> None:
    assert TOOL_PATHS[TOOL] == PATH
    # Every other tool is matched as GET.
    assert TOOL_METHODS == {TOOL: "POST"}


async def test_listed_when_its_post_row_is_active(monkeypatch: pytest.MonkeyPatch) -> None:
    tools = await listed(monkeypatch, [row("POST", PATH)])
    assert list(tools) == [TOOL]
    assert (tools[TOOL].description or "").startswith("Get the real URLs")


@pytest.mark.parametrize(
    "rows",
    [
        [],
        [row("GET", PATH)],
        [row("DELETE", PATH), row("GET", "/v1/google/search")],
    ],
)
async def test_hidden_without_its_post_row(
    monkeypatch: pytest.MonkeyPatch, rows: list[dict[str, str]]
) -> None:
    assert TOOL not in await listed(monkeypatch, rows)


@pytest.mark.parametrize(
    ("status", "prefix"),
    [("deprecated", "Deprecated. "), ("temporarily_unavailable", "Temporarily unavailable. ")],
)
async def test_post_row_status_marks_the_tool(
    monkeypatch: pytest.MonkeyPatch, status: str, prefix: str
) -> None:
    # A GET row for the same path does not decide a POST tool's state.
    tools = await listed(monkeypatch, [row("GET", PATH), row("POST", PATH, status)])
    assert (tools[TOOL].description or "").startswith(prefix + "Get the real URLs")


async def test_get_tools_are_still_matched_on_get_rows_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools = await listed(
        monkeypatch,
        [
            row("POST", "/v1/google/search"),
            row("POST", "/v1/grok/ask", "deprecated"),
            row("GET", "/v1/grok/ask"),
        ],
    )
    assert list(tools) == ["grok_ask"]
    assert (tools["grok_ask"].description or "").startswith("Ask the real Grok")


async def test_an_all_get_catalog_lists_every_tool_but_the_post_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools = await listed(monkeypatch, [row("GET", path) for path in TOOL_PATHS.values()])
    assert set(tools) == set(TOOL_PATHS) - {TOOL}
    assert len(tools) == 30


async def test_default_catalog_lists_the_tool_next_to_search_google() -> None:
    names = [tool.name for tool in await list_tools()]
    assert {TOOL, "search_google"} <= set(names)
    assert len(names) == len(TOOL_PATHS) == 31


# ------------------------------------------------------- schema and wording


async def test_schema_takes_1_to_25_rows_with_a_link_token() -> None:
    schema = {t.name: t for t in await list_tools()}[TOOL].inputSchema
    assert schema["required"] == ["results"]
    assert "$defs" not in schema
    results = schema["properties"]["results"]
    assert (results["type"], results["minItems"], results["maxItems"]) == ("array", 1, 25)
    items = results["items"]
    assert items["type"] == "object"
    assert items["required"] == ["link_token"]
    assert items["additionalProperties"] is True
    token = items["properties"]["link_token"]
    assert (token["type"], token["minLength"]) == ("string", 1)


async def test_descriptions_tell_an_agent_how_to_use_it() -> None:
    tools = {t.name: t.description or "" for t in await list_tools()}
    for phrase in (
        "organic results of search_google that carry a link_token",
        "1 to 25",
        "resolved row",
        "not-ready row has link_token and retry_after_seconds (1 or more)",
        "latest link_token",
        "failed row has link_token and error: do not send it again",
        "does not wait",
        "45 to 70 seconds",
        "160 seconds",
        "Costs no credits",
    ):
        assert phrase in tools[TOOL], phrase
    search = tools["search_google"]
    assert "google.com/goto redirect carry link_token and retry_after_seconds" in search
    assert f"pass them to {TOOL}" in search


# ----------------------------------------------------------------- dispatch


async def test_dispatch_makes_one_call_and_returns_the_rows_unchanged() -> None:
    client = mocked_client()
    out = await dispatched({"results": ROWS}, client)
    # One request even though a row is not ready: the tool does not wait or loop.
    client.google.search.resolve.assert_awaited_once_with(ROWS)
    client.google.search.resolve_all.assert_not_called()
    assert out == RESPONSE


async def test_dispatch_accepts_25_rows_and_a_bare_token() -> None:
    client = mocked_client()
    rows = [{"link_token": f"t{i}"} for i in range(25)]
    await dispatched({"results": rows}, client)
    client.google.search.resolve.assert_awaited_once_with(rows)


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"results": []},
        {"results": [{"link_token": f"t{i}"} for i in range(26)]},
        {"results": [{"link": GOTO}]},
        {"results": [{"link": GOTO, "link_token": None}]},
        {"results": [{"link_token": ""}]},
        {"results": [{"link_token": 7}]},
        {"results": [{"link_token": "t1"}, {"position": 2}]},
        {"results": ["t1"]},
        {"results": "t1"},
    ],
)
async def test_rejects_out_of_contract_rows_before_the_sdk(arguments: dict[str, Any]) -> None:
    client = mocked_client()
    out = await dispatched(arguments, client)
    assert out["error_type"] == "ValidationError"
    client.google.search.resolve.assert_not_awaited()


# ---------------------------------------------------------------- transport


class Recorder:
    """An in-process API: records each request and answers with one body."""

    def __init__(self, status: int, body: dict[str, Any]) -> None:
        self.status, self.body = status, body
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return httpx.Response(self.status, json=self.body)


async def sdk_over(recorder: Recorder) -> ScrapeBadger:
    """The real SDK client, its own headers and base URL included, over the recorder."""
    client = ScrapeBadger(api_key="test", base_url="https://api.test", max_retries=0)
    http = await client._base_client._get_client()
    http._transport = httpx.MockTransport(recorder)
    return client


async def test_transport_sends_one_post_with_the_rows() -> None:
    recorder = Recorder(200, RESPONSE)
    out = await dispatched({"results": ROWS}, await sdk_over(recorder))
    assert out == RESPONSE
    [request] = recorder.requests
    assert (request.method, request.url.raw_path.decode()) == ("POST", PATH)
    assert json.loads(request.content) == {"results": ROWS}
    assert request.headers["x-api-key"] == "test"


async def test_transport_surfaces_an_api_error() -> None:
    recorder = Recorder(503, {"detail": "Temporarily unavailable."})
    client = await sdk_over(recorder)
    with patch("scrapebadger_mcp.server._get_client", AsyncMock(return_value=client)):
        out = await call_tool(TOOL, {"results": ROWS})
    assert isinstance(out, CallToolResult)
    assert out.isError
    assert json.loads(out.content[0].text)["error_type"] == "ServerError"
    assert len(recorder.requests) == 1


async def test_mcp_session_lists_and_calls_the_tool() -> None:
    recorder = Recorder(200, RESPONSE)
    client = await sdk_over(recorder)
    with patch("scrapebadger_mcp.server._get_client", AsyncMock(return_value=client)):
        async with create_connected_server_and_client_session(server) as session:
            names = {tool.name for tool in (await session.list_tools()).tools}
            result = await session.call_tool(TOOL, {"results": ROWS})
            refused = await session.call_tool(TOOL, {"results": [{"link": GOTO}]})
    assert TOOL in names
    assert not result.isError
    assert json.loads(result.content[0].text) == RESPONSE
    assert refused.isError
    assert "link_token" in refused.content[0].text
    # The row without a link_token never reached the API.
    assert [json.loads(r.content) for r in recorder.requests] == [{"results": ROWS}]
