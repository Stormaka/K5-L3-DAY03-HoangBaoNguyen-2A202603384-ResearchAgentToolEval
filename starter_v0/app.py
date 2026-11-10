"""Streamlit UI for the Day03 Research Agent.

Run from starter_v0/:
    streamlit run app.py --server.port 8501

Reuses the tool-calling loop from chat.py (run_model_tool_loop) so UI behavior,
eval behavior and chat.py behavior stay identical.
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from chat import run_model_tool_loop
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

st.set_page_config(page_title="Research Agent — Day03 Lab", page_icon="🔎", layout="centered")


@st.cache_resource(show_spinner=False)
def load_agent_stack() -> dict:
    system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    provider = make_provider("openrouter")
    return {
        "system_prompt": system_prompt,
        "tools": to_openai_tools(declarations),
        "provider": provider,
        "model": getattr(provider, "default_model", None),
        "declarations": declarations,
    }


stack = load_agent_stack()

with st.sidebar:
    st.title("🔎 Research Agent")
    st.caption("Day03 Lab — Prompt Engineering & Tool Calling")
    st.markdown(f"**Model:** `{stack['model']}`")
    st.markdown(f"**Provider:** `openrouter`")
    st.divider()
    st.markdown("**Tools**")
    st.markdown("".join(f"- `{t['name']}`" for t in stack["declarations"]))
    st.divider()
    st.markdown(
        "Thử: *\"Tweet mới nhất của Sam Altman?\"*, *\"Tin AI hôm nay?\"*, "
        "*\"Tóm tắt bài này: <url>\"*, *\"Sam Altman là ai?\"*, "
        "*\"HN đang bàn gì về LLM?\"*, *\"Gửi bản tin lên Telegram\"*"
    )

st.title("🔎 Research Agent")
st.caption("Agent tìm kiếm tin tức/nghiên cứu — chọn tool, điền args, hỏi lại khi thiếu thông tin, xác nhận trước khi gửi.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    role = "assistant" if message["role"] == "assistant" else "user"
    with st.chat_message(role):
        st.markdown(message["content"])
        for event in message.get("tool_events", []):
            with st.expander(f"🔧 {event['tool']}({json.dumps(event['args'], ensure_ascii=False)})"):
                st.json(event["result"], expanded=False)

if prompt := st.chat_input("Hỏi agent bất cứ điều gì về tin tức / nghiên cứu..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Agent đang suy nghĩ..."):
            try:
                history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[-10:-1]
                ]
                result = run_model_tool_loop(
                    provider=stack["provider"],
                    messages=[{"role": "system", "content": stack["system_prompt"]}, *history, {"role": "user", "content": prompt}],
                    tools=stack["tools"],
                    model=None,
                    max_tool_rounds=4,
                )
                answer = result["assistant_text"] or "(không có phản hồi văn bản)"
                error = None
            except Exception as exc:
                answer = None
                error = f"{type(exc).__name__}: {exc}"

        if error:
            st.error(f"Lỗi provider: {error}")
            st.session_state.messages.append({"role": "assistant", "content": f"⚠️ {error}", "tool_events": []})
        else:
            st.markdown(answer)
            for event in result["tool_events"]:
                with st.expander(f"🔧 {event['tool']}({json.dumps(event['args'], ensure_ascii=False)})"):
                    st.json(event["result"], expanded=False)
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "tool_events": result["tool_events"],
            })
