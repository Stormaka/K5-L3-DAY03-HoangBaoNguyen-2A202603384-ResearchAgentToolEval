---
name: fetch
track: core
kind: live_api
provider: Firecrawl
requires_env: [FIRECRAWL_API_KEY]
inputs: [url]
outputs: [items]
side_effect: false
---
# fetch

Reads the content of a single URL via Firecrawl.

Keyless demo fallback: with `KEYLESS_FALLBACKS=1` and no `FIRECRAWL_API_KEY`,
the URL is fetched directly and stripped to plain text (`fallback: direct_get`);
script/style blocks are removed and text is capped at 4000 chars.
