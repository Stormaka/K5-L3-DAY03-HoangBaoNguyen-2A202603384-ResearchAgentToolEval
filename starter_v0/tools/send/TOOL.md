---
name: send
track: bonus
kind: action
provider: Telegram Bot API
requires_env: [TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]
inputs: [text, confirmed]
outputs: [status]
side_effect: true
---
# send

Low-level Telegram transport, retained for offline unit tests. `confirmed` is a
caller-provided argument, not evidence of user approval. Model-driven execution
is disabled by `tool_execution.py` in eval, CLI chat and the public UI. The public
UI also removes `send` from model tool declarations. No Telegram bonus is claimed
until an exact-draft approval flow and a real delivery receipt are demonstrated.
