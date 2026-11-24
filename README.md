<!-- mcp-name: io.github.scrape-badger/scrapebadger -->

<p align="center">
  <img src="https://scrapebadger.com/logo-dark.png" alt="ScrapeBadger" width="400">
</p>

<h1 align="center">ScrapeBadger MCP Server</h1>

<p align="center">
  <a href="https://pypi.org/project/scrapebadger-mcp/"><img src="https://img.shields.io/pypi/v/scrapebadger-mcp.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/scrapebadger-mcp/"><img src="https://img.shields.io/pypi/pyversions/scrapebadger-mcp.svg" alt="Python versions"></a>
  <a href="https://github.com/scrape-badger/scrapebadger-mcp/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/scrapebadger-mcp.svg" alt="License"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-Compatible-blue" alt="MCP Compatible"></a>
</p>

<p align="center">
  <strong>Give AI agents ScrapeBadger's scraping APIs through the Model Context Protocol: search engines, social media, e-commerce, real estate, AI answer engines and any web page.</strong>
</p>

---

## What is this?

[ScrapeBadger](https://scrapebadger.com) is a web scraping API. This repository is the official
[Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for it, so that Claude,
ChatGPT, Cursor, Windsurf, VS Code and other MCP clients can call ScrapeBadger as tools.

There are two ways to use it:

| | Hosted server | Local server (this package) |
|---|---|---|
| Where | `https://mcp.scrapebadger.com/mcp` | `uvx scrapebadger-mcp`, `pip install scrapebadger-mcp` or Docker |
| Transport | Streamable HTTP | stdio |
| Sign-in | OAuth with your ScrapeBadger account, or an API key | `SCRAPEBADGER_API_KEY` |
| Tools | Every ScrapeBadger API: 500+ tools across 40+ products | 31 tools: Twitter/X, Google, LinkedIn, Grok, Facebook Marketplace, Yelp, GitHub, AutoScout24 |
| Install | None | Python 3.10+ or Docker |

Both use the same credits as the REST API. Get an API key, or sign in with OAuth, at
[scrapebadger.com](https://scrapebadger.com/auth/signup?utm_source=mcp-readme&utm_medium=referral).

## Hosted server (recommended)

The hosted server at `https://mcp.scrapebadger.com/mcp` reaches every ScrapeBadger API,
including Twitter/X, Instagram, Facebook, LinkedIn, TikTok, YouTube, Reddit, Google (Search,
AI Mode, Maps, News, Shopping, Jobs, Hotels, Scholar and more), Bing, Yahoo, Baidu, DuckDuckGo,
Amazon, eBay, Walmart, Target, Etsy, AliExpress, Vinted, Zillow, Redfin, Idealista, ChatGPT,
Perplexity, Gemini, Copilot, Grok and the Web Scraping API for any URL. Nothing to install.

**Claude (claude.ai and Claude Desktop):** go to **Settings > Connectors > Add custom
connector**, enter `https://mcp.scrapebadger.com/mcp`, then sign in and approve. No API key
needed.

**Claude Code:**

```bash
claude mcp add --transport http scrapebadger https://mcp.scrapebadger.com/mcp
```

The first connection opens the ScrapeBadger sign-in in your browser (OAuth).

**Cursor and other clients that take a URL:** clients that support MCP OAuth sign in with
just the URL. Otherwise send your API key as a Bearer header (Windsurf names the URL field
`serverUrl`):

```json
{
  "mcpServers": {
    "scrapebadger": {
      "url": "https://mcp.scrapebadger.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

By default the hosted server lists a few free helper tools (`search_endpoints`,
`describe_endpoint`, `call_endpoint` and others) that reach every endpoint, which keeps your
agent's context small. Add `?apis=google,amazon` to the URL to list those APIs' tools
directly, or `?apis=all` for every tool. See the
[MCP docs](https://docs.scrapebadger.com/mcp/overview) and the
[client guides](https://docs.scrapebadger.com/mcp/integrations/claude-desktop).

## Local server (this package)

The local server runs on your machine over stdio and exposes the 31 tools listed under
[Available tools](#available-tools). It needs an API key from your
[ScrapeBadger dashboard](https://scrapebadger.com/dashboard/api-keys).

### Install

```bash
# Using uvx (recommended, nothing to install)
uvx scrapebadger-mcp

# Or with pip
pip install scrapebadger-mcp

# Or as a uv tool
uv tool install scrapebadger-mcp
```

### Configure your MCP client

Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS,
`%APPDATA%\Claude\claude_desktop_config.json` on Windows), Cursor (`.cursor/mcp.json`),
Windsurf and most other clients:

```json
{
  "mcpServers": {
    "scrapebadger": {
      "command": "uvx",
      "args": ["scrapebadger-mcp"],
      "env": {
        "SCRAPEBADGER_API_KEY": "sb_live_your_api_key_here"
      }
    }
  }
}
```

VS Code (`.vscode/mcp.json`) uses `servers` instead of `mcpServers`:

```json
{
  "servers": {
    "scrapebadger": {
      "type": "stdio",
      "command": "uvx",
      "args": ["scrapebadger-mcp"],
      "env": {
        "SCRAPEBADGER_API_KEY": "sb_live_your_api_key_here"
      }
    }
  }
}
```

Claude Code:

```bash
claude mcp add scrapebadger -e SCRAPEBADGER_API_KEY=sb_live_your_api_key_here -- uvx scrapebadger-mcp
```

### Docker

The [`Dockerfile`](Dockerfile) builds the server from this repository's source. Pass the API
key when you run the container; the image never contains it.

```bash
docker build -t scrapebadger-mcp .
docker run -i --rm -e SCRAPEBADGER_API_KEY=sb_live_your_api_key_here scrapebadger-mcp
```

`-i` keeps stdin open, which the stdio transport needs. To use the image from an MCP client:

```json
{
  "mcpServers": {
    "scrapebadger": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "SCRAPEBADGER_API_KEY", "scrapebadger-mcp"],
      "env": {
        "SCRAPEBADGER_API_KEY": "sb_live_your_api_key_here"
      }
    }
  }
}
```

### Try it

> "Get the profile and recent tweets of @sama"

> "Search Google for 'are noise cancelling headphones worth it' and answer the People Also Ask questions"

> "Ask Google AI Mode for the best coffee near me, as if I were in Wonju, South Korea"

> "Ask Grok what people on X say about the new iPhone, with sources"

> "Find pizza places in Toronto on Yelp, sorted by rating"

> "Show me used road bikes on Facebook Marketplace within 20 km of London, listed in the last two days"

---

## Available tools

The local server has 31 tools. It lists a tool only while ScrapeBadger's live endpoint catalog
lists its endpoint, and marks a deprecated or temporarily unavailable endpoint in the tool
description. A call to a restricted endpoint returns the API's error and is not billed.

### Twitter/X

| Tool | Description |
|------|-------------|
| `get_twitter_user_profile` | A user's profile by username: bio, followers, following, verification |
| `get_twitter_user_about` | Extended "About" info: account location, username history, verification details |
| `search_twitter_users` | Search users by query |
| `get_twitter_followers` | A user's followers |
| `get_twitter_following` | Accounts a user follows |
| `get_twitter_tweet` | A single tweet by ID: text, author, metrics, media, polls, quoted tweet |
| `get_twitter_user_tweets` | A user's recent tweets |
| `search_twitter_tweets` | Search tweets, with Twitter's advanced search operators |
| `get_twitter_trends` | Trending topics, optionally by category (news, sports, entertainment) |
| `get_twitter_place_trends` | Trends for a location by WOEID |
| `search_twitter_places` | Search Twitter places by name |
| `get_twitter_list_detail` | A list's name, description, member and subscriber counts, owner |
| `search_twitter_lists` | Search lists |
| `get_twitter_list_tweets` | Recent tweets from a list's members |
| `get_twitter_community_detail` | A community's name, description, member count, rules and admins |
| `search_twitter_communities` | Search communities |

### Google

| Tool | Description |
|------|-------------|
| `search_google` | Google web search (`/v1/google/search`): organic results, ads, knowledge graph, AI Overview, People Also Ask, shopping results, perspectives, discussions and forums, short videos, related searches |
| `google_ai_mode_search` | Google AI Mode (`/v1/google/ai-mode/search`): the generative answer as `markdown` and `text_blocks` with its cited `references`, optionally localised with `location`, `lat` + `lon` or `uule` |
| `google_resolve_links` | Real URLs for Google results (`POST /v1/google/resolve`): send the `search_google` organic results that carry a `link_token`, 1 to 25 per call, and get each row back resolved, not ready or failed. No credits |

`search_google` takes `q`, `gl`, `hl`, `start`, `location`, `ai_overview` and
`expand_related_questions`, plus Google's own request parameters. Google loads a People Also
Ask answer only when the question is clicked, so by default `related_questions` holds the
questions without answers. `expand_related_questions: true` opens every question the page
shows (usually four) and a number `N` opens the first N; each answered question then carries
`text_blocks` and `references`. Each answered question costs one more search
(credits = 20 x (1 + answered)), and a question whose answer does not come back is not billed.
See the [Google web search docs](https://docs.scrapebadger.com/api-reference/google/google-search/google-web-search).

Google can return a result's `link` as a redirect (`https://www.google.com/goto?url=...`) and
paces how fast the links of one result page can be followed. Such an organic result carries
`link_token` and `retry_after_seconds` (0 = can be resolved right away); both are null when
`link` is already the real URL. Pass the results that carry a `link_token` to
`google_resolve_links`, 1 to 25 per call. Other fields are returned unchanged and the rows come
back in the order sent, each as one of:

- resolved: `link` is the result's own URL and the row has no `link_token`.
- not ready: the row has `link_token` and `retry_after_seconds` (1 or more). Wait that many
  seconds, then send the row again with its latest `link_token`, which can differ from the one
  sent.
- failed: the row has `link_token` and `error`. Do not send it again.

A token sent early is not an error: the row comes back not ready with the wait that is left.
The response's own `retry_after_seconds` is the shortest wait among the not-ready rows, or
null when no row is waiting. One call makes one request and does not wait. Polling this way,
all ten links of a page are usually known 45 to 70 seconds after the search; once the result
page is about 160 seconds old, one call returns every remaining link.

`google_ai_mode_search` takes `q`, `gl`, `hl`, `include_html` (default `false` here:
`markdown` and `text_blocks` carry the whole answer) and one of `location`, `uule`, or
`lat` + `lon`. A location answers "near me" and other local questions as if the user were in
that place, down to the city or district, whatever the exit IP: `location` is a Google
canonical name such as `Wonju-si,Gangwon-do,South Korea`, a criteria ID such as `1009889`, or
an unambiguous short name. With `location` and no `gl`, `gl` becomes the location's country;
`gl` itself is Google's market and does not choose the exit country. Located answers echo a
`location` object. Unknown or ambiguous names are rejected with canonical candidates, and a
located request that cannot be answered right now fails unbilled; retry it. See the
[Google AI Mode docs](https://docs.scrapebadger.com/api-reference/google/google-ai-mode/google-ai-mode-search).

### LinkedIn

| Tool | Description |
|------|-------------|
| `linkedin_get_profile` | A public LinkedIn profile by vanity id (`public_id`): roles, education, public profile sections, recent posts and articles when LinkedIn shows them |
| `linkedin_get_full_profile` | The full profile with paginated positions and richer sections |

Both take `public_id` (the part after `linkedin.com/in/`) and an optional `country`
(default `us`). See the [LinkedIn docs](https://docs.scrapebadger.com/linkedin/overview).

### Grok

| Tool | Description |
|------|-------------|
| `grok_ask` | Ask the real Grok assistant: the answer with web citations, X post references, tool usage and follow-up suggestions. Pass an earlier `conversation_id` to continue a conversation; `mode` is `auto`, `fast` or `expert`, `web_search` is `auto`, `force` or `off`. 20 credits |
| `grok_brand_visibility` | Measure a brand in a real Grok answer: mentions, share of voice, position, competitor breakdown and citation rank, with the full answer and sources. 25 credits |
| `grok_get_conversation` | The messages of an existing Grok conversation, oldest first, with timestamps. 3 credits |
| `grok_list_models` | Grok's assistant modes (`auto`, `fast`, `expert`). 1 credit |

See the [Grok docs](https://docs.scrapebadger.com/grok/overview).

### Facebook Marketplace

| Tool | Description |
|------|-------------|
| `facebook_marketplace_search` | Search public Marketplace listings without a Facebook account. Verified filters enforce radius in kilometres and listing age; `include_details=true` adds full descriptions and photo URLs |
| `facebook_marketplace_item` | One public listing: description, photo URLs, seller and approximate coordinates |

Follow the opaque `end_cursor`, including after empty filtered pages. Coverage is partial and
newest-first order applies within each page. See the
[Facebook docs](https://docs.scrapebadger.com/facebook/overview).

### Yelp, GitHub and AutoScout24

| Tool | Description |
|------|-------------|
| `yelp_search_businesses` | Yelp business search (`/v1/yelp/search`) for a `location` in the US (`market=us`, default) or Canada (`ca`): rating, review count, categories, price, address and opening hours, ads in a separate `ads` list. Filters: `query`, `category`, `sort_by`, `price`, `features`. Ten per page, `page` 1-11. 15 credits per page with results; empty searches and errors are free |
| `yelp_list_markets` | The Yelp sites this API searches (`/v1/yelp/markets`). Free |
| `github_get_repository` | A public repository on its default branch (`/v1/github/repositories/{owner}/{repo}`): statistics, topics, license, native README, root files and latest commit. Pass `owner` and `repo` separately, not a URL. 10 credits |
| `autoscout24_get_listing` | Full AutoScout24 listing detail (`/v1/autoscout24/listing`): native specifications, equipment, photos, prices and public seller data. Pass exactly one `url` or `listing_id` from a vehicle search; `market` is inferred from the URL, otherwise `de`. 10 credits; removed listings are unbilled 404s |

These tools return the API response unchanged, so every native field stays available. See the
[Yelp](https://docs.scrapebadger.com/yelp/overview),
[GitHub](https://docs.scrapebadger.com/github/repositories) and
[AutoScout24](https://docs.scrapebadger.com/api-reference/endpoint/autoscout24/listing) docs.

For any other ScrapeBadger API (Amazon, Instagram, YouTube, TikTok, Reddit, ChatGPT,
Perplexity, the Web Scraping API and the rest), use the [hosted server](#hosted-server-recommended).

---

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `SCRAPEBADGER_API_KEY` | For tool calls | Your ScrapeBadger API key, from the [dashboard](https://scrapebadger.com/dashboard/api-keys) |

The server starts and lists its tools without a key, so MCP clients and directories can
inspect it. Until the key is set, every tool call returns an error (`MissingApiKeyError`) that
says how to set it.

To run from a checkout without installing:

```bash
export SCRAPEBADGER_API_KEY="sb_live_your_key_here"
uv run scrapebadger-mcp
```

---

## Error handling

Tool errors come back as MCP tool errors with an `error` message and an `error_type`:

| Error | Meaning | What to do |
|-------|---------|------------|
| `MissingApiKeyError` | `SCRAPEBADGER_API_KEY` is not set | Set it in the server's environment and restart the server |
| `AuthenticationError` | Invalid API key | Check your `SCRAPEBADGER_API_KEY` |
| `RateLimitError` | Too many requests | Wait and retry, or upgrade your plan |
| `InsufficientCreditsError` | Out of credits | Buy more at [scrapebadger.com](https://scrapebadger.com) |
| `NotFoundError` | User, tweet or listing not found | Check the username, ID or URL |

---

## Development

```bash
git clone https://github.com/scrape-badger/scrapebadger-mcp.git
cd scrapebadger-mcp
uv sync --extra dev

uv run pytest                      # tests
uv run ruff check src/ tests/      # lint
uv run ruff format src/ tests/     # format
uv run mypy src/                   # type check
```

---

## Troubleshooting

### "SCRAPEBADGER_API_KEY is not set"

Add the key to the server entry in your MCP client config and restart the client:

```json
{
  "env": {
    "SCRAPEBADGER_API_KEY": "sb_live_your_key_here"
  }
}
```

With Docker, pass `-e SCRAPEBADGER_API_KEY=...` to `docker run`.

### Server not showing in Claude Desktop

1. Restart Claude Desktop after changing the config.
2. Check that the config file path is right for your OS.
3. Check that the JSON is valid (no trailing commas).

### "uvx: command not found"

Install `uv` first:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Rate limit errors

ScrapeBadger has usage limits based on your plan. If you hit them, send fewer requests, use
smaller `max_results`, or upgrade your plan at [scrapebadger.com](https://scrapebadger.com).

---

## Related projects

- [ScrapeBadger Python SDK](https://github.com/scrape-badger/scrapebadger-python)
- [ScrapeBadger Node.js SDK](https://github.com/scrape-badger/scrapebadger-node)
- [ScrapeBadger API docs](https://docs.scrapebadger.com)

## Support

- **Documentation:** [docs.scrapebadger.com](https://docs.scrapebadger.com)
- **Issues:** [GitHub Issues](https://github.com/scrape-badger/scrapebadger-mcp/issues)
- **Email:** support@scrapebadger.com
- **Discord:** [Join our community](https://discord.gg/scrapebadger)

## License

MIT License. See [LICENSE](LICENSE).

---

<p align="center">
  Made with love by <a href="https://scrapebadger.com">ScrapeBadger</a>
</p>
