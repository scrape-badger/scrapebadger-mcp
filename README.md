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
  <strong>Give your AI agents access to Twitter/X data, Google Search, Yelp businesses, GitHub repositories and AutoScout24 listings via the Model Context Protocol</strong>
</p>

---

## What is this?

ScrapeBadger MCP Server is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that enables AI assistants like **Claude**, **ChatGPT**, **Cursor**, **Windsurf**, and other MCP-compatible clients to access Twitter/X data, Google Search results, Yelp business search, GitHub repository detail and AutoScout24 listing detail through the [ScrapeBadger API](https://scrapebadger.com).

**With this MCP server, your AI can:**

- Get Twitter user profiles, followers, and following lists
- Search and retrieve tweets
- Access trending topics globally or by location
- Explore Twitter lists and communities
- Search for places and geolocated content
- Search Google and read the structured results page, including People Also Ask answers
- Ask Google AI Mode, optionally as if the user were in a given city or district
- Search Yelp businesses in the US and Canada in Yelp's own order, with ads kept separate
- Read a public GitHub repository: README, root files, latest commit and statistics
- Read a full AutoScout24 vehicle listing: specifications, equipment, photos and seller data

## Quick Start

### 1. Get Your API Key

Sign up at [scrapebadger.com](https://scrapebadger.com/auth/signup?utm_source=mcp-readme&utm_medium=referral) and get your API key.

### 2. Install

```bash
# Using uvx (recommended - no installation needed)
uvx scrapebadger-mcp

# Or install globally with pip
pip install scrapebadger-mcp

# Or with uv
uv tool install scrapebadger-mcp
```

### 3. Configure Your AI Client

#### Claude Desktop

Add to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

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

#### Cursor

Add to your Cursor MCP settings (`.cursor/mcp.json`):

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

#### Windsurf

Add to your Windsurf MCP configuration:

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

#### VS Code with Copilot

Add to your VS Code settings (`.vscode/mcp.json`):

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

### 4. Start Using It!

Once configured, simply ask your AI to fetch Twitter data:

> "Get the profile of @elonmusk"

> "Search for tweets about AI agents"

> "What's trending on Twitter right now?"

> "Find the top 10 Python developers on Twitter"

> "Search Google for 'are noise cancelling headphones worth it' and answer the People Also Ask questions"

> "Ask Google AI Mode for the best coffee near me, as if I were in Wonju, South Korea"

---

## Available Tools

The MCP server provides 17 tools organized into categories:

### User Tools

| Tool | Description |
|------|-------------|
| `get_twitter_user_profile` | Get a user's profile by username (bio, followers, following, etc.) |
| `get_twitter_user_about` | Get extended "About" info (account location, username history) |
| `search_twitter_users` | Search for users by query |
| `get_twitter_followers` | Get a user's followers |
| `get_twitter_following` | Get accounts a user follows |

### Tweet Tools

| Tool | Description |
|------|-------------|
| `get_twitter_tweet` | Get a single tweet by ID |
| `get_twitter_user_tweets` | Get recent tweets from a user |
| `search_twitter_tweets` | Search for tweets (supports Twitter search operators) |

### Trend Tools

| Tool | Description |
|------|-------------|
| `get_twitter_trends` | Get global trending topics (optionally by category) |
| `get_twitter_place_trends` | Get trends for a specific location (by WOEID) |

### Geo Tools

| Tool | Description |
|------|-------------|
| `search_twitter_places` | Search for Twitter places by name |

### List Tools

| Tool | Description |
|------|-------------|
| `get_twitter_list_detail` | Get details about a Twitter list |
| `search_twitter_lists` | Search for Twitter lists |
| `get_twitter_list_tweets` | Get tweets from a list |

### Community Tools

| Tool | Description |
|------|-------------|
| `get_twitter_community_detail` | Get details about a Twitter community |
| `search_twitter_communities` | Search for communities |

### Google Tools

| Tool | Description |
|------|-------------|
| `search_google` | Search Google (`/v1/google/search`): organic results, ads, knowledge graph, AI Overview, People Also Ask, shopping results, perspectives, discussions and forums, short videos, related searches |
| `google_ai_mode_search` | Google AI Mode (`/v1/google/ai-mode/search`): the generative answer as `markdown` and `text_blocks` with its cited `references`, optionally localised with `location`, `lat` + `lon` or `uule` |

`search_google` takes `q`, `gl`, `hl`, `start`, `location`, `ai_overview` and
`expand_related_questions`. Google loads a People Also Ask answer only when the
question is clicked, so by default `related_questions` holds the questions
without answers. `expand_related_questions: true` opens every question the page
shows (usually four) and a number `N` opens the first N; each answered question
then carries `text_blocks` and `references`. Each answered question costs one
more search (credits = 20 x (1 + answered)), and a question whose answer does
not come back is not billed. See the
[Google web search docs](https://docs.scrapebadger.com/api-reference/google/google-search/google-web-search).

`google_ai_mode_search` takes `q`, `gl`, `hl`, `include_html` (default `false`
here: `markdown` and `text_blocks` carry the whole answer) and one of `location`,
`uule`, or `lat` + `lon`. A location answers "near me" and other local questions
as if the user were in that place, down to the city or district, whatever the
exit IP: `location` is a Google canonical name such as
`Wonju-si,Gangwon-do,South Korea`, a criteria ID such as `1009889`, or an
unambiguous short name. With `location` and no `gl`, `gl` becomes the location's
country; `gl` itself is Google's market and does not choose the exit country.
Located answers echo a `location` object. Unknown or ambiguous names are
rejected with canonical candidates, and a located request that cannot be
answered right now fails unbilled; retry it. Location targeting needs
`scrapebadger` SDK 0.77.0 or later. See the
[Google AI Mode docs](https://docs.scrapebadger.com/api-reference/google/google-ai-mode/google-ai-mode-search).

### Yelp, GitHub repository and AutoScout24 listing tools

| Tool | Description |
|------|-------------|
| `yelp_search_businesses` | Yelp business search (`/v1/yelp/search`) for a `location` in the US (`market=us`, default) or Canada (`ca`): rating, review count, categories, price, address and opening hours, ads in a separate `ads` list. Filters: `query`, `category`, `sort_by`, `price`, `features`. Ten per page, `page` 1-11. 15 credits per page with results; empty searches and errors are free |
| `yelp_list_markets` | The Yelp sites this API searches (`/v1/yelp/markets`). Free |
| `github_get_repository` | A public repository on its default branch (`/v1/github/repositories/{owner}/{repo}`): statistics, topics, license, native README, root files and latest commit. Pass `owner` and `repo` separately, not a URL. 10 credits |
| `autoscout24_get_listing` | Full AutoScout24 listing detail (`/v1/autoscout24/listing`): native specifications, equipment, photos, prices and public seller data. Pass exactly one `url` or `listing_id` from a vehicle search; `market` is inferred from the URL, otherwise `de`. 10 credits; removed listings are unbilled 404s |

These tools return the API response unchanged, so every native field stays available.
See the [Yelp](https://docs.scrapebadger.com/yelp/overview),
[GitHub](https://docs.scrapebadger.com/github/repositories) and
[AutoScout24](https://docs.scrapebadger.com/api-reference/endpoint/autoscout24/listing) docs.

The server lists a tool only while ScrapeBadger's live endpoint catalog lists its endpoint,
and marks a deprecated or temporarily unavailable endpoint in the tool description. A call to
a restricted endpoint returns the API's error and is not billed.

---

## Example Conversations

### Research a Twitter Account

**You:** Get the profile and recent tweets from @sama

**Claude:** I'll fetch Sam Altman's Twitter profile and recent tweets.

*Uses `get_twitter_user_profile` and `get_twitter_user_tweets`*

```
Sam Altman (@sama)
- 3.2M followers, 1,847 following
- Bio: "ceo of openai"
- Joined: December 2008

Recent tweets:
1. "excited to share..." (245K likes)
2. "the future of ai..." (180K likes)
...
```

### Monitor Trending Topics

**You:** What's trending in tech on Twitter today?

**Claude:** I'll check the current trending topics.

*Uses `get_twitter_trends` with category="news"*

```
Top Tech Trends:
1. #GPT5 - 125,000 tweets
2. Apple Vision Pro - 89,000 tweets
3. #AGI - 45,000 tweets
...
```

### Competitive Analysis

**You:** Compare the Twitter engagement of Stripe, Square, and PayPal

**Claude:** I'll gather data on all three companies' Twitter profiles.

*Uses `get_twitter_user_profile` for each company*

```
| Company | Followers | Following | Engagement Rate |
|---------|-----------|-----------|-----------------|
| Stripe  | 892K      | 1,245     | 2.3%           |
| Square  | 1.2M      | 567       | 1.8%           |
| PayPal  | 2.1M      | 234       | 0.9%           |
```

---

## Configuration Options

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SCRAPEBADGER_API_KEY` | Yes | Your ScrapeBadger API key |

### Using with Docker

```dockerfile
FROM python:3.12-slim

RUN pip install scrapebadger-mcp

ENV SCRAPEBADGER_API_KEY=your_key_here

CMD ["scrapebadger-mcp"]
```

### Using with Python Directly

```bash
# Set your API key
export SCRAPEBADGER_API_KEY="sb_live_your_key_here"

# Run the server
python -m scrapebadger_mcp.server
```

---

## Error Handling

The MCP server handles common errors gracefully:

| Error | Description | Solution |
|-------|-------------|----------|
| `AuthenticationError` | Invalid API key | Check your `SCRAPEBADGER_API_KEY` |
| `RateLimitError` | Too many requests | Wait and retry, or upgrade your plan |
| `InsufficientCreditsError` | Out of credits | Purchase more at scrapebadger.com |
| `NotFoundError` | User/tweet not found | Verify the username or tweet ID |

---

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/scrape-badger/scrapebadger-mcp.git
cd scrapebadger-mcp

# Install dependencies
uv sync --dev

# Set your API key
export SCRAPEBADGER_API_KEY="sb_live_your_key_here"
```

### Running Locally

```bash
# Run the MCP server directly
uv run python -m scrapebadger_mcp.server

# Or use the CLI
uv run scrapebadger-mcp
```

### Testing

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/scrapebadger_mcp
```

### Code Quality

```bash
# Lint
uv run ruff check src/

# Format
uv run ruff format src/

# Type check
uv run mypy src/
```

---

## Troubleshooting

### "SCRAPEBADGER_API_KEY environment variable is required"

Make sure you've set the API key in your MCP configuration:

```json
{
  "env": {
    "SCRAPEBADGER_API_KEY": "sb_live_your_key_here"
  }
}
```

### Server not showing in Claude Desktop

1. Restart Claude Desktop after changing the config
2. Check the config file path is correct for your OS
3. Verify JSON syntax is valid (no trailing commas)

### "uvx: command not found"

Install `uv` first:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Rate limit errors

ScrapeBadger has usage limits based on your plan. If you're hitting limits:

1. Reduce request frequency
2. Use pagination with smaller `max_results`
3. Upgrade your plan at [scrapebadger.com](https://scrapebadger.com)

---

## Related Projects

- [ScrapeBadger Python SDK](https://github.com/scrape-badger/scrapebadger-python) - Official Python SDK
- [ScrapeBadger Node.js SDK](https://github.com/scrape-badger/scrapebadger-node) - Official Node.js SDK
- [ScrapeBadger API Docs](https://docs.scrapebadger.com) - Full API documentation

---

## Support

- **Documentation:** [docs.scrapebadger.com](https://docs.scrapebadger.com)
- **Issues:** [GitHub Issues](https://github.com/scrape-badger/scrapebadger-mcp/issues)
- **Email:** support@scrapebadger.com
- **Discord:** [Join our community](https://discord.gg/scrapebadger)

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  Made with love by <a href="https://scrapebadger.com">ScrapeBadger</a>
</p>

### Public Facebook Marketplace

`facebook_marketplace_search` reads public listings without a Facebook account.
Verified filters enforce radius in kilometres and age. Set `include_details=true`
for full public descriptions and photo URLs. Follow the opaque `end_cursor`,
including after empty filtered pages; coverage is partial and newest-first order
applies within each page. `facebook_marketplace_item` reads one listing.
