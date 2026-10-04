# Roadmap

**Current Milestone:** ⏸️ **none in progress** — Milestones 0–1 complete, 2–5 frozen
**Status:** **PAUSED (2026-10-04)** — awaiting **JevBench #182 evaluation + board publication** (WS-B-022; evidence in `docs/jevbench-noninterference.md`)
**Resume trigger:** #182 **closed** + **board published** → re-run reachability audit → ADR-0017 (go-ahead required)
**Source of truth:** `docs/tachyone_prd.md` **v1.2.0** §6 (phases), §7 (acceptance), §8 (risks)
**Last Updated:** 2026-10-04

---

## Milestone 0 — Baseline System-2 (Day 1) — ✅ COMPLETE (2026-10-03)

**Goal:** Ship measured baselines on the abstained slice and fix the numeric accuracy targets so the PRD can leave "in review".
**Target:** Day 1 of the 10-day plan (PRD §6).

### Features

**baseline-system2** — **COMPLETE** (PRD bumped v1.1.0 → **v1.2.0**)

- ✅ Ran System-1 + LLM candidates (`ornith-9b`, `ling-tiny`) **+ the SLM base `qwen2.5:0.5b`** on the slice `confidence < τ` (τ = 0.6) under the `compare.py` protocol — 4 engines × 4 eval sets
- ✅ Slice sizes + GPU recorded next to every number (1 / 4 / 18 / **264**; τ sweep 0.30–0.95)
- ✅ A/B service context: 2,048 vs 4,096 → **2,048** (identical accuracy/latency; 0 rows exceed 2,048 tokens)
- ✅ PRD §2 updated: `≥0.723` (LLM candidate) / `≥0.474` (System-1), anchor `eval_multi_domains` n=264

**Exit criteria:** ✅ PRD §2 has exact numeric targets; ✅ context decision recorded in `STATE.md` (WS-AD-007).
**Evidence:** `docs/phase0-baseline.md` · 24 artifacts `benchmarks/results/phase0_*.json`.
**Open follow-ups:** WS-B-015 (approve PRD v1.2.0), WS-B-016/017/018.

---

## Milestone 1 — SFT Mixture Data (Days 2–3) — ✅ COMPLETE (2026-10-04)

**Goal:** A reproducible, contamination-audited SFT dataset rendered from the wire protocol.

### Features

**slm-mixture-data** — **COMPLETE** (DAT-01…08, 8/8 delivered)

- ✅ `training/configs/data_sft_slm.json`: 7 languages × 5 domains, seed **20261003** → 85,500 raw → **50,180 clean** records
- ✅ Labels derived from text (ADR-0014/0015) — upstream generator imported **unmodified** (workspace package `slm_pipeline/` never shadows it)
- ✅ Golden-hash idempotence + deterministic split (`sha256(line)%10` → 45,175 / 5,005), 16 tests green in 3 s
- ✅ Contamination audit **pass**: overlap **0/0** after removing 35,320 colliding raw records (41.31% — shared phrase banks), 18,000 frozen records compared
- ✅ SFT rendering: 50,180 pairs (wire-request prompt → §3.4 label), every prompt re-parsed by `tachyone.wire.parse_request`, **0 rejected**

**Exit criteria:** ✅ golden-hash test green; ✅ audit record written (`artifacts/slm-mixture-v1/audit.json`); ✅ config matches PRD §3.3.
**Evidence:** `docs/slm-mixture-v1.md` (dataset card, sha256 of every artifact).
**Open follow-ups:** WS-B-019 (publish dataset to HF), WS-B-020 (probe audit when probe data exists).

---

## Milestone 2 — LoRA / SFT Training (Days 4–5) — ⏸️ PAUSED (WS-B-022; also gated by ADR-0017)

**Goal:** A fine-tuned adapter beating the Phase 0 slice targets without regressing `eval_en`.

### Features

**slm-lora-sft** — PLANNED

