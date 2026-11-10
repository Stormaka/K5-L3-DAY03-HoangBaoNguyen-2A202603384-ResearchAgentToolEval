"""Regrade recorded responses without a model/network call or changing source logs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from run_eval import evaluate_phase_b, evaluate_tool_execution, summarize
from versioning import file_hash


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    results = []
    sources = []
    for path in args.runs:
        run = json.loads(path.read_text(encoding="utf-8"))
        sources.append({"file": path.as_posix(), "sha256": file_hash(path)})
        for item in run["results"]:
            original = item["result"]
            result = dict(original)
            if original.get("failure_type") != "provider_error":
                case = {**item, "failure_type": original["case_failure_type"]}
                result = evaluate_phase_b(case, original["actual_tool_calls"], original.get("actual_text"))
                result.update(evaluate_tool_execution(original["actual_tool_calls"], item.get("tool_results", [])))
            results.append({**item, "source_run": path.name, "original_passed": original["passed"], "result": result})
    payload = {
        "kind": "offline_regrade_not_a_new_model_run",
        "evaluator_hash": file_hash(ROOT / "run_eval.py"),
        "sources": sources, "summary": summarize(results), "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload["summary"]))
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
