# Phase 3 — Export & Quantization Specification

**Feature ID:** `slm-export-quant` · **Prefix:** `EXP` · **Phase:** 3 (Day 6) · **Status:** Planned — depends on Phase 2 checkpoint + **DEC-002** (local); frozen by WS-B-022
**PRD source:** `docs/tachyone_prd.md` v1.1.0 — §4 (performance optimization, hardware matrix), §2 (VRAM KPI), §6 Fase 3, §7.5 (acceptance), §8 (Ada availability / new deps risks)

---

## Problem Statement

A trained adapter is not a servable System-2. The merged model must be exported to a real inference stack and quantized so it fits the VRAM budget — ≤ 1.6 GB additional (bf16) / ≤ 1.0 GB (INT4/FP8) — on the actual hardware matrix: RTX 3060 (Ampere, **no FP8**) for the main path and NVIDIA L4 (Ada) only for the stretch. The stack choice (vLLM vs TensorRT-LLM) is recorded in **DEC-002** (local, PRD v2.0 — no upstream ADR) and must not be re-litigated here.

## Goals

- [ ] LoRA weights merged into the trunk (single deployable model).
- [ ] Export to the DEC-002-chosen engine (vLLM or TensorRT-LLM).
- [ ] Quantization matrix produced: bf16 reference, INT4 (AWQ/GPTQ) @ 3060, FP8 @ L4.
- [ ] Additional VRAM measured in-harness against both KPI bounds.
- [ ] Serving flags (prefix caching, CUDA Graphs/warm-up shapes) configured — as configuration, not custom code.

## Out of Scope

| Item | Reason |
| --- | --- |
| Deciding vLLM vs TensorRT-LLM | **DEC-002 (local, pending)** |
| Training or re-training | Phase 2 |
| End-to-end KPI benchmarking (latency, accuracy, ECE) | Phase 4/5 (this phase only exports + measures VRAM/loads) |
| Custom CUDA kernels / speculative decoding | §4.6 optional, measured later; not a Phase 3 prerequisite |
| Cloud/multi-tenant serving | PRD §1.4 |

---

## User Stories

### P1: LoRA merge + engine export ⭐ MVP

**User Story**: As an operator, I want the adapter merged and exported to the serving engine so that inference has no training-time dependencies.

**Why P1**: §4.1 makes merge → export the first performance step; everything else measures this artifact.

**Acceptance Criteria**:

1. WHEN merging THEN the LoRA weights SHALL be merged into the trunk producing one set of weights (§4.1).
2. WHEN exporting THEN the target engine SHALL be the one recorded in **DEC-002** (§4.1); if DEC-002 carries no verdict, work SHALL stop (WS-B-002).
3. WHEN the export completes THEN the artifact SHALL load on the main-path GPU (RTX 3060) with the declared precision (§4 matrix).
4. WHEN the merged model answers THEN its outputs SHALL be equivalent to the pre-merge adapter on a fixed probe set (merge sanity check).

**Independent Test**: load test on 3060 + probe equivalence table.

### P1: Quantization matrix (INT4 / FP8) with VRAM measurement

**User Story**: As an operator, I want quantized variants for each target GPU with measured additional VRAM so that the resource KPI is evidenced, not estimated.

**Why P1**: §7.5 acceptance — ≤ 1.6 GB (bf16) / ≤ 1.0 GB (INT4/FP8), measured in the harness.

**Acceptance Criteria**:

1. WHEN producing variants THEN bf16 (reference), INT4 via **AWQ or GPTQ** for RTX 3060, and FP8 for **NVIDIA L4 (Ada)** SHALL exist per the §4 matrix (FP8 is declared **only** for Ada).
2. WHEN measuring VRAM THEN the number SHALL be **additional** to System-1, measured in the `compare.py` harness style, with GPU declared (§2, §7.5).
3. WHEN a variant misses its bound THEN the measurement SHALL be published as-is (no re-definition of the bound).
4. WHEN precision is selected per GPU THEN the main path (3060) SHALL never depend on FP8 (§8: "caminho principal não depende de Ada").

**Independent Test**: VRAM table with bf16/INT4/FP8 rows, GPU per row, bounds checked.

### P1: Contract integrity after export

**User Story**: As a maintainer, I want proof that the exported artifact still respects the wire contract so that quantization cannot silently break §7.1.

**Acceptance Criteria**:

