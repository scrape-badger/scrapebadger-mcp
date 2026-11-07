"""ScrapeBadger MCP Server.

This module implements the Model Context Protocol (MCP) server for ScrapeBadger,
providing AI agents with access to Twitter/X scraping and Google Search.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Annotated, Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field
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


class GetUserProfileArgs(BaseModel):
    """Arguments for getting a user profile."""

    username: str = Field(description="Twitter username (without @)")


class GetUserAboutArgs(BaseModel):
    """Arguments for getting extended user info."""

    username: str = Field(description="Twitter username (without @)")


class SearchUsersArgs(BaseModel):
    """Arguments for searching users."""

    query: str = Field(description="Search query string")
    max_results: int = Field(default=20, ge=1, le=100, description="Max results (1-100)")


class GetFollowersArgs(BaseModel):
    """Arguments for getting followers."""

    username: str = Field(description="Twitter username (without @)")
    max_results: int = Field(default=50, ge=1, le=200, description="Max results (1-200)")


class GetFollowingArgs(BaseModel):
    """Arguments for getting following."""

    username: str = Field(description="Twitter username (without @)")
    max_results: int = Field(default=50, ge=1, le=200, description="Max results (1-200)")


class GetTweetArgs(BaseModel):
    """Arguments for getting a tweet."""

    tweet_id: str = Field(description="Tweet ID")


class GetUserTweetsArgs(BaseModel):
    """Arguments for getting user tweets."""

    username: str = Field(description="Twitter username (without @)")
    max_results: int = Field(default=20, ge=1, le=100, description="Max results (1-100)")


class SearchTweetsArgs(BaseModel):
    """Arguments for searching tweets."""

    query: str = Field(description="Search query string")
    max_results: int = Field(default=20, ge=1, le=100, description="Max results (1-100)")


class GetTrendsArgs(BaseModel):
    """Arguments for getting trends."""

    category: str | None = Field(
        default=None,
        description="Trend category: 'news', 'sports', 'entertainment', or None for all",
    )


class GetPlaceTrendsArgs(BaseModel):
    """Arguments for getting place trends."""

    woeid: int = Field(description="Where On Earth ID (e.g., 23424977 for US, 44418 for London)")


class SearchPlacesArgs(BaseModel):
    """Arguments for searching places."""

    query: str = Field(description="Place name to search")


class GetListDetailArgs(BaseModel):
    """Arguments for getting list detail."""

    list_id: str = Field(description="Twitter list ID")


class SearchListsArgs(BaseModel):
    """Arguments for searching lists."""

    query: str = Field(description="Search query for lists")
    max_results: int = Field(default=20, ge=1, le=50, description="Max results (1-50)")


class GetListTweetsArgs(BaseModel):
    """Arguments for getting list tweets."""

    list_id: str = Field(description="Twitter list ID")
    max_results: int = Field(default=20, ge=1, le=100, description="Max results (1-100)")


class GetCommunityDetailArgs(BaseModel):
    """Arguments for getting community detail."""

    community_id: str = Field(description="Twitter community ID")


class SearchCommunitiesArgs(BaseModel):
    """Arguments for searching communities."""

    query: str = Field(description="Search query for communities")


class SearchGoogleArgs(BaseModel):
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
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        client = await _get_client()
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
            result = await client.google.search.search(
                args.q,
                gl=args.gl,
                hl=args.hl,
                start=args.start,
                location=args.location,
                ai_overview=args.ai_overview,
                expand_related_questions=args.expand_related_questions,
            )

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
