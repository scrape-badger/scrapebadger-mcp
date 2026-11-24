# ScrapeBadger MCP server (stdio), built from this repository's source.
#
#   docker build -t scrapebadger-mcp .
#   docker run -i --rm -e SCRAPEBADGER_API_KEY=sb_live_... scrapebadger-mcp
#
# The API key is passed at run time and never stored in the image. Without it the server
# still starts and lists its tools; each tool call then returns an error that says how to
# set the key.

FROM python:3.12-slim AS build

COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Dependencies first, pinned by uv.lock, so source edits do not reinstall them.
COPY pyproject.toml uv.lock README.md LICENSE ./
RUN uv sync --locked --no-dev --no-install-project

COPY src ./src
RUN uv sync --locked --no-dev --no-editable


FROM python:3.12-slim

LABEL org.opencontainers.image.title="ScrapeBadger MCP server" \
      org.opencontainers.image.description="MCP server for ScrapeBadger: Twitter/X, Google, LinkedIn, Grok, Facebook Marketplace, Yelp, GitHub and AutoScout24 tools for AI agents" \
      org.opencontainers.image.source="https://github.com/scrape-badger/scrapebadger-mcp" \
      org.opencontainers.image.url="https://scrapebadger.com" \
      org.opencontainers.image.licenses="MIT" \
      io.modelcontextprotocol.server.name="io.github.scrape-badger/scrapebadger"

RUN useradd --create-home --uid 10001 mcp

COPY --from=build /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER mcp

# MCP over stdio: run with `docker run -i` so the client can write to stdin.
ENTRYPOINT ["scrapebadger-mcp"]
