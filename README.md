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
  <strong>Give your AI agents access to Twitter/X data via the Model Context Protocol</strong>
</p>

---

## What is this?

ScrapeBadger MCP Server is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that enables AI assistants like **Claude**, **ChatGPT**, **Cursor**, **Windsurf**, and other MCP-compatible clients to access Twitter/X data through the [ScrapeBadger API](https://scrapebadger.com).

**With this MCP server, your AI can:**

- Get Twitter user profiles, followers, and following lists
- Search and retrieve tweets
- Access trending topics globally or by location
- Explore Twitter lists and communities
- Search for places and geolocated content

## Quick Start

### 1. Get Your API Key

Sign up at [scrapebadger.com](https://scrapebadger.com) and get your API key.

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
