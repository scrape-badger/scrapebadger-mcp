# Changelog

## [0.6.2] - 2026-11-09

- Tool descriptions no longer mention cached or free repeat responses: ScrapeBadger no longer caches or stores results, so every call is fetched fresh and billed. `search_google`'s `no_cache` is kept for compatibility and has no effect.

## [0.6.1] - 2026-11-08

- Add verified account-free Facebook Marketplace filters, public continuations and detail enrichment.

## 0.6.0 — 2026-11-07

- Expose Google Search `oq`, `sourceid` and `ie`, including explicit empty values. Requires ScrapeBadger SDK 0.76.0.
