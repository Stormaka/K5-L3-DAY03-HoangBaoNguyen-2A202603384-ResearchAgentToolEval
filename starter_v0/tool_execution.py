"""Execution boundary shared by eval, CLI chat and the public UI."""
from __future__ import annotations

from typing import Any

from providers.base import ToolCall
from tools import TOOL_FUNCTIONS


def execute_tool_call(call: ToolCall) -> dict[str, Any]:
    # No model-controlled flag can authorize delivery. Keep it disabled until
    # the host implements user approval bound to an exact draft and recipient.
    if call.name == "send":
        result = {
            "error": "delivery_disabled",
            "status": "disabled",
            "message": "Gửi Telegram đang tắt. Chưa có tin nhắn nào được gửi.",
        }
        return {"tool": call.name, "args": call.args, "result": result}
    func = TOOL_FUNCTIONS.get(call.name)
    if not func:
        return {"tool": call.name, "args": call.args, "error": "unknown_tool",
                "result": {"error": "unknown_tool", "message": f"No local implementation for {call.name}"}}
    try:
        result = func(**call.args)
    except Exception as exc:
        result = {"error": type(exc).__name__, "message": str(exc)}
    return {"tool": call.name, "args": call.args, "result": result}
