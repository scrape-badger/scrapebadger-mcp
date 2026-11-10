# Changelog

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
