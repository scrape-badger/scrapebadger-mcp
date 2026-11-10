"""Google AI Mode tool with location targeting (SCR-610).

Schema through list_tools, dispatch through call_tool with a mocked client, and
the exact API request through the real SDK over an in-process httpx transport.
"""

from __future__ import annotations

import inspect
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from mcp.types import CallToolResult
from scrapebadger import ScrapeBadger
from scrapebadger.google.ai_mode import AiModeClient

from scrapebadger_mcp.server import TOOL_PATHS, call_tool, list_tools

TOOL = "google_ai_mode_search"
WONJU = "Wonju-si,Gangwon-do,South Korea"
ANSWER = {"markdown": "...", "text_blocks": [], "references": [], "country": "kr"}

# location/uule/lat/lon reach the API from scrapebadger 0.77.0 on.
SDK_HAS_LOCATION = "location" in inspect.signature(AiModeClient.search).parameters


async def dispatched(arguments: dict[str, Any], client: Any) -> Any:
    with patch("scrapebadger_mcp.server._get_client", AsyncMock(return_value=client)):
        out = await call_tool(TOOL, arguments)
    content = out.content if isinstance(out, CallToolResult) else out
    return json.loads(content[0].text)


def mocked_client() -> MagicMock:
    client = MagicMock()
    client.google.ai_mode.search = AsyncMock(return_value=ANSWER)
    return client


def test_tool_maps_to_the_api_operation() -> None:
    assert TOOL_PATHS[TOOL] == "/v1/google/ai-mode/search"


async def test_schema_offers_the_location_params() -> None:
    tool = {t.name: t for t in await list_tools()}[TOOL]
    schema = tool.inputSchema
    assert schema["required"] == ["q"]
    props = schema["properties"]
    assert {"location", "uule", "lat", "lon", "gl", "hl", "include_html"} <= set(props)
    lat, lon = props["lat"]["anyOf"][0], props["lon"]["anyOf"][0]
    assert (lat["minimum"], lat["maximum"], lon["minimum"], lon["maximum"]) == (-90, 90, -180, 180)
    assert props["gl"]["default"] is None
    assert props["include_html"]["default"] is False
    assert "only one of" in props["location"]["description"]
    assert "near me" in (tool.description or "")


async def test_location_dispatch_leaves_gl_to_the_api() -> None:
    client = mocked_client()
    out = await dispatched({"q": "best coffee near me", "location": WONJU, "hl": "ko"}, client)
    client.google.ai_mode.search.assert_awaited_once_with(
        q="best coffee near me", hl="ko", include_html=False, location=WONJU
    )
    assert out == ANSWER


async def test_unlocated_and_coordinate_dispatch() -> None:
    client = mocked_client()
    await dispatched({"q": "what is kubernetes"}, client)
    client.google.ai_mode.search.assert_awaited_once_with(
        q="what is kubernetes", hl="en", include_html=False
    )

    client = mocked_client()
    await dispatched({"q": "맛집 추천", "lat": 35.1763, "lon": 129.0798, "gl": "kr"}, client)
    client.google.ai_mode.search.assert_awaited_once_with(
        q="맛집 추천", gl="kr", hl="en", include_html=False, lat=35.1763, lon=129.0798
    )


@pytest.mark.parametrize(
    "arguments",
    [
        {"q": "cafe", "location": WONJU, "lat": 37.3, "lon": 127.9},
        {"q": "cafe", "location": WONJU, "uule": "w+abc"},
        {"q": "cafe", "uule": "w+abc", "lat": 37.3, "lon": 127.9},
        {"q": "cafe", "lat": 37.3},
        {"q": "cafe", "lon": 127.9},
        {"q": "cafe", "lat": 91, "lon": 0},
        {"q": "cafe", "lat": 0, "lon": 181},
        {"q": ""},
        {},
    ],
)
async def test_rejects_out_of_contract_targeting_before_the_sdk(arguments: dict[str, Any]) -> None:
    client = mocked_client()
    out = await dispatched(arguments, client)
    assert out["error_type"] == "ValidationError"
    client.google.ai_mode.search.assert_not_awaited()


class Recorder:
    """An in-process API: records each request and answers with one body."""

    def __init__(self, status: int, body: dict[str, Any]) -> None:
        self.status, self.body = status, body
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return httpx.Response(self.status, json=self.body)


async def sdk_over(recorder: Recorder) -> ScrapeBadger:
    client = ScrapeBadger(api_key="test", base_url="https://api.test", max_retries=0)
    http = await client._base_client._get_client()
    http._transport = httpx.MockTransport(recorder)
    return client


@pytest.mark.skipif(not SDK_HAS_LOCATION, reason="needs scrapebadger>=0.77.0")
async def test_transport_sends_the_exact_located_request() -> None:
    echo = {"requested": WONJU, "resolved": WONJU, "latitude": None, "longitude": None}
    recorder = Recorder(200, {**ANSWER, "location": {**echo, "uule": "w+x"}})
    client = await sdk_over(recorder)
    out = await dispatched({"q": "best coffee near me", "location": WONJU, "hl": "ko"}, client)
    assert out["location"]["resolved"] == WONJU
    assert recorder.requests[0].url.raw_path.decode() == (
        "/v1/google/ai-mode/search?q=best+coffee+near+me&hl=ko&include_html=false"
        "&location=Wonju-si%2CGangwon-do%2CSouth+Korea"
    )


async def test_transport_surfaces_a_targeting_422_as_an_error() -> None:
    detail = "Unknown location; use a canonical Google location name or lat/lon."
    client = await sdk_over(Recorder(422, {"detail": detail}))
    out = await dispatched({"q": "cafe"}, client)
    assert out["error_type"] == "ValidationError"
    assert "Unknown location" in out["error"]
