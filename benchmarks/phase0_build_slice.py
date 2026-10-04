"""Phase 0 — build the abstained slice (``confidence < τ``) from System-1's wire answers.

Drives the frozen ``/v1/systemone`` wire path (``tachyone.wire.answer``) with the ``encoder``
backend (System-1) over an eval set, then applies the handoff rule of
``tachyone.handoff.assess_response``:

* ``choice`` / ``score`` — abstain when the selected mass (``max(probabilities)``) < τ;
* ``noul`` — abstain when ``max(p, 1 - p)`` < τ (the engine returns ``[1-p, p]``, so
  ``max(probs)`` is the same quantity).

Rows, row order and metric semantics come from ``benchmarks.compare`` itself (same loader,
same ``_record_to_row``, same argmax rule as ``compare.accuracy``), so every number here is
comparable with the harness tables — BSL-01.

Outputs:

* **slice JSONL** — the abstained records, byte-identical to the input records, consumable by
  ``benchmarks.compare run --engine llm --format jsonl --data <slice>``;
* **report JSON** — τ, slice size (denominator) per eval set, System-1 accuracy on
  full/slice/kept rows, per type and per language breakdown, environment (GPU declared).

Run (from the ``munod/tachyone`` checkout):

    TACHYONE_BACKEND=encoder \
    TACHYONE_ADAPTERS="tachyone-en=checkpoints/en,tachyone-multi=checkpoints/multi" \
    PYTHONPATH=. uv run python <this file> \
        --data data/eval_en.jsonl \
        --slice-out benchmarks/results/phase0_slice_en.jsonl \
        --report-out benchmarks/results/phase0_slice_en.json
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from tachyone.backends import build_backend
from tachyone.config import Config

from benchmarks import compare


def _parse_taus(raw: str) -> list[float]:
    """Parse ``--taus 0.5,0.6,...`` into a sorted list of thresholds."""
    values = sorted({float(part.strip()) for part in raw.split(",") if part.strip()})
    for value in values:
        if not 0.0 <= value <= 1.0:
            raise SystemExit(f"--taus entries must be within [0, 1], got {value}")
    return values


def _percentile(values: list[float], fraction: float) -> float:
    """Linearly interpolated percentile (the estimator ``benchmarks.compare`` uses)."""
    if not values:
        return float("nan")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = fraction * (len(ordered) - 1)
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def _accuracy(pairs: list[tuple[list[float] | None, int]]) -> float:
    """Top-1 accuracy over ``(distribution, gold)`` — a failed answer counts as wrong.

    Same rule as ``benchmarks.compare.accuracy`` (argmax == gold index).
    """
    if not pairs:
        return float("nan")
    correct = sum(
        1
        for probs, gold in pairs
        if probs is not None and max(range(len(probs)), key=probs.__getitem__) == gold
    )
    return correct / len(pairs)


def _group(
    pairs_by_group: dict[str, list[tuple[list[float] | None, int]]],
) -> dict[str, dict[str, Any]]:
    return {
        key: {"n": len(pairs), "accuracy": round(_accuracy(pairs), 4)}
        for key, pairs in sorted(pairs_by_group.items())
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    data_path = Path(args.data)
    if not data_path.exists():
        raise SystemExit(
            f"{data_path} not found; regenerate it with training/generate_data.py"
        )

    records = [
        json.loads(line)
        for line in data_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows = [compare._record_to_row(record) for record in records]
    if len(rows) != len(records):  # pragma: no cover - defensive
        raise SystemExit("row/record misalignment")

    env = {**os.environ, "TACHYONE_BACKEND": args.backend}
    backend = build_backend(Config.from_env(env))
    engine = compare._wire_engine(backend, model=args.model)

    tau = args.tau
    slice_records: list[dict[str, Any]] = []
    full_pairs: list[tuple[list[float] | None, int]] = []
    slice_pairs: list[tuple[list[float] | None, int]] = []
    kept_pairs: list[tuple[list[float] | None, int]] = []
    slice_by_type: dict[str, list[tuple[list[float] | None, int]]] = defaultdict(list)
    slice_by_lang: dict[str, list[tuple[list[float] | None, int]]] = defaultdict(list)
    slice_type_counts: dict[str, int] = defaultdict(int)
    slice_lang_counts: dict[str, int] = defaultdict(int)
    failures: list[str] = []
    confidences: list[float] = []
    #: (confidence, correct) for every answered row — feeds the τ sweep without a re-run.
    answered_meta: list[tuple[float, bool]] = []

    for record, row in zip(records, rows, strict=True):
        probs = engine.decide(row)
        gold = int(row["answer_index"])
        full_pairs.append((probs, gold))
        if probs is None:
            failures.append(str(record.get("id", "?")))
            continue
        confidence = max(probs)  # handoff rule for all three primitives
        confidences.append(confidence)
        correct = max(range(len(probs)), key=probs.__getitem__) == gold
        answered_meta.append((confidence, correct))
        pair = (probs, gold)
        if confidence < tau:
            slice_records.append(record)
            slice_pairs.append(pair)
            slice_by_type[str(record["type"])].append(pair)
            slice_by_lang[str(record.get("lang", "?"))].append(pair)
            slice_type_counts[str(record["type"])] += 1
            slice_lang_counts[str(record.get("lang", "?"))] += 1
        else:
            kept_pairs.append(pair)

    total = len(records)
    slice_size = len(slice_records)

    # τ sensitivity (spec edge case: a tiny/empty slice must be flagged with its denominator,
    # never published as a percentage without one) — computed from the same pass.
    sweep: dict[str, dict[str, Any]] = {}
    for value in _parse_taus(args.taus):
        members = [(c, ok) for c, ok in answered_meta if c < value]
        sweep[f"{value:.2f}"] = {
            "size": len(members),
            "share": round(len(members) / total, 4) if total else float("nan"),
            "accuracy_slice": (
                round(sum(1 for _, ok in members if ok) / len(members), 4)
                if members
                else None
            ),
            "usable_denominator": len(members) >= args.min_slice,
        }

    report: dict[str, Any] = {
        "phase": 0,
        "feature": "baseline-system2",
        "tau": tau,
        "dataset": {
            "path": str(data_path),
            "rows": total,
            "per_task_cap": "none (full split)",
        },
        "system1": {
            "backend": args.backend,
            "model": args.model,
            "accuracy_full": round(_accuracy(full_pairs), 4),
            "accuracy_slice": round(_accuracy(slice_pairs), 4),
            "accuracy_kept": round(_accuracy(kept_pairs), 4),
            "correct_slice": sum(
                1
                for probs, gold in slice_pairs
                if probs is not None
                and max(range(len(probs)), key=probs.__getitem__) == gold
            ),
            "wire_failures": len(failures),
            "wire_failure_ids": failures[:50],
        },
        "slice": {
            "definition": "System-1 confidence < tau (tachyone.handoff.assess_response rule)",
            "size": slice_size,
            "share": round(slice_size / total, 4) if total else float("nan"),
            "kept_size": len(kept_pairs),
            "coverage_rule": "100% of slice rows must receive a valid wire answer from System-2",
            "by_type": {
                key: {
                    "size": slice_type_counts[key],
                    "accuracy": round(_accuracy(pairs), 4),
                }
                for key, pairs in sorted(slice_by_type.items())
            },
            "by_lang": {
                key: {
                    "size": slice_lang_counts[key],
                    "accuracy": round(_accuracy(pairs), 4),
                }
                for key, pairs in sorted(slice_by_lang.items())
            },
        },
        "confidence": {
            "mean": round(statistics.fmean(confidences), 4)
            if confidences
            else float("nan"),
            "min": round(min(confidences), 4) if confidences else float("nan"),
            "max": round(max(confidences), 4) if confidences else float("nan"),
            "percentiles": {
                f"p{label}": round(_percentile(confidences, fraction), 4)
                for label, fraction in (
                    ("01", 0.01),
                    ("05", 0.05),
                    ("10", 0.10),
                    ("25", 0.25),
                    ("50", 0.50),
                )
            }
            if confidences
            else {},
        },
        "tau_sweep": sweep,
        "environment": compare._environment(),
    }

    if args.slice_out:
        out = Path(args.slice_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as handle:
            for record in slice_records:
                handle.write(
                    json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n"
                )
        report["slice"]["slice_out"] = str(out)

    if args.report_out:
        out = Path(args.report_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"wrote {out}", file=sys.stderr)

    print(json.dumps(report, indent=2, sort_keys=True))
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="phase0-build-slice",
        description="Phase 0: System-1 abstained slice builder",
    )
    parser.add_argument(
        "--data", required=True, help="eval records JSONL (frozen eval set)"
    )
    parser.add_argument(
        "--slice-out", default=None, help="write the abstained records here"
    )
    parser.add_argument(
        "--report-out", default=None, help="write the measurement report JSON"
    )
    parser.add_argument(
        "--tau", type=float, default=0.6, help="handoff threshold (PRD §2: 0.6)"
    )
    parser.add_argument(
        "--taus",
        default="0.3,0.5,0.6,0.7,0.8,0.9,0.95",
        help="comma-separated τ sweep reported alongside --tau (slice-size sensitivity)",
    )
    parser.add_argument(
        "--min-slice",
        type=int,
        default=30,
        help="denominator below which a τ is flagged as an unusable slice size",
    )
    parser.add_argument("--backend", default="encoder", help="System-1 backend")
    parser.add_argument("--model", default="tachyone-latest", help="wire `model` field")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