1. WHEN any exported variant is exercised THEN the wire response SHALL remain schema-valid (`answers` wrapper, `probabilities` summing to 1.0, `noul` in 0..1, `legend` mirroring criteria, §5.1).
2. WHEN the export touches tests THEN `tests/test_contract_wire.py` SHALL remain **unchanged and green** (§1.4).

**Independent Test**: contract suite green against the exported artifact.

### P2: Serving flags — prefix caching & warm-up

**User Story**: As an operator, I want the latency levers of §4 enabled via engine configuration so that Phase 5 measures the tuned path.

**Why P2**: "maior alavanca de latência por linha de config; nos engines de serving é flag, não código" (§4.3).

**Acceptance Criteria**:

1. WHEN the engine is configured THEN prefix caching for the fixed template (`system`/`task`/`questions` shared) SHALL be enabled (§4.3).
2. WHEN warming up THEN captured/warmed shapes SHALL cover the service context (2,048 or the Phase 0 A/B winner) (§4.4).
3. WHEN flags are set THEN they SHALL be recorded as configuration lines in the run/export manifest — not as bespoke code (§4.3–4.4).

**Independent Test**: manifest lists the flags; warm-up shapes documented.

### P3: Speculative decoding experiment (optional)

**User Story**: As an operator, I want speculative decoding evaluated honestly so that it is kept only if it pays.

**Acceptance Criteria**:

1. IF speculative decoding is tried THEN a measurement SHALL be recorded **before** keeping it; with 4–8 output tokens the expected gain is marginal (§4.6) — default is **not** to adopt.

**Independent Test**: either a measurement record exists or the item is marked "not tried".

---

## Edge Cases

- WHEN no Ada/L4 GPU is available THEN FP8 artifacts SHALL be marked "not measured — hardware unavailable" and the main path (3060/INT4) proceeds unaffected (§8).
- WHEN INT4 quantization degrades contract outputs THEN the variant SHALL be rejected in favor of the next viable precision, with the failure recorded.
- WHEN new engine dependencies conflict with the repo's `uv` stack THEN extras SHALL be **opt-in** and recorded in DEC-002 (§8 "novas dependências … extras `serve`/`train`/`fast` já existem como precedente").
- WHEN VRAM includes CUDA context THEN measurement SHALL state methodology (harness, additional to System-1) so the number is comparable (§2 note on the relaxed v1.0 bound).

---

## Requirement Traceability

| Requirement ID | Requirement | PRD | KPI / Criterion | Status |
| --- | --- | --- | --- | --- |
| EXP-01 | LoRA merge into trunk | §4.1 | enables serving | Pending |
| EXP-02 | Export to DEC-002 engine (vLLM or TRT-LLM); stop if the decision has no verdict | §4.1, §6 | §7.6 | Pending |
| EXP-03 | Variants: bf16 / INT4 (AWQ·GPTQ) @3060 / FP8 @L4 — FP8 Ada-only | §4.2 | §7.5 precision matrix | Pending |
| EXP-04 | Additional VRAM ≤ 1.6 GB bf16, ≤ 1.0 GB INT4/FP8, harness-measured, GPU declared | §2, §4 | §7.5 | Pending |
| EXP-05 | Main path independent of Ada/FP8 | §4.2, §8 | robustness of §7.5 | Pending |
| EXP-06 | Contract integrity of exported artifact; contract suite untouched & green | §1.4, §5.1 | §7.1 | Pending |
| EXP-07 | Serving flags (prefix caching, warm-up shapes) recorded in manifest | §4.3, §4.4 | enables §7.3 | Pending |
| EXP-08 | Opt-in extras for new engine deps (uv precedent) | §8 | §7.6 | Pending |
| EXP-09 | Speculative decoding: measure before keep (default: skip) | §4.6 | stretch hygiene | Pending |

**Coverage:** 9 requirements, 0 unmapped.

---

## Verification (Phase 3 exit)

- **Gates:** `ruff check` · `ruff format --check` · `pyright` · `pytest` (incl. contract suite) · `mkdocs build --strict`.
- **Artifacts:** merged weights, per-GPU variants, VRAM table (GPU declared per row), export manifest (engine, precision, flags), probe-equivalence table.
- **Rules:** no invented VRAM numbers; unmeasured combos explicitly marked *(not measured)* (WS-AD-006).

## Success Criteria

- [ ] Artifact loads and answers schema-validly on the RTX 3060 main path.
- [ ] VRAM KPI evidenced for bf16 and at least one of INT4/FP8 within bounds.
- [ ] DEC-002 referenced (not contradicted) for engine + dependency choices.
