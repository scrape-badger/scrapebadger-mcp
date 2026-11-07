"""ScrapeBadger MCP Server.

Model Context Protocol (MCP) server for ScrapeBadger, enabling AI agents
like Claude, ChatGPT, and Cursor to access Twitter/X data, Google Search, AutoScout24
listing detail, GitHub repository detail and Yelp business search.

Example:
    Configure in Claude Desktop's config:

    ```json
    {
        "mcpServers": {
            "scrapebadger": {
                "command": "uvx",
                "args": ["scrapebadger-mcp"],
                "env": {
                    "SCRAPEBADGER_API_KEY": "sb_live_your_key_here"
                }
            }
        }
    }
    ```
"""

from scrapebadger_mcp.server import main, serve

__version__ = "0.5.0"

__all__ = ["__version__", "main", "serve"]
