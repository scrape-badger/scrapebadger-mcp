"""ScrapeBadger MCP Server.

This module implements the Model Context Protocol (MCP) server for ScrapeBadger,
providing AI agents with access to Twitter/X scraping, Google Search, AutoScout24
listing detail, GitHub repository detail and Yelp business search.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Annotated, Any, Literal

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, TextContent, Tool
from pydantic import BaseModel, Field, field_validator, model_validator
from scrapebadger import ScrapeBadger, ScrapeBadgerError

TOOL_PATHS = {
    "get_twitter_user_profile": "/v1/twitter/users/{username}/by_username",
    "get_twitter_user_about": "/v1/twitter/users/{username}/about",
    "search_twitter_users": "/v1/twitter/users/search_users",
    "get_twitter_followers": "/v1/twitter/users/{username}/followers",
    "get_twitter_following": "/v1/twitter/users/{username}/followings",
    "get_twitter_tweet": "/v1/twitter/tweets/tweet/{tweet_id}",
    "get_twitter_user_tweets": "/v1/twitter/users/{username}/latest_tweets",
    "search_twitter_tweets": "/v1/twitter/tweets/advanced_search",
    "get_twitter_trends": "/v1/twitter/trends/",
    "get_twitter_place_trends": "/v1/twitter/trends/place/{woeid}",
    "search_twitter_places": "/v1/twitter/geo/search",
    "get_twitter_list_detail": "/v1/twitter/lists/{list_id}/detail",
    "search_twitter_lists": "/v1/twitter/lists/search",
    "get_twitter_list_tweets": "/v1/twitter/lists/{list_id}/tweets",
    "get_twitter_community_detail": "/v1/twitter/communities/{community_id}",
    "search_twitter_communities": "/v1/twitter/communities/search",
    "search_google": "/v1/google/search",
    "autoscout24_get_listing": "/v1/autoscout24/listing",
    "github_get_repository": "/v1/github/repositories/{owner}/{repo}",
    "yelp_search_businesses": "/v1/yelp/search",
    "yelp_list_markets": "/v1/yelp/markets",
    "facebook_marketplace_search": "/v1/facebook/marketplace/search",
    "facebook_marketplace_item": "/v1/facebook/marketplace/item/{item_id}",
}

# Initialize MCP server
server = Server("scrapebadger")

# Global client instance (initialized on first use)
_client: ScrapeBadger | None = None


def _get_api_key() -> str:
    """Get API key from environment."""
    api_key = os.environ.get("SCRAPEBADGER_API_KEY")
    if not api_key:
        raise ValueError(
            "SCRAPEBADGER_API_KEY environment variable is required. "
            "Get your API key at https://scrapebadger.com"
        )
    return api_key


async def _get_client() -> ScrapeBadger:
    """Get or create the ScrapeBadger client."""
    global _client
    if _client is None:
        _client = ScrapeBadger(api_key=_get_api_key())
    return _client


def _serialize_model(obj: Any) -> dict[str, Any]:
    """Serialize a Pydantic model or dict to JSON-compatible dict."""
    if hasattr(obj, "model_dump"):
        dumped: dict[str, Any] = obj.model_dump(mode="json")
        return dumped
    if isinstance(obj, dict):
        return obj
    return {"data": str(obj)}


# =============================================================================
# Tool Definitions
# =============================================================================

NO_CACHE_DESCRIPTION = (
    "Skip the 60-second duplicate-request cache and fetch a fresh result; billed as a normal call."
)


class NoCacheArgs(BaseModel):
    """The cache bypass every billed tool accepts."""

    no_cache: bool = Field(default=False, description=NO_CACHE_DESCRIPTION)


class GetUserProfileArgs(NoCacheArgs):
    """Arguments for getting a user profile."""

    username: str = Field(description="Twitter username (without @)")


class GetUserAboutArgs(NoCacheArgs):
    """Arguments for getting extended user info."""

    username: str = Field(description="Twitter username (without @)")


class SearchUsersArgs(NoCacheArgs):
    """Arguments for searching users."""

    query: str = Field(description="Search query string")
    max_results: int = Field(default=20, ge=1, le=100, description="Max results (1-100)")


class GetFollowersArgs(NoCacheArgs):
    """Arguments for getting followers."""

    username: str = Field(description="Twitter username (without @)")
    max_results: int = Field(default=50, ge=1, le=200, description="Max results (1-200)")


class GetFollowingArgs(NoCacheArgs):
    """Arguments for getting following."""

    username: str = Field(description="Twitter username (without @)")
    max_results: int = Field(default=50, ge=1, le=200, description="Max results (1-200)")


class GetTweetArgs(NoCacheArgs):
    """Arguments for getting a tweet."""

    tweet_id: str = Field(description="Tweet ID")


class GetUserTweetsArgs(NoCacheArgs):
    """Arguments for getting user tweets."""

    username: str = Field(description="Twitter username (without @)")
    max_results: int = Field(default=20, ge=1, le=100, description="Max results (1-100)")


class SearchTweetsArgs(NoCacheArgs):
    """Arguments for searching tweets."""

    query: str = Field(description="Search query string")
    max_results: int = Field(default=20, ge=1, le=100, description="Max results (1-100)")


class GetTrendsArgs(NoCacheArgs):
    """Arguments for getting trends."""

    category: str | None = Field(
        default=None,
        description="Trend category: 'news', 'sports', 'entertainment', or None for all",
    )


class GetPlaceTrendsArgs(NoCacheArgs):
    """Arguments for getting place trends."""

    woeid: int = Field(description="Where On Earth ID (e.g., 23424977 for US, 44418 for London)")


class SearchPlacesArgs(NoCacheArgs):
    """Arguments for searching places."""

    query: str = Field(description="Place name to search")


class GetListDetailArgs(NoCacheArgs):
    """Arguments for getting list detail."""

    list_id: str = Field(description="Twitter list ID")


class SearchListsArgs(NoCacheArgs):
    """Arguments for searching lists."""

    query: str = Field(description="Search query for lists")
    max_results: int = Field(default=20, ge=1, le=50, description="Max results (1-50)")


class GetListTweetsArgs(NoCacheArgs):
    """Arguments for getting list tweets."""

    list_id: str = Field(description="Twitter list ID")
    max_results: int = Field(default=20, ge=1, le=100, description="Max results (1-100)")


class GetCommunityDetailArgs(NoCacheArgs):
    """Arguments for getting community detail."""

    community_id: str = Field(description="Twitter community ID")


class SearchCommunitiesArgs(NoCacheArgs):
    """Arguments for searching communities."""

    query: str = Field(description="Search query for communities")


class SearchGoogleArgs(NoCacheArgs):
    """Arguments for a Google web search."""

    q: str = Field(description="Search query (supports Google operators like site:, intitle:)")
    gl: str = Field(default="us", description="Country code (e.g. us, gb, de)")
    hl: str = Field(default="en", description="Language code (e.g. en, fr, de)")
    start: int = Field(default=0, ge=0, description="Result offset for paging (0, 10, 20, ...)")
    location: str | None = Field(
        default=None, description="City-level geo-targeting (e.g. 'New York, USA')"
    )
    ai_overview: bool = Field(
        default=False,
        description=(
            "Also fetch an AI Overview that Google loads after the page, and resolve "
            "its source links."
        ),
    )
    expand_related_questions: bool | Annotated[int, Field(ge=0, le=99)] | None = Field(
        default=None,
        description=(
            "Open the People Also Ask questions and return their answers: true opens "
            "every question the page shows (usually four), a number N opens the first N. "
            "Each answered question gets text_blocks and references. Each answered "
            "question costs one more search (credits = 20 x (1 + answered)); a question "
            "whose answer does not come back is not billed. Adds about a second per question."
        ),
    )

    domain: str | None = Field(default=None, description="Google domain country hint.")
    uule: str | None = Field(default=None, description="Encoded Google location.")
    lr: str | None = Field(default=None, description="Result language restrict.")
    tbs: str | None = Field(default=None, description="Google search filters.")
    safe: str | None = Field(default=None, description="off or active.")
    filter: int | None = Field(default=None, description="Omitted-results filter: 0 or 1.")
    nfpr: int | None = Field(default=None, description="Disable spelling correction.")
    output: str | None = Field(default=None, description="json or html.")
    device: str | None = Field(default=None, description="Device target.")
    user_agent: str | None = Field(default=None, description="Custom User-Agent.")
    cr: str | None = Field(default=None, description="Country restrict.")
    ludocid: str | None = Field(default=None, description="Place CID.")
    lsig: str | None = Field(default=None, description="Map view ID.")
    kgmid: str | None = Field(default=None, description="Knowledge Graph entity ID.")
    si: str | None = Field(default=None, description="Cached Google parameters.")
    ibp: str | None = Field(default=None, description="Layout control.")
    uds: str | None = Field(default=None, description="Google filter string.")
    google_domain: str | None = Field(
        default=None,
        description="Alias for domain; Google requests use google.com with country targeting.",
    )
    lat: float | None = Field(
        default=None, description="Latitude; supply together with lon instead of location or uule."
    )
    lon: float | None = Field(default=None, description="Longitude; supply together with lat.")
    radius: float | None = Field(
        default=None,
        description="Accuracy in meters; needs lat/lon or a city with a known center.",
    )
    color_scheme: Literal["light", "dark"] | None = Field(
        default=None, description="Google color scheme."
    )
    tbm: Literal["isch", "lcl", "vid", "nws", "shop", "pts", "bks"] | None = Field(
        default=None,
        description="Search type; use output=html or the dedicated vertical APIs.",
    )
    udm: str | None = Field(
        default=None,
        description="Google result filter: 14 web, 18 forums. Other verticals require output=html.",
    )
    no_cache: bool = Field(
        default=False, description="Bypass result caches and request a fresh Google fetch."
    )
    as_dt: str | None = Field(
        default=None, description="Site restriction mode: i includes, e excludes as_sitesearch."
    )
    as_epq: str | None = Field(default=None, description="Exact phrase.")
    as_eq: str | None = Field(default=None, description="Words to exclude.")
    as_lq: str | None = Field(
        default=None, description="Find pages linking to this URL; availability depends on Google."
    )
    as_nlo: str | None = Field(default=None, description="Numeric range minimum.")
    as_nhi: str | None = Field(default=None, description="Numeric range maximum.")
    as_oq: str | None = Field(default=None, description="Match any of these words.")
    as_q: str | None = Field(default=None, description="Additional query words.")
    as_qdr: str | None = Field(default=None, description="Time range, such as d, w, m or y1.")
    as_rq: str | None = Field(
        default=None, description="Related URL; availability depends on Google."
    )
    as_sitesearch: str | None = Field(default=None, description="Restrict results to a site.")
    oq: str | None = Field(
        default=None,
        description="Original query sent to Google. Defaults to q; an empty string omits it.",
    )
    sourceid: str | None = Field(
        default=None,
        description="Google source identifier. Defaults to chrome; an empty string omits it.",
    )
    ie: str | None = Field(
        default=None,
        description="Google input encoding hint. Defaults to UTF-8; an empty string omits it.",
    )
    num: int | None = Field(default=None, description="Results per page.")
    mode: str | None = Field(default=None, description="full or fast.")


class GetAutoscout24ListingArgs(NoCacheArgs):
    """Arguments for AutoScout24 listing detail: exactly one url or listing_id."""

    url: str | None = Field(
        default=None,
        max_length=2048,
        description="Full HTTPS listing URL from vehicle search results. Supply url or "
        "listing_id, not both.",
    )
    listing_id: str | None = Field(
        default=None,
        min_length=36,
        max_length=36,
        description="Listing UUID from search results.",
    )
    market: Literal["de", "at", "be", "es", "fr", "it", "lu", "nl"] | None = Field(
        default=None,
        description="Inferred from url, otherwise de. An explicit market must match the URL host.",
    )

    @model_validator(mode="after")
    def _exactly_one_locator(self) -> GetAutoscout24ListingArgs:
        if (self.url is None) == (self.listing_id is None):
            raise ValueError("Supply exactly one of url or listing_id")
        return self


class GetGitHubRepositoryArgs(NoCacheArgs):
    """Arguments for public GitHub repository detail."""

    owner: str = Field(
        min_length=1,
        max_length=39,
        pattern=r"^[A-Za-z0-9-]+$",
        description="Owner login, e.g. cli (owner.login from a profile repository summary).",
    )
    repo: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[A-Za-z0-9_.-]+$",
        description="Repository name, e.g. cli. Not a URL.",
    )

    @field_validator("repo")
    @classmethod
    def _not_dot_segment(cls, value: str) -> str:
        if value in {".", ".."}:
            raise ValueError("repo must not be . or ..")
        return value


class SearchYelpBusinessesArgs(NoCacheArgs):
    """Arguments for a Yelp business search."""

    location: str = Field(
        min_length=1,
        max_length=128,
        description="Where to search, as typed into Yelp: city, neighbourhood, address or "
        "postcode.",
    )
    query: str | None = Field(
        default=None,
        max_length=128,
        description="What to search for (e.g. pizza, plumbers). Optional when category is set.",
    )
    market: Literal["us", "ca"] = Field(
        default="us", description="Yelp site: us (www.yelp.com) or ca (www.yelp.ca)."
    )
    category: str | None = Field(
        default=None,
        pattern=r"^[a-z0-9_-]{1,64}$",
        description="Yelp category alias, e.g. pizza, coffee, plumbing.",
    )
    sort_by: Literal["recommended", "rating", "review_count"] = Field(
        default="recommended", description="Yelp's own result order."
    )
    price: str | None = Field(
        default=None,
        pattern=r"^[1-4](,[1-4]){0,3}$",
        description="Comma-separated price levels 1-4 ($ to $$$$), e.g. 1,2.",
    )
    features: str | None = Field(
        default=None,
        description="Comma-separated refinements: delivery, takeout, reservations, "
        "outdoor_seating, good_for_kids, dogs_allowed, free_wifi, wheelchair_accessible.",
    )
    page: int = Field(
        default=1, ge=1, le=11, description="1-based page, ten businesses each; pages 1-11."
    )


class SearchMarketplaceArgs(NoCacheArgs):
    """Account-free public Marketplace search with verified filters."""

    query: str = Field(min_length=1)
    location: str = "london"
    radius: int | None = Field(default=None, ge=1, le=500)
    min_price: str | None = None
    max_price: str | None = None
    days_since_listed: str | None = "2"
    sort_by: str = "creation_time_descend"
    strict_filters: bool = True
    include_details: bool = False
    after: str | None = None


class GetMarketplaceItemArgs(NoCacheArgs):
    """A public listing ID from Marketplace search."""

    item_id: str = Field(pattern=r"^[0-9]{1,32}$")


class ListYelpMarketsArgs(BaseModel):
    """The Yelp markets list takes no arguments."""


# =============================================================================
# Tool Handlers
# =============================================================================


@server.list_tools()  # type: ignore[no-untyped-call, untyped-decorator]
async def list_tools() -> list[Tool]:
    """List all available tools."""
    tools = [
        # User tools
        Tool(
            name="get_twitter_user_profile",
            description=(
                "Get a Twitter/X user's profile by username. Returns name, bio, "
                "follower count, following count, verified status, and more."
            ),
            inputSchema=GetUserProfileArgs.model_json_schema(),
        ),
        Tool(
            name="get_twitter_user_about",
            description=(
                "Get extended 'About' information for a Twitter/X user including "
                "account location, username change history, and verification details."
            ),
            inputSchema=GetUserAboutArgs.model_json_schema(),
        ),
        Tool(
            name="search_twitter_users",
            description=(
                "Search for Twitter/X users by query. Returns matching profiles "
                "with bios, follower counts, and verification status."
            ),
            inputSchema=SearchUsersArgs.model_json_schema(),
        ),
        Tool(
            name="get_twitter_followers",
            description=(
                "Get followers of a Twitter/X user. Returns list of follower "
                "profiles with their bios and follower counts."
            ),
            inputSchema=GetFollowersArgs.model_json_schema(),
        ),
        Tool(
            name="get_twitter_following",
            description=(
                "Get accounts that a Twitter/X user is following. Returns list "
                "of following profiles with their bios and follower counts."
            ),
            inputSchema=GetFollowingArgs.model_json_schema(),
        ),
        # Tweet tools
        Tool(
            name="get_twitter_tweet",
            description=(
                "Get a single tweet by ID. Returns tweet text, author, metrics "
                "(likes, retweets, replies), media, polls, and quoted tweets."
            ),
            inputSchema=GetTweetArgs.model_json_schema(),
        ),
        Tool(
            name="get_twitter_user_tweets",
            description=(
                "Get recent tweets from a Twitter/X user. Returns tweets with "
                "text, metrics, media, and engagement data."
            ),
            inputSchema=GetUserTweetsArgs.model_json_schema(),
        ),
        Tool(
            name="search_twitter_tweets",
            description=(
                "Search for tweets by query. Returns matching tweets with text, "
                "authors, metrics, and media. Supports advanced Twitter search operators."
            ),
            inputSchema=SearchTweetsArgs.model_json_schema(),
        ),
        # Trend tools
        Tool(
            name="get_twitter_trends",
            description=(
                "Get current trending topics on Twitter/X. Optionally filter by "
                "category (news, sports, entertainment). Returns trend names and tweet counts."
            ),
            inputSchema=GetTrendsArgs.model_json_schema(),
        ),
        Tool(
            name="get_twitter_place_trends",
            description=(
                "Get trending topics for a specific location using WOEID. "
                "Common WOEIDs: US=23424977, UK=23424975, Japan=23424856."
            ),
            inputSchema=GetPlaceTrendsArgs.model_json_schema(),
        ),
        # Geo tools
        Tool(
            name="search_twitter_places",
            description=(
                "Search for Twitter places by name. Returns place names, types, "
                "and full location details for use with geolocated tweets."
            ),
            inputSchema=SearchPlacesArgs.model_json_schema(),
        ),
        # List tools
        Tool(
            name="get_twitter_list_detail",
            description=(
                "Get details about a Twitter list including name, description, "
                "member count, subscriber count, and owner information."
            ),
            inputSchema=GetListDetailArgs.model_json_schema(),
        ),
        Tool(
            name="search_twitter_lists",
            description=(
                "Search for Twitter lists by query. Returns matching lists "
                "with names, descriptions, and member counts."
            ),
            inputSchema=SearchListsArgs.model_json_schema(),
        ),
        Tool(
            name="get_twitter_list_tweets",
            description=(
                "Get recent tweets from a Twitter list. Returns tweets from "
                "all list members with text, metrics, and media."
            ),
            inputSchema=GetListTweetsArgs.model_json_schema(),
        ),
        # Community tools
        Tool(
            name="get_twitter_community_detail",
            description=(
                "Get details about a Twitter community including name, description, "
                "member count, rules, and admin information."
            ),
            inputSchema=GetCommunityDetailArgs.model_json_schema(),
        ),
        Tool(
            name="search_twitter_communities",
            description=(
                "Search for Twitter communities by query. Returns matching "
                "communities with names, descriptions, and member counts."
            ),
            inputSchema=SearchCommunitiesArgs.model_json_schema(),
        ),
        # Google tools
        Tool(
            name="search_google",
            description=(
                "Search Google and get the structured results page: organic results, ads, "
                "knowledge graph, AI Overview, People Also Ask, shopping results, "
                "perspectives, discussions and forums, short videos and related searches. "
                "Set expand_related_questions to also get the People Also Ask answers."
            ),
            inputSchema=SearchGoogleArgs.model_json_schema(),
        ),
        # Dedicated APIs (SCR-564, SCR-567, SCR-569)
        Tool(
            name="autoscout24_get_listing",
            description=(
                "Get full AutoScout24 listing detail: native specifications, equipment, "
                "photos, prices and public seller data. Supply exactly one url or listing_id "
                "from vehicle search; the URL decides the market, otherwise de. 10 credits; "
                "removed or missing listings are unbilled 404s. Swiss listings are unsupported."
            ),
            inputSchema=GetAutoscout24ListingArgs.model_json_schema(),
        ),
        Tool(
            name="github_get_repository",
            description=(
                "Get a public GitHub repository on its default branch: statistics, topics, "
                "license, native README, root files and latest commit. Pass owner and repo "
                "separately, not a URL. 10 credits per successful uncached call."
            ),
            inputSchema=GetGitHubRepositoryArgs.model_json_schema(),
        ),
        Tool(
            name="yelp_search_businesses",
            description=(
                "Search Yelp businesses for a location (US or Canada) in Yelp's own order, "
                "with rating, review count, categories, price, address and opening hours; "
                "sponsored listings come back separately in ads. Ten per page, pages 1-11. "
                "15 credits per page with results; empty searches, errors and cache hits are "
                "free. Follow next_page while has_next_page is true."
            ),
            inputSchema=SearchYelpBusinessesArgs.model_json_schema(),
        ),
        Tool(
            name="facebook_marketplace_search",
            description="Search public Facebook Marketplace without an account. Verified filters "
            "enforce radius in km and age; include_details adds description and public photos. "
            "Coverage is partial. Follow opaque end_cursor; an empty filtered page can still "
            "have a continuation. Sort all collected pages for newest-first monitoring.",
            inputSchema=SearchMarketplaceArgs.model_json_schema(),
        ),
        Tool(
            name="facebook_marketplace_item",
            description="Get public Marketplace listing detail: description, exposed photo URLs, "
            "seller and approximate coordinates. No Facebook account needed.",
            inputSchema=GetMarketplaceItemArgs.model_json_schema(),
        ),
        Tool(
            name="yelp_list_markets",
            description="List the Yelp sites this API searches (us, ca). Free.",
            inputSchema=ListYelpMarketsArgs.model_json_schema(),
        ),
    ]

    import re

    entries = await (await _get_client()).endpoints()

    def normalize(path: str) -> str:
        return re.sub(r"\{[^}]+\}", "{}", path).rstrip("/")

    states = {normalize(row["path"]): row["status"] for row in entries if row["method"] == "GET"}
    visible = []
    for tool in tools:
        path = TOOL_PATHS[tool.name]
        state = states.get(normalize(path))
        if state is None:
            continue
        if state != "active":
            tool = tool.model_copy(
                update={
                    "description": state.replace("_", " ").capitalize()
                    + ". "
                    + (tool.description or "")
                }
            )
        visible.append(tool)
    return visible


@server.call_tool()  # type: ignore[untyped-decorator]
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent] | CallToolResult:
    """Handle tool calls."""
    try:
        client = await _get_client()
        if NoCacheArgs.model_validate(arguments).no_cache:
            # Sends Cache-Control: no-cache on every request this tool makes.
            client = client.with_options(no_cache=True)
        result: Any = None
        args: Any  # each branch validates into its own args model

        # User tools
        if name == "get_twitter_user_profile":
            args = GetUserProfileArgs(**arguments)
            result = await client.twitter.users.get_by_username(args.username)

        elif name == "get_twitter_user_about":
            args = GetUserAboutArgs(**arguments)
            result = await client.twitter.users.get_about(args.username)

        elif name == "search_twitter_users":
            args = SearchUsersArgs(**arguments)
            users = []
            async for user in client.twitter.users.search_all(
                args.query, max_items=args.max_results
            ):
                users.append(_serialize_model(user))
            result = {"users": users, "count": len(users)}

        elif name == "get_twitter_followers":
            args = GetFollowersArgs(**arguments)
            followers = []
            async for user in client.twitter.users.get_followers_all(
                args.username, max_items=args.max_results
            ):
                followers.append(_serialize_model(user))
            result = {"followers": followers, "count": len(followers)}

        elif name == "get_twitter_following":
            args = GetFollowingArgs(**arguments)
            following = []
            async for user in client.twitter.users.get_following_all(
                args.username, max_items=args.max_results
            ):
                following.append(_serialize_model(user))
            result = {"following": following, "count": len(following)}

        # Tweet tools
        elif name == "get_twitter_tweet":
            args = GetTweetArgs(**arguments)
            result = await client.twitter.tweets.get_by_id(args.tweet_id)

        elif name == "get_twitter_user_tweets":
            args = GetUserTweetsArgs(**arguments)
            tweets = []
            async for tweet in client.twitter.tweets.get_user_tweets_all(
                args.username, max_items=args.max_results
            ):
                tweets.append(_serialize_model(tweet))
            result = {"tweets": tweets, "count": len(tweets)}

        elif name == "search_twitter_tweets":
            args = SearchTweetsArgs(**arguments)
            tweets = []
            async for tweet in client.twitter.tweets.search_all(
                args.query, max_items=args.max_results
            ):
                tweets.append(_serialize_model(tweet))
            result = {"tweets": tweets, "count": len(tweets)}

        # Trend tools
        elif name == "get_twitter_trends":
            args = GetTrendsArgs(**arguments)
            from scrapebadger.twitter import TrendCategory

            category_map = {
                "news": TrendCategory.NEWS,
                "sports": TrendCategory.SPORTS,
                "entertainment": TrendCategory.ENTERTAINMENT,
            }
            category = category_map.get(args.category.lower()) if args.category else None
            if category:
                trends_response = await client.twitter.trends.get_trends(category=category)
            else:
                trends_response = await client.twitter.trends.get_trends()
            result = {
                "trends": [_serialize_model(t) for t in trends_response.data],
                "count": len(trends_response.data),
            }

        elif name == "get_twitter_place_trends":
            args = GetPlaceTrendsArgs(**arguments)
            place_trends = await client.twitter.trends.get_place_trends(args.woeid)
            result = _serialize_model(place_trends)

        # Geo tools
        elif name == "search_twitter_places":
            args = SearchPlacesArgs(**arguments)
            places_response = await client.twitter.geo.search(query=args.query)
            result = {
                "places": [_serialize_model(p) for p in places_response.data],
                "count": len(places_response.data),
            }

        # List tools
        elif name == "get_twitter_list_detail":
            args = GetListDetailArgs(**arguments)
            result = await client.twitter.lists.get_detail(args.list_id)

        elif name == "search_twitter_lists":
            args = SearchListsArgs(**arguments)
            lists_response = await client.twitter.lists.search(args.query)
            lists_data = lists_response.data[: args.max_results]
            result = {
                "lists": [_serialize_model(lst) for lst in lists_data],
                "count": len(lists_data),
            }

        elif name == "get_twitter_list_tweets":
            args = GetListTweetsArgs(**arguments)
            tweets = []
            async for tweet in client.twitter.lists.get_tweets_all(
                args.list_id, max_items=args.max_results
            ):
                tweets.append(_serialize_model(tweet))
            result = {"tweets": tweets, "count": len(tweets)}

        # Community tools
        elif name == "get_twitter_community_detail":
            args = GetCommunityDetailArgs(**arguments)
            result = await client.twitter.communities.get_detail(args.community_id)

        elif name == "search_twitter_communities":
            args = SearchCommunitiesArgs(**arguments)
            communities_response = await client.twitter.communities.search(args.query)
            result = {
                "communities": [_serialize_model(c) for c in communities_response.data],
                "count": len(communities_response.data),
            }

        # Google tools
        elif name == "search_google":
            args = SearchGoogleArgs(**arguments)
            result = await client.google.search.search(**args.model_dump(exclude_none=True))

        # Dedicated APIs: raw response dicts, every native field kept
        elif name == "autoscout24_get_listing":
            args = GetAutoscout24ListingArgs(**arguments)
            result = await client.autoscout24.get_listing(
                url=args.url, listing_id=args.listing_id, market=args.market
            )

        elif name == "github_get_repository":
            args = GetGitHubRepositoryArgs(**arguments)
            # The SDK percent-encodes owner and repo as separate path segments.
            result = await client.github.get_repository(args.owner, args.repo)

        elif name == "yelp_search_businesses":
            args = SearchYelpBusinessesArgs(**arguments)
            result = await client.yelp.search_businesses(
                location=args.location,
                query=args.query,
                market=args.market,
                category=args.category,
                sort_by=args.sort_by,
                price=args.price,
                features=args.features,
                page=args.page,
            )

        elif name == "facebook_marketplace_search":
            args = SearchMarketplaceArgs(**arguments)
            result = await client.facebook.search_marketplace(
                **args.model_dump(exclude_none=True, exclude={"no_cache"})
            )

        elif name == "facebook_marketplace_item":
            args = GetMarketplaceItemArgs(**arguments)
            result = await client.facebook.get_a_marketplace_item(args.item_id)

        elif name == "yelp_list_markets":
            ListYelpMarketsArgs(**arguments)
            result = await client.yelp.list_markets()

        else:
            return [
                TextContent(
                    type="text",
                    text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2),
                )
            ]

        # Serialize and return result
        serialized = _serialize_model(result) if result else {"data": None}
        return [TextContent(type="text", text=json.dumps(serialized, indent=2))]

    except ScrapeBadgerError as e:
        return CallToolResult(
            isError=True,
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                        indent=2,
                    ),
                )
            ],
        )
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    indent=2,
                ),
            )
        ]


async def serve() -> None:
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:
    """Main entry point."""
    try:
        # Verify API key is set before starting
        _get_api_key()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    asyncio.run(serve())


if __name__ == "__main__":
    main()
