"""Phase 1 — raw → dedup → split → render → audit → report (`Tachyone-SLM-Mixture-v1`).

Pipeline, in order:

1. **Contamination dedup** — every raw record whose *state* or *prompt fingerprint* matches a
   frozen eval set is **removed** (spec DAT-04 AC2 sanctions exactly this: "or the records be
   removed and the audit re-run — never proceed silently"). The drop is counted per reason and
   per domain/language. The canonical ``tachyone_slm_mixture_v1.jsonl`` name is written **only
   for the clean dataset** — the raw file stays ``*.raw.jsonl``.
   *Measured 2026-10-03:* the shared phrase-bank pools make **41.3%** of raw records collide,
   which is why the config generates 85,500 raw records to land ≈50,180 clean ones.
2. **Deterministic split** — ``val`` when ``int(sha256(raw_line)[:8], 16) % 10 == 0``, else
   ``train``. Keyed on record *bytes*, so membership is stable across runs and independent of
   record order, ids (positional, colliding) and language/domain cycles (DAT-03).
3. **Render pairs** through ``slm_pipeline.render_sft`` — prompt = wire request (§5.1), target =
   gold label (§3.4); every prompt is parsed back by ``tachyone.wire.parse_request`` and every
   target must sit in its own candidate set. Rejected pairs are dropped and **counted**
   (DAT-05/DAT-06), never emitted.
4. **Contamination audit** re-run on the clean set, with the temperature-fit ``val`` side
   audited separately; any overlap fails the build (DAT-04).
5. **Reports** — split sizes, rejection reasons, per-cell counts (language × domain) for the
   worst-cell gating of §3.2 (DAT-07), written to ``artifacts/slm-mixture-v1/``.

Outputs: ``data/*.train.jsonl``, ``data/*.val.jsonl``, ``data/*.pairs.jsonl`` (big, gitignored)
and ``artifacts/slm-mixture-v1/{audit,split_render}.json`` (small, versioned).

Run (this workspace is the cwd, the clone provides the packages):

    cd <workspace> && PYTHONPATH="$TACHYONE_REPO" uv run --project "$TACHYONE_REPO" \
        python -m slm_pipeline.prepare_sft --frozen-dir "$TACHYONE_REPO/data"
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from slm_pipeline.audit_contamination import audit, load_records, prompt_fingerprint
from slm_pipeline.render_sft import render_pair

WORKSPACE = Path(__file__).resolve().parents[1]
RAW = WORKSPACE / "data" / "tachyone_slm_mixture_v1.raw.jsonl"
CLEAN = WORKSPACE / "data" / "tachyone_slm_mixture_v1.jsonl"
ARTIFACTS = WORKSPACE / "artifacts" / "slm-mixture-v1"

#: Frozen eval sets that must never appear in the mixture (§3.3).
FROZEN_SETS = (
    "eval_en.jsonl",
    "eval_multi.jsonl",
    "eval_en_domains.jsonl",
    "eval_multi_domains.jsonl",
)

VAL_MODULUS = 10  # ~10% of the clean lines go to the temperature-fit validation split


def side(raw_line: str) -> str:
    """``"val"`` or ``"train"`` — a pure function of the record's bytes (DAT-03)."""
    digest = int(hashlib.sha256(raw_line.encode("utf-8")).hexdigest()[:8], 16)
    return "val" if digest % VAL_MODULUS == 0 else "train"


def _write_jsonl(path: Path, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(row if row.endswith("\n") else row + "\n" for row in rows),
        encoding="utf-8",
    )


def build_frozen_index(frozen_paths: dict[str, Path]) -> tuple[set[str], set[str]]:
    states: set[str] = set()
    prompts: set[str] = set()
    for path in frozen_paths.values():
        for record in load_records(path):
            if not record.get("state"):
                continue
            states.add(str(record["state"]))
            fingerprint = prompt_fingerprint(record)
            if fingerprint:
                prompts.add(fingerprint)
    return states, prompts


def dedup(
    raw_lines: list[str],
    records: list[dict[str, Any]],
    frozen_states: set[str],
    frozen_prompts: set[str],
) -> tuple[list[str], list[dict[str, Any]], dict[str, Any]]:
    """Drop every record a frozen eval set already contains (DAT-04 AC2)."""
    clean_lines: list[str] = []
    clean_records: list[dict[str, Any]] = []
    dropped_state: Counter[str] = Counter()
    dropped_prompt: Counter[str] = Counter()
    dropped_empty_state = 0
    for line, record in zip(raw_lines, records, strict=True):
        state = str(record.get("state", ""))
        if not state:
            # An empty state carries no information and cannot leak a frozen row's content;
            # it is kept (the frozen sets contain such rows too) and reported.
            dropped_empty_state += 0
        else:
            cell = f"{record.get('domain', 'support')}/{record.get('lang', '?')}"
            if state in frozen_states:
                dropped_state[cell] += 1
                continue
            fingerprint = prompt_fingerprint(record)
            if fingerprint and fingerprint in frozen_prompts:
                dropped_prompt[cell] += 1
                continue
        clean_lines.append(line)
        clean_records.append(record)
    return (
        clean_lines,
        clean_records,
        {
            "raw_records": len(raw_lines),
            "clean_records": len(clean_lines),
            "dropped_state_match": sum(dropped_state.values()),
            "dropped_prompt_match": sum(dropped_prompt.values()),
            "drop_rate": round(1 - len(clean_lines) / len(raw_lines), 4)
            if raw_lines
            else 0.0,
            "empty_states_kept": dropped_empty_state,
            "dropped_by_cell": dict(sorted((dropped_state + dropped_prompt).items())),
        },
    )


