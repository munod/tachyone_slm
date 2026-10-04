"""Phase 0 — static context-coverage report for the 2,048 vs 4,096 service-context A/B.

Counts tokens per eval-set row under the **Qwen2.5 tokenizer** (the SLM base, PRD §3.1) and
reports how many rows would be truncated at each candidate context. Two views are given:

* ``state`` — just the state text (the PRD §1.3 comparison against B-13's 512-token cut);
* ``wire``  — state + rendered questions (what actually reaches the engine), computed as
  ``len(tokenize(state)) + sum(len(tokenize(criteria/instructions))) + overhead``; the
  overhead (chat template, system prompt, JSON punctuation) is declared, not guessed away.

Static measurement only: no inference, no GPU, safe to run while benchmarks hold the card.

Run (from the ``munod/tachyone`` checkout):

    PYTHONPATH=. uv run python <this file> \
        --data data/eval_en.jsonl --slice <slice jsonl> \
        --out benchmarks/results/phase0_context_en.json
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

#: Chat overhead the wire path adds around the JSON payload: the system prompt
#: (``tachyone.backends.llm._SYSTEM_PROMPT``, tokenized at runtime — never guessed) plus a
#: fixed allowance for the chat template / JSON punctuation of the request.
JSON_OVERHEAD_TOKENS = 60
SYSTEM_PROMPT_FALLBACK_TOKENS = 400


def _percentile(values: list[int], fraction: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    position = fraction * (len(ordered) - 1)
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def _stats(values: list[int]) -> dict[str, Any]:
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "mean": round(statistics.fmean(values), 1),
        "p50": round(_percentile(values, 0.50), 1),
        "p95": round(_percentile(values, 0.95), 1),
        "max": max(values),
        "over_2048": sum(1 for value in values if value > 2048),
        "over_4096": sum(1 for value in values if value > 4096),
    }


def record_tokens(
    tokenizer: Any, record: dict[str, Any], system_tokens: int
) -> dict[str, int]:
    state = len(
        tokenizer.encode(str(record.get("state", "")), add_special_tokens=False)
    )
    criteria = record.get("criteria")
    pieces: list[str] = [str(record.get("instructions", ""))]
    if isinstance(criteria, dict):
        pieces.extend(f"{key} {value or key}" for key, value in criteria.items())
    else:
        pieces.extend(str(level) for level in criteria or [])
    payload = len(tokenizer.encode(" ".join(pieces), add_special_tokens=False))
    return {
        "state": state,
        "wire": state + payload + JSON_OVERHEAD_TOKENS,
        "wire_with_system": state + payload + JSON_OVERHEAD_TOKENS + system_tokens,
    }


def _load(path: str) -> list[dict[str, Any]]:
    source = Path(path)
    return [
        json.loads(line)
        for line in source.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="phase0-context-lengths", description=__doc__)
    parser.add_argument("--data", required=True, help="full eval records JSONL")
    parser.add_argument("--slice", default=None, help="abstained-slice records JSONL")
    parser.add_argument(
        "--model", default="Qwen/Qwen2.5-0.5B-Instruct", help="tokenizer id"
    )
    parser.add_argument("--out", default=None, help="report JSON path")
    args = parser.parse_args(argv)

    from transformers import AutoTokenizer  # lazy: needs the `train` extra

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    try:  # the real system prompt of the wire's LLM path, tokenized with the SLM tokenizer
        from tachyone.backends.llm import _SYSTEM_PROMPT

        system_tokens = len(tokenizer.encode(_SYSTEM_PROMPT, add_special_tokens=False))
        system_source = "tachyone.backends.llm._SYSTEM_PROMPT"
    except (
        ImportError,
        AttributeError,
        ValueError,
        OSError,
    ):  # repo not importable/parsable
        system_tokens = SYSTEM_PROMPT_FALLBACK_TOKENS
        system_source = "fallback constant"

    report: dict[str, Any] = {
        "model": args.model,
        "candidates": [2048, 4096],
        "overhead": {
            "system_prompt_tokens": system_tokens,
            "system_prompt_source": system_source,
            "json_overhead_tokens": JSON_OVERHEAD_TOKENS,
        },
    }
    for label, path in (("full", args.data), ("slice", args.slice)):
        if not path:
            continue
        records = _load(path)
        rows = [record_tokens(tokenizer, record, system_tokens) for record in records]
        report[label] = {
            "path": str(path),
            "rows": len(records),
            "state": _stats([row["state"] for row in rows]),
            "wire": _stats([row["wire"] for row in rows]),
            "wire_with_system": _stats([row["wire_with_system"] for row in rows]),
        }

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {out}")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
