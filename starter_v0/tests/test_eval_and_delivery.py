"""Regression tests for false-positive refusals and model-controlled delivery."""
from __future__ import annotations

import json
import io
import sys
from pathlib import Path

import pytest

from agent import ResearchAgent
from chat import run_model_tool_loop
from providers.base import ModelResponse, ToolCall
from run_eval import REFUSAL_TEXT, evaluate_phase_b, evaluate_tool_execution, summarize
from tools import TOOL_FUNCTIONS


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("suite,case_id", [
    ("base", "R08_out_of_scope"), ("base", "R14_out_of_scope_coding"),
    ("group", "G05_out_of_scope_translation"),
])
def test_historical_v4_solutions_are_not_refusals(suite, case_id):
    path = next((ROOT / "runs").glob(f"v4_B_{suite}_*.json"))
    item = next(x for x in json.loads(path.read_text(encoding="utf-8"))["results"] if x["id"] == case_id)
    case = {**item, "failure_type": item["result"]["case_failure_type"]}
    result = evaluate_phase_b(case, [], item["result"]["actual_text"])
    assert result["routing_correct"] is True
    assert result["passed"] is False
    assert result["observed_mismatch"] == "wrong_response_content"


@pytest.mark.parametrize("text,passed", [
    (REFUSAL_TEXT, True), ("  " + REFUSAL_TEXT + "\n", True),
    (None, False), ("", False), ("Không có tool.", False),
    (REFUSAL_TEXT + " Nguyên hàm là x³/3+C.", False),
    (REFUSAL_TEXT + "\n```python\ndef fibonacci(n): return n\n```", False),
])
def test_refusal_checks_content_and_rejects_appended_answers(text, passed):
    case = {"failure_type": "out_of_scope", "expect": {"no_tool": True, "behavior": "refuse"}}
    assert evaluate_phase_b(case, [], text)["passed"] is passed


def test_capability_answer_cannot_be_blank_or_scope_refusal():
    case = {"failure_type": "unnecessary_tool", "expect": {"no_tool": True, "behavior": "answer_without_tool"}}
    assert evaluate_phase_b(case, [], "Mình giúp tìm tin tức và tóm tắt nguồn.")["passed"]
    assert not evaluate_phase_b(case, [], "")["passed"]
    assert not evaluate_phase_b(case, [], REFUSAL_TEXT)["passed"]


def test_execution_failure_is_reported_separately_from_routing():
    calls = [{"name": "papers", "args": {"query": "LLM"}}]
    case = {"phase": "B", "failure_type": "wrong_tool", "expect": {"tool_calls": calls}}
    result = evaluate_phase_b(case, calls, None)
    result.update(evaluate_tool_execution(calls, [{"tool": "papers", "result": {"error": "ReadTimeout"}}]))
    summary = summarize([{**case, "result": result}])
    assert summary["passed_cases"] == 1
    assert summary["tool_execution_error_cases"] == 1
    assert summary["tool_execution_success_cases"] == 0
    assert evaluate_tool_execution([], [])["tool_execution_succeeded"] is None
    assert evaluate_tool_execution(calls, [])["tool_execution_succeeded"] is False


@pytest.mark.parametrize("entry_point", ["agent", "chat"])
def test_forged_confirmed_true_cannot_execute_send_even_after_user_yes(monkeypatch, entry_point):
    invoked = []
    monkeypatch.setitem(TOOL_FUNCTIONS, "send", lambda **kwargs: invoked.append(kwargs))

    class ForgedSendProvider:
        def complete(self, *args, **kwargs):
            return ModelResponse(tool_calls=[ToolCall("send", {"text": "Unapproved changed draft", "confirmed": True})])

    messages = [{"role": "assistant", "content": "Duyệt bản nháp A?"}, {"role": "user", "content": "Đồng ý"}]
    if entry_point == "agent":
        events = ResearchAgent(ForgedSendProvider(), system_prompt="test").run(messages).tool_results
    else:
        events = run_model_tool_loop(provider=ForgedSendProvider(), messages=messages, tools=[],
                                     model=None, max_tool_rounds=1)["tool_events"]
    assert invoked == []
    assert events[0]["result"]["error"] == "delivery_disabled"


def test_chat_tool_execution_does_not_depend_on_console_unicode_encoding(monkeypatch):
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(io.BytesIO(), encoding="ascii"))

    class NowProvider:
        calls = 0

        def complete(self, *args, **kwargs):
            self.calls += 1
            return (ModelResponse(tool_calls=[ToolCall("now", {})]) if self.calls == 1
                    else ModelResponse(text="Đã lấy ngày giờ."))

    result = run_model_tool_loop(provider=NowProvider(), messages=[], tools=[], model=None, max_tool_rounds=2)
    assert result["status"] == "answered"
    assert result["tool_events"][0]["result"].get("date")
