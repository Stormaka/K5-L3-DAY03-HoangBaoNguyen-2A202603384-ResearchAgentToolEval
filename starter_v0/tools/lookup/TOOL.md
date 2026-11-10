---
name: lookup
track: core
kind: live_api
provider: Tavily
requires_env: [TAVILY_API_KEY]
inputs: [query, topic, timeframe, max_results]
outputs: [items]
side_effect: false
---
# lookup

Searches the web via Tavily. Has a `topic` (`general` or `news`) and a
`timeframe` argument.

Keyless demo fallback: with `KEYLESS_FALLBACKS=1` and no `TAVILY_API_KEY`,
`topic="news"` queries are served by Google News RSS (`fallback: google_news_rss`
in the result); `topic="general"` still requires the key.
