# Changelog

## [0.7.0] - 2026-11-09

- Every tool that costs credits takes `no_cache` (default `false`). It skips the API's 60-second duplicate-request cache and fetches a fresh result, billed as a normal call. The server sends `Cache-Control: no-cache` through `ScrapeBadger.with_options(no_cache=True)`. On `search_google`, `no_cache` also still goes as the existing query parameter. `yelp_list_markets` is free and does not take it. Requires ScrapeBadger SDK 0.77.0. (SCR-396)

## [0.6.1] - 2026-11-08

- Add verified account-free Facebook Marketplace filters, public continuations and detail enrichment.

## 0.6.0 — 2026-11-07

- Expose Google Search `oq`, `sourceid` and `ie`, including explicit empty values. Requires ScrapeBadger SDK 0.76.0.
