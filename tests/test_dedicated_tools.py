"""AutoScout24 listing, GitHub repository and Yelp tools (SCR-564, SCR-567, SCR-569).

Inventory and lifecycle go through list_tools; dispatch through call_tool with a
mocked client; transport through the real SDK client over an in-process httpx
transport and through an in-memory MCP session. Nothing leaves the process.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from mcp.shared.memory import create_connected_server_and_client_session
from scrapebadger import ScrapeBadger

from scrapebadger_mcp.server import TOOL_PATHS, call_tool, list_tools, server

DEDICATED = {
    "autoscout24_get_listing": "/v1/autoscout24/listing",
    "github_get_repository": "/v1/github/repositories/{owner}/{repo}",
    "yelp_search_businesses": "/v1/yelp/search",
    "yelp_list_markets": "/v1/yelp/markets",
}
LISTING_ID = "26ba8d7b-f8b3-4a08-8b03-b23574f1583d"


def catalog(rows: dict[str, str]) -> AsyncMock:
    """The live endpoint catalog as the API serves it (FastAPI path templates)."""
    return AsyncMock(
        return_value=[
            {"method": "GET", "path": path, "api": path.split("/")[2], "status": status}
            for path, status in rows.items()
        ]
    )


def dispatched(name: str, arguments: dict[str, Any], client: Any) -> Any:
    async def run() -> Any:
        with patch("scrapebadger_mcp.server._get_client", AsyncMock(return_value=client)):
            out = await call_tool(name, arguments)
        return json.loads(out[0].text)

    return run()


# ---------------------------------------------------------------- inventory


def test_paths_are_the_api_operations() -> None:
    assert {name: TOOL_PATHS[name] for name in DEDICATED} == DEDICATED


async def test_inventory_has_every_tool_once() -> None:
    names = [tool.name for tool in await list_tools()]
    assert len(names) == len(set(names)) == len(TOOL_PATHS) == 21
    assert set(DEDICATED) <= set(names)


async def test_schemas_mirror_the_source_contract() -> None:
    tools = {tool.name: tool.inputSchema for tool in await list_tools()}
    listing = tools["autoscout24_get_listing"]
    assert listing.get("required", []) == []
    assert listing["properties"]["listing_id"]["anyOf"][0]["minLength"] == 36
    assert listing["properties"]["market"]["anyOf"][0]["enum"] == [
        "de", "at", "be", "es", "fr", "it", "lu", "nl"
    ]  # fmt: skip
    repo = tools["github_get_repository"]
    assert repo["required"] == ["owner", "repo"]
    assert repo["properties"]["owner"]["pattern"] == "^[A-Za-z0-9-]+$"
    assert repo["properties"]["repo"]["maxLength"] == 100
    yelp = tools["yelp_search_businesses"]
    assert yelp["required"] == ["location"]
    assert yelp["properties"]["market"]["enum"] == ["us", "ca"]
    assert yelp["properties"]["sort_by"]["enum"] == ["recommended", "rating", "review_count"]
    page = yelp["properties"]["page"]
    assert (page["minimum"], page["maximum"], page["default"]) == (1, 11, 1)
    assert tools["yelp_list_markets"].get("properties", {}) == {}


# ---------------------------------------------------------------- lifecycle


async def test_lifecycle_applies_to_the_new_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ScrapeBadger,
        "endpoints",
        catalog(
            {
                "/v1/yelp/search": "temporarily_unavailable",
                "/v1/yelp/markets": "active",
                # Placeholder names differ from the tool map; templates still match.
                "/v1/github/repositories/{o}/{r}": "deprecated",
            }
        ),
    )
    tools = {tool.name: tool for tool in await list_tools()}
    assert set(tools) == {"yelp_search_businesses", "yelp_list_markets", "github_get_repository"}
    assert tools["yelp_search_businesses"].description.startswith("Temporarily unavailable. ")
    assert tools["github_get_repository"].description.startswith("Deprecated. ")
    assert tools["yelp_list_markets"].description.startswith("List the Yelp sites")


async def test_tools_stay_hidden_until_the_catalog_lists_them(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    live = {path: "active" for name, path in TOOL_PATHS.items() if name not in DEDICATED}
    monkeypatch.setattr(ScrapeBadger, "endpoints", catalog(live))
    names = {tool.name for tool in await list_tools()}
    assert names == set(TOOL_PATHS) - set(DEDICATED)


# ---------------------------------------------------------------- dispatch


async def test_listing_dispatch_keeps_every_native_field() -> None:
    native = {
        "market": "it",
        "listing": {"id": LISTING_ID, "vehicle": {"rawData": {"equipment": ["x"]}}},
        "latency_ms": 812,
    }
    client = MagicMock()
    client.autoscout24.get_listing = AsyncMock(return_value=native)
    out = await dispatched(
        "autoscout24_get_listing", {"listing_id": LISTING_ID, "market": "it"}, client
    )
    client.autoscout24.get_listing.assert_awaited_once_with(
        url=None, listing_id=LISTING_ID, market="it"
    )
    assert out == native


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"url": "https://www.autoscout24.de/angebote/x", "listing_id": LISTING_ID},
        {"listing_id": "short"},
        {"url": "https://www.autoscout24.ch/angebote/x", "market": "ch"},
    ],
)
async def test_listing_rejects_bad_locators_before_the_sdk(arguments: dict[str, Any]) -> None:
    client = MagicMock()
    client.autoscout24.get_listing = AsyncMock()
    out = await dispatched("autoscout24_get_listing", arguments, client)
    assert out["error_type"] == "ValidationError"
    client.autoscout24.get_listing.assert_not_awaited()


async def test_repository_dispatch_passes_segments_to_the_sdk() -> None:
    client = MagicMock()
    client.github.get_repository = AsyncMock(return_value={"repository": {"name": "cli"}})
    out = await dispatched("github_get_repository", {"owner": "cli", "repo": "cli"}, client)
    client.github.get_repository.assert_awaited_once_with("cli", "cli")
    assert out == {"repository": {"name": "cli"}}


@pytest.mark.parametrize(
    "arguments",
    [
        {"owner": "cli/cli", "repo": "cli"},
        {"owner": "cli", "repo": ".."},
        {"owner": "cli", "repo": "a/b"},
        {"owner": "", "repo": "cli"},
        {"owner": "cli"},
    ],
)
async def test_repository_rejects_non_segments(arguments: dict[str, Any]) -> None:
    client = MagicMock()
    client.github.get_repository = AsyncMock()
    out = await dispatched("github_get_repository", arguments, client)
    assert out["error_type"] == "ValidationError"
    client.github.get_repository.assert_not_awaited()


async def test_yelp_search_dispatch_uses_the_sdk_signature() -> None:
    client = MagicMock()
    client.yelp.search_businesses = AsyncMock(return_value={"results": [], "ads": []})
    await dispatched(
        "yelp_search_businesses",
        {"location": "Toronto, ON", "query": "pizza", "market": "ca", "page": 11},
        client,
    )
    client.yelp.search_businesses.assert_awaited_once_with(
        location="Toronto, ON",
        query="pizza",
        market="ca",
        category=None,
        sort_by="recommended",
        price=None,
        features=None,
        page=11,
    )


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"location": "SF", "page": 12},
        {"location": "SF", "page": 0},
        {"location": "London", "market": "gb"},
        {"location": "SF", "price": "5"},
        {"location": "SF", "category": "Pizza Places"},
        {"location": "SF", "sort_by": "distance"},
    ],
)
async def test_yelp_search_rejects_out_of_contract_input(arguments: dict[str, Any]) -> None:
    client = MagicMock()
    client.yelp.search_businesses = AsyncMock()
    out = await dispatched("yelp_search_businesses", arguments, client)
    assert out["error_type"] == "ValidationError"
    client.yelp.search_businesses.assert_not_awaited()


async def test_yelp_markets_dispatch() -> None:
    client = MagicMock()
    client.yelp.list_markets = AsyncMock(return_value={"markets": [{"code": "us"}]})
    out = await dispatched("yelp_list_markets", {}, client)
    client.yelp.list_markets.assert_awaited_once_with()
    assert out == {"markets": [{"code": "us"}]}


# ---------------------------------------------------------------- transport


class Recorder:
    """An in-process API: records each request and answers from a table."""

    def __init__(self, answers: dict[str, tuple[int, dict[str, Any]]]) -> None:
        self.answers = answers
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        status, body = self.answers[request.url.path]
        return httpx.Response(status, json=body)


async def sdk_over(recorder: Recorder) -> ScrapeBadger:
    """The real SDK client, its own headers and base URL included, over the recorder."""
    client = ScrapeBadger(api_key="test", base_url="https://api.test", max_retries=0)
    http = await client._base_client._get_client()
    http._transport = httpx.MockTransport(recorder)
    return client


async def test_transport_sends_the_exact_api_requests() -> None:
    body = {"listing": {"vehicle": {"rawData": {"k": 1}}}, "results": [{"position": 1}]}
    recorder = Recorder(
        {
            "/v1/autoscout24/listing": (200, body),
            "/v1/github/repositories/my-org/my_repo.js": (200, body),
            "/v1/yelp/search": (200, body),
            "/v1/yelp/markets": (200, {"markets": []}),
        }
    )
    client = await sdk_over(recorder)
    calls = [
        ("autoscout24_get_listing", {"url": "https://www.autoscout24.de/angebote/a-b"}),
        ("github_get_repository", {"owner": "my-org", "repo": "my_repo.js"}),
        ("yelp_search_businesses", {"location": "San Francisco, CA", "features": "delivery"}),
        ("yelp_list_markets", {}),
    ]
    outputs = [await dispatched(name, arguments, client) for name, arguments in calls]
    assert outputs[:3] == [body, body, body]
    sent = [(r.method, r.url.raw_path.decode()) for r in recorder.requests]
    assert sent == [
        ("GET", "/v1/autoscout24/listing?url=https%3A%2F%2Fwww.autoscout24.de%2Fangebote%2Fa-b"),
        ("GET", "/v1/github/repositories/my-org/my_repo.js"),
        (
            "GET",
            "/v1/yelp/search?location=San+Francisco%2C+CA&market=us"
            "&sort_by=recommended&features=delivery&page=1",
        ),
        ("GET", "/v1/yelp/markets"),
    ]
    assert all(r.headers["x-api-key"] == "test" for r in recorder.requests)


async def test_transport_surfaces_a_disabled_operation_as_an_error() -> None:
    refusal = {"error": "endpoint_unavailable", "detail": "Temporarily unavailable."}
    client = await sdk_over(Recorder({"/v1/yelp/search": (423, refusal)}))
    out = await dispatched("yelp_search_businesses", {"location": "Austin, TX"}, client)
    assert out["error_type"] == "ScrapeBadgerError"


async def test_mcp_session_lists_and_calls_the_new_tools() -> None:
    recorder = Recorder({"/v1/yelp/markets": (200, {"markets": [{"code": "ca"}]})})
    client = await sdk_over(recorder)
    with patch("scrapebadger_mcp.server._get_client", AsyncMock(return_value=client)):
        async with create_connected_server_and_client_session(server) as session:
            names = {tool.name for tool in (await session.list_tools()).tools}
            result = await session.call_tool("yelp_list_markets", {})
    assert set(DEDICATED) <= names
    assert json.loads(result.content[0].text) == {"markets": [{"code": "ca"}]}
