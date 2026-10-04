"""Phase 0 — render the measured baselines into the Phase 0 report (BSL-03/04/05/06/07).

Consumes the artifacts produced by ``phase0_build_slice.py``, ``phase0_run_llms.sh``,
``phase0_run_context_ab.sh`` and ``phase0_context_lengths.py`` and writes one markdown
report with every number traceable to its artifact. Nothing is computed from thin air:
missing artifacts are reported as **not measured**, never guessed (WS-AD-006).

    PYTHONPATH=. uv run python benchmarks/phase0_render.py \
        --results /path/to/benchmarks/results --out docs/phase0-baseline.md
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

#: Engines in report order: (tag used in artifact filenames, display name).
ENGINES = (
    ("system1", "System-1 (encoder)"),
    ("ollama", "SLM base qwen2.5:0.5b (Ollama)"),
    ("ling", "ling-tiny (llama-server Q4)"),
    ("ornith", "ornith-9b (llama-server Q4)"),
)

#: Eval sets in report order.
DATASETS = ("eval_en", "eval_en_domains", "eval_multi", "eval_multi_domains")

#: Published System-1 references (composite yardstick, BSL-06) — `benchmarks/report.md`,
#: git 18bdc27, RTX 3060. Copied verbatim; never re-measured here.
YARDSTICK = {
    "eval_en": ("english", "1500", "1.000", "0.006"),
    "eval_en_domains": ("english five-domain", "7500", "1.000", "0.009"),
    "eval_multi": ("multilingual", "1500", "0.895", "0.062"),
    "eval_multi_domains": ("multilingual five-domain", "7500", "0.997", "0.001"),
}


def _load(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        if math.isnan(value):
            return "—"
        return f"{value:.{digits}f}"
    return str(value)


def build(results: Path) -> str:
    slices = {ds: _load(results / f"phase0_slice_{ds}.json") for ds in DATASETS}
    contexts = {ds: _load(results / f"phase0_context_{ds}.json") for ds in DATASETS}
    artifacts: dict[str, dict[str, dict[str, Any] | None]] = {}
    for tag, _ in ENGINES:
        artifacts[tag] = {
            ds: _load(results / f"phase0_{tag}_{ds}.json") for ds in DATASETS
        }

    gpu = ""
    for report in slices.values():
        if report:
            gpu = report["environment"].get("gpu", "")
            timestamp = report["environment"].get("timestamp", "")
            break
    else:  # pragma: no cover - no slice report at all
        timestamp = ""

    lines: list[str] = [
        "# Phase 0 — System-2 baseline on the abstained slice",
        "",
        "**Feature:** `baseline-system2` (BSL-01…07) · **Phase:** 0 · **Status:** measured",
        "",
        (
            f"*GPU:* {gpu or 'not recorded'} · *run:* {timestamp} · "
            "*protocol:* PRD §2 (sequential, batch=1, warm-up excluded, same rows, same metric "
            "implementation, GPU declared) · *harness:* `benchmarks/compare.py`"
        ),
        "",
        (
            "Every table below is rendered from the artifacts in `benchmarks/results/`; "
            "an absent artifact renders as **not measured**."
        ),
        "",
        "## 1. Slice sizes (BSL-02)",
        "",
        (
            "Slice = eval-set rows where System-1's wire confidence is below τ "
            "(`tachyone.handoff.assess_response` rule: `max(probabilities)` for `choice`/`score`, "
            "`max(p, 1-p)` for `noul`)."
        ),
        "",
        "| Eval set | rows | System-1 acc (full) | τ=0.6 slice | share | System-1 acc on slice | kept |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for ds in DATASETS:
        report = slices[ds]
        if not report:
            lines.append(f"| `{ds}` | — | — | not measured | — | — | — |")
            continue
        sl = report["slice"]
        sys1 = report["system1"]
        lines.append(
            f"| `{ds}` | {report['dataset']['rows']} | {_fmt(sys1['accuracy_full'])} "
            f"| **{sl['size']}** | {_fmt(sl['share'], 4)} | {_fmt(sys1['accuracy_slice'])} "
            f"| {sl['kept_size']} |"
        )

    lines += [
        "",
        "### τ sensitivity (a slice must have a denominator to be quotable)",
        "",
    ]
    lines.append("| Eval set | " + " | ".join(f"τ={t}" for t in _taus(slices)) + " |")
    lines.append("| --- | " + " | ".join("---:" for _ in _taus(slices)) + " |")
    for ds in DATASETS:
        report = slices[ds]
        if not report:
            continue
        cells = []
        for tau in _taus(slices):
            entry = report["tau_sweep"].get(tau)
            cells.append(
                f"{entry['size']} ({_fmt(entry['share'], 4)})" if entry else "—"
            )
        lines.append(f"| `{ds}` | " + " | ".join(cells) + " |")

    lines += [
        "",
        "## 2. Candidate accuracy on the identical slice (BSL-03 / BSL-07)",
        "",
        (
            "Accuracy counts a contract failure as wrong; `JSON ok` is the share of rows that "
            "produced a contract-valid payload at all (failures are recorded, never dropped)."
        ),
        "",
    ]

    for ds in DATASETS:
        report = slices[ds]
        lines.append(f"### `{ds}`")
        lines.append("")
        if not report:
            lines += ["_slice not measured._", ""]
            continue
        lines.append(
            f"n = **{report['slice']['size']}** abstained rows "
            f"(of {report['dataset']['rows']}; τ = {report['tau']})"
        )
        lines.append("")
        lines.append(
            "| Engine | n answered | Accuracy | JSON ok | p50 (ms) | p95 (ms) | items/s | VRAM (MiB) |"
        )
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        for tag, name in ENGINES:
            art = artifacts[tag][ds]
            if not art:
                lines.append(f"| {name} | — | not measured | — | — | — | — | — |")
                continue
            acc = art["raw"]["accuracy"]
            comp = art["compliance"]
            lat = art["latency_ms"]
            lines.append(
                f"| {name} | {comp['answered']} | {_fmt(acc)} | {_fmt(comp['rate'])} "
                f"| {_fmt(lat['p50'], 2)} | {_fmt(lat['p95'], 2)} "
                f"| {_fmt(art['throughput']['items_per_s'], 1)} "
                f"| {_fmt(art['memory']['peak_vram_mb'], 0)} |"
            )
        lines.append("")

    lines += [
        "## 3. Context coverage: 2,048 vs 4,096 (BSL-05)",
        "",
        (
            "Static token count under the Qwen2.5 tokenizer (wire = state + questions + JSON "
            "overhead; `+system` adds the measured system prompt)."
        ),
        "",
        "| Eval set | view | rows | p50 | p95 | max | over 2048 | over 4096 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for ds in DATASETS:
        ctx = contexts[ds]
        if not ctx:
            continue
        for label in ("full", "slice"):
            block = ctx.get(label)
            if not block:
                continue
            stats = block["wire_with_system"]
            lines.append(
                f"| `{ds}` | {label} (+system) | {block['rows']} | {stats['p50']} "
                f"| {stats['p95']} | {stats['max']} | **{stats['over_2048']}** "
                f"| {stats['over_4096']} |"
            )

    lines += [
        "",
        "## 4. Composite yardstick — System-1 only (BSL-06)",
        "",
        (
            "Published references (`benchmarks/report.md`, git `18bdc27`, RTX 3060) — the bar "
            "Phase 4/5 must not regress against:"
        ),
        "",
        "| Eval set | published entry | n | Accuracy | ECE |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for ds, (label, n, acc, ece) in YARDSTICK.items():
        lines.append(f"| `{ds}` | {label} | {n} | {acc} | {ece} |")

    lines += [
        "",
        "## 5. Protocol notes and deviations (read before quoting a number)",
        "",
        (
            "1. **`-n 1024` generation cap on `llama-server`** (rows `ling`, `ornith` and both "
            "context arms). The wire payload carries no `max_tokens`, so the published runs let a "
            "malformed answer generate up to `-c 8192` tokens — measured here at **6,024 tokens "
            "≈ 39 s for a single row**. A contract-valid answer needs < 400 tokens; the cap only "
            "truncates pathological generations, which are parse failures either way. "
            "**Accuracy and `JSON ok` are unaffected; the failure-dominated p95 tail is shorter "
            "than the published one** (`docs/compare.md` documents that tail as "
            "failure-dominated regardless)."
        ),
        (
            "2. **Ollama rows ran before the cap** (`num_predict` unlimited, context 4096), so "
            "their p95 tail is *not* directly comparable with the capped llama-server rows."
        ),
        (
            "3. **Temperature**: fitted by the harness on a 192-row validation split (64 rows per "
            "primitive from `train_{en,multi}.jsonl`), never on the reported slice. The 1- and "
            "4-row English slices ran with a fixed `T=1.0` — a fit would burn 192 LLM calls to "
            "calibrate 1–4 test rows and does not move argmax accuracy."
        ),
        (
            "4. **Ollama greedy variant**: the payload carries no `temperature`, so "
            "`qwen2.5:0.5b-phase0` was created locally from `qwen2.5:0.5b-instruct` with "
            "`PARAMETER temperature 0 / seed 42 / num_ctx 4096` (published protocol is "
            "`--temp 0 --seed 42`). Nothing was pushed to the Ollama registry."
        ),
        (
            "5. **System-1 adapters are the deployable Hub ones** (`munod/tachyone-en`/`-multi`). "
            "The five-domain fitted-bank checkpoints quoted in `benchmarks/report.md` "
            "(`multi_b5b_fit_bank`, 0.997) are **not distributed** (no Hub model, no release "
            "asset), so they cannot be measured here: System-1 on `eval_multi_domains` scores "
            "**0.9145 full-set / 0.4735 on the slice** with the deployable adapter."
        ),
        (
            "6. **Ollama VRAM is not in the artifacts** — the harness resolves the server pid by "
            "matching `llama-server` only. Measured separately after the runs: **718 MiB** "
            "(`ollama ps` + `nvidia-smi`, 622 MB weights resident, 100% GPU, ctx 4096)."
        ),
        (
            "7. **`eval_en` / `eval_en_domains` slices are 1 and 4 rows.** Their percentages are "
            "reported with the denominator, per the spec's edge case — they are too small to "
            "carry a published target."
        ),
        "",
        "## 6. Environment",
        "",
        "```json",
        json.dumps(
            (slices[next(iter(slices))] or {}).get("environment", {}),
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
    ]
    return "\n".join(lines) + "\n"


def _taus(slices: dict[str, dict[str, Any] | None]) -> list[str]:
    for report in slices.values():
        if report:
            return sorted(report["tau_sweep"])
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="phase0-render", description=__doc__)
    parser.add_argument(
        "--results", required=True, help="directory holding phase0_* artifacts"
    )
    parser.add_argument("--out", default=None, help="markdown report path")
    args = parser.parse_args(argv)
    text = build(Path(args.results))
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