def run(raw_path: Path, frozen_dir: Path, workspace: Path) -> dict[str, Any]:
    raw_lines = [
        line
        for line in raw_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    records = [json.loads(line) for line in raw_lines]

    # 1. contamination dedup (fail-loud: the audit below re-checks the clean result)
    frozen_paths = {
        name.removesuffix(".jsonl"): frozen_dir / name
        for name in FROZEN_SETS
        if (frozen_dir / name).exists()
    }
    if not frozen_paths:
        raise SystemExit(
            f"no frozen eval sets found in {frozen_dir} — generate them first"
        )
    frozen_states, frozen_prompts = build_frozen_index(frozen_paths)
    clean_lines, clean_records, dedup_report = dedup(
        raw_lines, records, frozen_states, frozen_prompts
    )
    _write_jsonl(CLEAN, clean_lines)

    # 2. split (pure function of the record bytes)
    train_lines = [line for line in clean_lines if side(line) == "train"]
    val_lines = [line for line in clean_lines if side(line) == "val"]
    val_records = [json.loads(line) for line in val_lines]

    stem = CLEAN.stem
    data_dir = CLEAN.parent
    _write_jsonl(data_dir / f"{stem}.train.jsonl", train_lines)
    _write_jsonl(data_dir / f"{stem}.val.jsonl", val_lines)

    # 3. render pairs (validated at generation time)
    pairs: list[dict[str, Any]] = []
    rejected: Counter[str] = Counter()
    for line, record in zip(clean_lines, clean_records, strict=True):
        pair, reason = render_pair(record)
        if pair is None:
            rejected[reason or "unknown"] += 1
            continue
        pair["split"] = side(line)
        pairs.append(pair)

    pairs_path = data_dir / f"{stem}.pairs.jsonl"
    _write_jsonl(
        pairs_path,
        [json.dumps(pair, sort_keys=True, ensure_ascii=False) for pair in pairs],
    )

    # 4. audit the CLEAN set (val audited as its own side)
    report = audit(
        mixture=clean_records,
        val=val_records,
        frozen_paths=frozen_paths,
        workspace=workspace,
    )

    # 5. reports
    cells: dict[str, Counter[str]] = {}
    per_primitive: Counter[str] = Counter()
    per_language: Counter[str] = Counter()
    for pair in pairs:
        cells.setdefault(str(pair["lang"]), Counter())[str(pair["domain"])] += 1
        per_primitive[str(pair["type"])] += 1
        per_language[str(pair["lang"])] += 1

    split_render = {
        "dataset": "Tachyone-SLM-Mixture-v1",
        "dedup": dedup_report,
        "rule": f"val if int(sha256(raw_line)[:8],16) % {VAL_MODULUS} == 0",
        "records": len(clean_lines),
        "split": {
            "train": len(train_lines),
            "val": len(val_lines),
            "val_share": round(len(val_lines) / len(clean_lines), 4)
            if clean_lines
            else 0.0,
        },
        "pairs": len(pairs),
        "dropped_pairs": dict(sorted(rejected.items())),
        "by_primitive": dict(sorted(per_primitive.items())),
        "by_language": dict(sorted(per_language.items())),
        "per_cell_language_x_domain": {
            lang: dict(sorted(counts.items())) for lang, counts in sorted(cells.items())
        },
        "language_domain_cells": sum(len(counts) for counts in cells.values()),
        "outputs": {
            name: {
                "path": str(path.relative_to(workspace)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
            for name, path in (
                ("clean", CLEAN),
                ("train", data_dir / f"{stem}.train.jsonl"),
                ("val", data_dir / f"{stem}.val.jsonl"),
                ("pairs", pairs_path),
            )
        },
    }

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (ARTIFACTS / "split_render.json").write_text(
        json.dumps(split_render, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "dedup": {
                    k: dedup_report[k]
                    for k in ("raw_records", "clean_records", "drop_rate")
                },
                "split": split_render["split"],
                "pairs": len(pairs),
                "dropped": dict(rejected),
                "audit": report["result"],
                "overlap": report["overlap"],
            },
            indent=2,
        )
    )
    if report["result"] == "fail":
        raise SystemExit(
            "contamination audit FAILED — see artifacts/slm-mixture-v1/audit.json"
        )
    return {"split_render": split_render, "audit": report}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="prepare-sft", description=__doc__)
    parser.add_argument("--raw", default=str(RAW), help="raw generation (*.raw.jsonl)")
    parser.add_argument(
        "--frozen-dir", required=True, help="directory holding the frozen eval sets"
    )
    args = parser.parse_args(argv)
    run(Path(args.raw), Path(args.frozen_dir), WORKSPACE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
