"""Smoke-test the deployed Streamlit HTTP/WebSocket protocol (not visual QA)."""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import streamlit
import websockets
from streamlit.proto.BackMsg_pb2 import BackMsg
from streamlit.proto.ForwardMsg_pb2 import ForwardMsg
from websockets.sync.client import connect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run_eval import REFUSAL_TEXT
from versioning import artifact_version_dict, build_artifact_version, file_hash


def read_run(ws):
    evidence = {"markdown": [], "alerts": [], "json": [], "exceptions": [], "widget_id": None, "script_path": None, "page_hash": None}
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        data = ws.recv(timeout=max(1, deadline - time.monotonic()))
        message = ForwardMsg()
        message.ParseFromString(data)
        kind = message.WhichOneof("type")
        if kind == "new_session":
            evidence["script_path"] = message.new_session.main_script_path
            evidence["page_hash"] = message.new_session.page_script_hash
        elif kind == "delta" and message.delta.HasField("new_element"):
            element = message.delta.new_element
            if element.HasField("markdown"):
                evidence["markdown"].append(element.markdown.body)
            elif element.HasField("chat_input"):
                evidence["widget_id"] = element.chat_input.id
            elif element.HasField("alert"):
                evidence["alerts"].append(element.alert.body)
            elif element.HasField("json"):
                evidence["json"].append(json.loads(element.json.body))
            elif element.HasField("exception"):
                evidence["exceptions"].append(str(element.exception))
        elif kind == "script_finished" and message.script_finished != ForwardMsg.FINISHED_EARLY_FOR_RERUN:
            evidence["script_finished"] = int(message.script_finished)
            return evidence
    raise TimeoutError("Streamlit run did not finish within 60 seconds")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/public_app_smoke.json")
    args = parser.parse_args()
    url = args.url.rstrip("/")
    version = build_artifact_version("v6", ROOT / "artifacts/system_prompt.md", ROOT / "artifacts/tools.yaml")
    evidence = {
        "kind": "public_http_websocket_smoke_not_browser_visual_qa", "url": url,
        "streamlit_version": streamlit.__version__, "websockets_version": websockets.__version__,
        "checked_at": datetime.now(timezone(timedelta(hours=7))).isoformat(),
        **artifact_version_dict(version), "app_hash": file_hash(ROOT / "app.py"), "turns": [],
    }
    for path in ["/", "/_stcore/health"]:
        response = requests.get(url + path, timeout=30)
        response.raise_for_status()
        evidence[path] = {"status_code": response.status_code}
        if path.endswith("health"):
            assert response.text.strip() == "ok", response.text
    ws_url = url.replace("https://", "wss://").replace("http://", "ws://") + "/_stcore/stream"
    with connect(ws_url, origin=url, subprotocols=["streamlit"], open_timeout=30, max_size=10_000_000) as ws:
        request = BackMsg()
        request.rerun_script.query_string = ""
        ws.send(request.SerializeToString())
        initial = read_run(ws)
        assert not initial["exceptions"], initial
        assert Path(initial["script_path"]).resolve() == (ROOT / "app.py").resolve(), initial["script_path"]
        assert version.artifact_version in initial["markdown"], initial["markdown"]
        assert any("Gửi Telegram đang tắt" in text for text in initial["alerts"]), initial["alerts"]
        assert not any("- `send`" in text for text in initial["markdown"]), initial["markdown"]
        evidence["initial"] = initial
        widget_id, page_hash = initial["widget_id"], initial["page_hash"]
        for prompt, expected in [
            ("Giải giúp mình bài toán tích phân: nguyên hàm của x^2 là gì?", REFUSAL_TEXT),
            ("Viết hàm Python tính dãy Fibonacci giúp mình", REFUSAL_TEXT),
            ("Dịch câu 'I love artificial intelligence' sang tiếng Pháp", REFUSAL_TEXT),
            ("Hôm nay là ngày mấy?", "2026"),
            ("Gửi bản tin 'Bản tin thử nghiệm' lên Telegram giúp mình", None),
        ]:
            request = BackMsg()
            request.rerun_script.page_script_hash = page_hash
            widget = request.rerun_script.widget_states.widgets.add()
            widget.id = widget_id
            widget.chat_input_value.data = prompt
            ws.send(request.SerializeToString())
            result = read_run(ws)
            evidence["last_run"] = result
            args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
            assert not result["exceptions"], result
            # Last markdown is the new answer; earlier entries include history.
            answer = result["markdown"][-1]
            if expected == REFUSAL_TEXT:
                assert answer == expected, answer
            elif expected:
                assert expected in answer and "Lỗi provider" not in answer, answer
            else:
                # The initial UI already states delivery is disabled. This turn
                # must ask yes/no rather than claim successful delivery.
                assert result["json"][-1].get("awaiting_user") is True, result
                assert result["json"][-1].get("response_type") == "yes_no", result
                assert not any(item.get("status") == "sent" for item in result["json"]), result
            evidence["turns"].append({"prompt": prompt, "answer": answer, "passed": True,
                                      "script_finished": result["script_finished"]})
            widget_id = result["widget_id"] or widget_id
            page_hash = result["page_hash"] or page_hash
            print(f"PASS: {prompt}", flush=True)
    evidence["passed"] = True
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
