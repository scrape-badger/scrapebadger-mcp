from unittest.mock import AsyncMock, MagicMock

from scrapebadger_mcp.server import TOOL_PATHS
from tests.test_dedicated_tools import dispatched


def test_grok_paths_are_registered():
    assert TOOL_PATHS["grok_ask"] == "/v1/grok/ask"
    assert TOOL_PATHS["grok_brand_visibility"] == "/v1/grok/brand-visibility"
    assert TOOL_PATHS["grok_get_conversation"] == "/v1/grok/conversations/{conversation_id}"
    assert TOOL_PATHS["grok_list_models"] == "/v1/grok/models"


async def test_grok_dispatch_uses_the_generated_client():
    client = MagicMock()
    client.grok.ask_grok_a_question = AsyncMock(return_value={"answer": "Vilnius."})
    client.grok.measure_brand_visibility_in_grok = AsyncMock(return_value={"mentioned": True})
    client.grok.get_a_grok_conversation = AsyncMock(return_value={"messages": []})
    client.grok.list_grok_assistant_modes = AsyncMock(return_value={"models": []})

    await dispatched(
        "grok_ask",
        {"prompt": "Capital?", "conversation_id": "42:123", "mode": "expert", "web_search": "off"},
        client,
    )
    await dispatched(
        "grok_brand_visibility",
        {"prompt": "Best APIs", "brand": "ScrapeBadger", "competitors": ["Apify"]},
        client,
    )
    await dispatched("grok_get_conversation", {"conversation_id": "42:123"}, client)
    await dispatched("grok_list_models", {}, client)

    client.grok.ask_grok_a_question.assert_awaited_once_with(
        prompt="Capital?", conversation_id="42:123", mode="expert", web_search="off"
    )
    client.grok.measure_brand_visibility_in_grok.assert_awaited_once_with(
        prompt="Best APIs",
        brand="ScrapeBadger",
        competitors=["Apify"],
        brand_domain=None,
        mode="auto",
        web_search="force",
    )
    client.grok.get_a_grok_conversation.assert_awaited_once_with("42:123")
    client.grok.list_grok_assistant_modes.assert_awaited_once_with()
