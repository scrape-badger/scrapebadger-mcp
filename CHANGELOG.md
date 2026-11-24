# Changelog

## [0.10.1] - 2026-11-24

- The server starts and lists its tools without `SCRAPEBADGER_API_KEY`, so MCP clients and directories can inspect it before a key is set. Without a key the tool list does not read the live endpoint catalog, and every tool call returns an MCP error (`MissingApiKeyError`) that says how to set the key. Before, the server exited with code 1 at startup.
- New `Dockerfile` that builds the server from this repository's source with the locked dependencies (`uv.lock`) and runs it over stdio as a non-root user. The API key is passed at run time (`docker run -i --rm -e SCRAPEBADGER_API_KEY=... scrapebadger-mcp`) and is not stored in the image. CI builds the image and lists its tools without a key.
- README: leads with the hosted server at `https://mcp.scrapebadger.com/mcp` (OAuth or API key, every ScrapeBadger API), then the local install and Docker. The tool list now covers all 31 tools, including LinkedIn and Grok.
- `server.json` and package metadata describe every product the package covers. `uv.lock` matches `pyproject.toml` again (it still locked `scrapebadger` 0.78.0). (SCR-653)

## [0.10.0] - 2026-11-23

- New `google_resolve_links` tool (`POST /v1/google/resolve`, no credits): get the real URLs of `search_google` organic results whose `link` is a `google.com/goto` redirect. Send the results that carry a `link_token`, 1 to 25 per call; other fields are returned unchanged. Each row comes back resolved (`link` is the result's own URL; no `link_token`), not ready (`link_token` and `retry_after_seconds` of 1 or more: wait that long, then send the row's latest `link_token` again) or failed (`link_token` and `error`: do not send it again). One call makes one request and does not wait.
- The `search_google` description now says that such results carry `link_token` and `retry_after_seconds`.
- Tool listing matches each tool against the live endpoint catalog by HTTP method and path, so a tool on a POST-only endpoint can be listed. The other tools are matched on their GET rows, as before.
- Requires ScrapeBadger Python SDK 0.82.0 (`scrapebadger>=0.82.0`). (SCR-667)

## [0.9.0] - 2026-11-14

- Add four Grok tools: `grok_ask`, `grok_brand_visibility`, `grok_get_conversation`, and `grok_list_models`, with web citations, X post references, multi-turn conversations, and brand analysis. Requires ScrapeBadger Python SDK 0.79.0. (SCR-623)

## [0.7.0] - 2026-11-10

- New `google_ai_mode_search` tool for Google AI Mode (`/v1/google/ai-mode/search`): the generative answer as `markdown` and `text_blocks` with cited `references`. `include_html` defaults to `false` here to keep the raw `answer_html` out of the agent's context.
- Location targeting: pass one of `location` (a Google canonical name such as `Wonju-si,Gangwon-do,South Korea`, a criteria ID such as `1009889`, or an unambiguous short name), `uule` (`w+`/`j+`) or `lat` + `lon`, and AI Mode answers "near me" and local questions as if the user were in that city or district, whatever the exit IP. With `location` and no `gl`, the API uses the location's country. More than one targeting method, `lat` without `lon` and out-of-range coordinates are rejected before the call. Located answers echo a `location` object. (SCR-610)
- Requires ScrapeBadger SDK 0.77.0 (`scrapebadger>=0.77.0`) for the location parameters.

## [0.6.2] - 2026-11-09

- Tool descriptions no longer mention cached or free repeat responses: ScrapeBadger no longer caches or stores results, so every call is fetched fresh and billed. `search_google`'s `no_cache` is kept for compatibility and has no effect.

## [0.6.1] - 2026-11-08

- Add verified account-free Facebook Marketplace filters, public continuations and detail enrichment.

## 0.6.0 — 2026-11-07

- Expose Google Search `oq`, `sourceid` and `ie`, including explicit empty values. Requires ScrapeBadger SDK 0.76.0.
