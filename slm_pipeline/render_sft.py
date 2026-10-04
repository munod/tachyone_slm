"""Phase 1 — render mixture records as SFT pairs: wire request → gold label (DAT-05, DAT-06).

**Prompt** = the frozen `/v1/systemone` request of PRD §5.1 rendered as JSON, plus a fixed
answer cue. **Target** = the gold label the scoring engine will rank at inference (PRD §3.4):

* ``choice`` → the criteria key (the option named by the state, ADR-0015);
* ``score``  → the level index as a string (``"0"`` … ``"n-1"``, the wire ``probabilities`` keys);
* ``noul``   → ``"true"`` / ``"false"`` (the scoring engine turns their logprob gap into a
  probability via ``sigmoid(ℓ(true) − ℓ(false))``).

Nothing here derives a label — derivation stays in the upstream pipeline (ADR-0014/0015 are
binding, §3.3). This module only *renders* what the generator already produced and **rejects**
anything the contract or the target set would not accept (fail loud, B-11/B-12 guard).

Validation at generation time (§5.4 / DAT-06): every prompt is parsed back through
``tachyone.wire.parse_request`` — the same authority the contract suite tests — and every
target must be a member of the question's own candidate set. Invalid pairs are dropped and
counted, never emitted.

The prompt template lives here so Phase 4 serves **exactly** what Phase 1 trained (shared
``task``/``questions`` prefix → prefix caching, PRD §4.3).

Run (this workspace is the cwd; the clone provides ``tachyone.wire``):

    cd <workspace> && PYTHONPATH="$TACHYONE_REPO" uv run --project "$TACHYONE_REPO" \
        python -m slm_pipeline.render_sft --mixture data/tachyone_slm_mixture_v1.jsonl
"""

from __future__ import annotations

import argparse
import json
from typing import Any

#: Wire ``model`` field (§5.1) — the SLM answers as ``tachyone-latest``.
MODEL = "tachyone-latest"

#: Fixed suffix; scoring continues from here, so everything before it is a shared prefix.
ANSWER_CUE = "Answer:"

#: Rejection reasons (counted in the render report — never silent).
REJECTIONS = (
    "unknown_type",
    "malformed_criteria",
    "target_not_in_candidates",
    "wire_parse_error",
)


def wire_question(record: dict[str, Any]) -> dict[str, Any]:
    """The record's own question in §5.1 shape (type + instructions + criteria)."""
    return {
        "type": str(record["type"]),
        "instructions": str(record["instructions"]),
        "criteria": record["criteria"],
    }


def wire_request(record: dict[str, Any]) -> dict[str, Any]:
    """The canonical request: state + model + one question id (``q``)."""
    return {
        "state": str(record["state"]),
        "model": MODEL,
        "questions": {"q": wire_question(record)},
    }


def render_prompt(record: dict[str, Any]) -> str:
    """Wire request as JSON + the answer cue the scorer continues from."""
    return json.dumps(wire_request(record), ensure_ascii=False) + "\n" + ANSWER_CUE


def candidate_labels(record: dict[str, Any]) -> list[str] | None:
    """The exact label set the scoring engine ranks — ``None`` means malformed criteria."""
    kind = str(record.get("type"))
    criteria = record.get("criteria")
    if kind == "choice":
        if not isinstance(criteria, dict) or not criteria:
            return None
        return [str(key) for key in criteria]
    if kind == "score":
        if not isinstance(criteria, list) or not criteria:
            return None
        return [str(index) for index in range(len(criteria))]
    if kind == "noul":
        if not isinstance(criteria, dict):
            return None
        if "true" not in criteria or "false" not in criteria:
            return None
        return ["false", "true"]
    return None


def gold_target(record: dict[str, Any]) -> str | None:
    """Gold label for the scorer, or ``None`` when it cannot be derived from the record.

    ``noul`` targets arrive as ``0``/``1`` (wire option order: ``[false, true]``); ``choice``
    targets arrive as a criteria key or an index into it; ``score`` targets are level indices.
    """
    labels = candidate_labels(record)
    if labels is None:
        return None
    target = record.get("target")
    kind = str(record.get("type"))
    if kind == "noul":
        if isinstance(target, str) and target in labels:
            return target
        if isinstance(target, bool):
            return "true" if target else "false"
        if isinstance(target, int) and target in (0, 1):
            return labels[target]
        return None
    if kind == "choice":
        if isinstance(target, str) and target in labels:
            return target
        if isinstance(target, int) and 0 <= target < len(labels):
            return labels[target]
        return None
    if isinstance(target, int) and 0 <= target < len(labels):
        return str(target)
    if isinstance(target, str) and target in labels:
        return target
    return None


def render_pair(record: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """``(pair, None)`` on success, ``(None, reason)`` on rejection (DAT-06 accounting)."""
    kind = str(record.get("type"))
    if kind not in {"choice", "score", "noul"}:
        return None, "unknown_type"
    labels = candidate_labels(record)
    if labels is None:
        return None, "malformed_criteria"
    target = gold_target(record)
    if target is None or target not in labels:
        return None, "target_not_in_candidates"

    prompt = render_prompt(record)
    try:
        from tachyone.wire import parse_request  # contract authority (PYTHONPATH=.)

        request = parse_request(json.loads(prompt[: -len(ANSWER_CUE)]))
    except Exception:  # noqa: BLE001 - any contract violation rejects the pair
        return None, "wire_parse_error"
    if not request.questions:
        return None, "wire_parse_error"

    return (
        {
            "prompt": prompt,
            "target": target,
            "type": kind,
            "lang": record.get("lang", "?"),
            "domain": record.get("domain", "support"),
            "candidates": len(labels),
        },
        None,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="render-sft", description=__doc__)
    parser.add_argument("--mixture", required=True)
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args(argv)
    shown = 0
    with open(args.mixture, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip() or shown >= args.limit:
                continue
            record = json.loads(line)
            pair, reason = render_pair(record)
            print(
                json.dumps(pair or {"rejected": reason}, ensure_ascii=False, indent=2)
            )
            shown += 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