- **ADR-0017 published before any training code** (PRD §6 Fase 2)
- LoRA hyperparameters frozen per PRD §3.2 (r=16, α=32, dropout 0.05, LR 2e-4 cosine, effective batch 32, AdamW, 3–5 epochs)
- Early stopping on `eval_en` **+** the abstained slice; gating on worst domain/language
- Experiment discipline: pinned seed, pre-run config verification, control before variance claims, explicit adapter (never routed harness)
- Estimated 4–12 h GPU

**Exit criteria:** checkpoint + eval report; `eval_en` not regressed; slice accuracy vs Phase 0 target recorded.

---

## Milestone 3 — Export & Quantization (Day 6) — ⏸️ PAUSED (WS-B-022)

**Goal:** A deployable artifact fitting the VRAM budget on both target GPUs.

### Features

**slm-export-quant** — PLANNED

- Merge LoRA weights into the trunk
- Export to vLLM (FP8) or TensorRT-LLM — choice recorded in ADR-0017
- Quantization matrix: INT4 (AWQ/GPTQ) for RTX 3060, FP8 for NVIDIA L4, bf16 reference
- Additional VRAM measured in-harness: ≤ 1.6 GB (bf16) / ≤ 1.0 GB (INT4/FP8)
- Engine flags only (prefix caching, CUDA Graphs/warm-up shapes) — no custom kernels

**Exit criteria:** artifacts load on 3060 and L4; VRAM KPI measured; contract suite still green.

---

## Milestone 4 — System-2 Integration (Days 7–8) — ⏸️ PAUSED (WS-B-022)

**Goal:** The official `system_two()` implementation wired into SDK/CLI with calibration and fallback policy — wire untouched.

### Features

**system-two-integration** — PLANNED

- `system_two(state, questions, context)` consuming `HandoffReport`; SDK export + CLI flag; `cookbook-handoff.md` migrated from stub
- Additive, client-side composition: **zero new fields** in `/v1/systemone`
- Default decoding = candidate scoring (`choice`/`score`/`noul` semantics per §3.4)
- Experimental constrained-generation mode (opt-in, §3.4 alternative)
- Temperature scaling fit per (primitive, language); report ECE + Brier + `Conf`
- τ configurable (reference 0.6), max 1 retry, documented fallback chain (SLM → remote LLM → human) explicit in diagnostics

**Exit criteria:** `JSON ok` = 1.000, 100% handoff coverage, ECE ≤ 0.030 measured, `test_contract_wire.py` untouched and green.

---

## Milestone 5 — Benchmark & Publication (Days 9–10) — ⏸️ PAUSED (WS-B-022)

**Goal:** All KPIs measured under the repo protocol and the full English doc set published as one unit.

### Features

**slm-benchmark-docs** — PLANNED

- New engine row in `benchmarks/compare.py` (the 4 existing rows are the yardstick)
- KPIs measured with GPU declared: p50/p95, ≥ 50× `ornith-9b`, ≥ 20 items/s, `JSON ok`, accuracy slice/composite, ECE/Brier/`Conf`, VRAM
- Stretch `< 8 ms` recorded **only** with §4 preconditions (FP8@L4 + minimal output) and marked as stretch
- Embedded local engine vs external servers (vLLM/TRT-LLM) both measured
- English doc set updated **as a set**: ADR-0017, `docs/cookbook-handoff.md`, `README`, `docs/model-card.md`, `CHANGELOG.md`, `benchmarks/report.md`

**Exit criteria:** PRD §7 checklist fully evidenced; gates green.

---

## Future Considerations (not scheduled)

- Scratchpad reasoning in the experimental generation mode for the hard slice (§3.4)
- Speculative decoding — measure first, keep only if the gain is real (§4.6)
- Composed System-1 + System-2 JevBench submission (explicitly out of scope now, §1.4)
- Context 4,096 if the Phase 0 A/B favors it (§3.1)
- 8-bit AdamW via bitsandbytes if the RTX 3060 is tight (§3.2)
