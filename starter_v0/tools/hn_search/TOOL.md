---
name: hn_search
track: bonus
kind: live_api
requires_env: []
inputs: [query, tags, limit]
outputs: [total_hits, items]
provider: Algolia HN API
side_effect: false
---
# hn_search

Tìm thảo luận / tin trên Hacker News theo từ khóa qua Algolia HN API.
`tags` mặc định `story`; hit không có url riêng (Ask HN) thì dùng link item HN.
Không cần API key.
