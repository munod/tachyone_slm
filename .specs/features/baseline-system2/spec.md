# Phase 0 — Baseline System-2 Specification

**Feature ID:** `baseline-system2` · **Prefix:** `BSL` · **Phase:** 0 (Day 1) · **Status:** ✅ Complete (2026-10-03)
**PRD source:** `docs/tachyone_prd.md` **v1.2.0** — §2 (KPIs), §3.1 (context), §6 Fase 0, §7.2 (acceptance), §8 (risk "slice may not improve")
**Evidence:** `docs/phase0-baseline.md` + 24 artifacts in `benchmarks/results/phase0_*.json` (RTX 3060, 2026-10-03)

---

## Problem Statement

The accuracy KPI for the abstained slice read *"a medir (Fase 0)"*, so PRD v1.1.0 could not leave review (§ Status line) and acceptance criterion §7.2 had no number to check against — and the "0.5B may not beat the slice" risk (§8) had to be quantified **before** training, not after. **Resolved 2026-10-03:** the measurement ran, PRD §2 carries fixed targets (v1.2.0), and this spec's 7 requirements are delivered (see Evidence in the header).

## Goals

- [x] Measure System-1 and both LLM candidates (`ornith-9b`, `ling-tiny`) on the slice `confidence < τ` of the eval sets, under the `benchmarks/compare.py` protocol. *(Also measured: the SLM base `qwen2.5:0.5b` — the actual System-2 candidate — on the same slices.)*
- [x] Fix the exact numeric accuracy targets in PRD §2 (replace "a medir (Fase 0)"). *(→ PRD v1.2.0 §2: `≥0.723` LLM candidate / `≥0.474` System-1, anchor `eval_multi_domains` n=264.)*
- [x] Decide the service context (2,048 vs 4,096 tokens) by A/B on the abstained slice. *(→ 2,048 — WS-AD-007.)*

## Out of Scope

| Item | Reason |
| --- | --- |
| SLM training / data generation / export | Phases 1–3 |
| Any modification of the eval sets | Frozen-eval rule (§8 contamination risk) |
| System-1 retraining or encoder changes | PRD §1.4 non-goal |
| Publishing new KPI numbers not derived from this run | No invented metrics (WS-AD-006) |

---

## User Stories

### P1: Abstained-slice baseline measurement ⭐ MVP

**User Story**: As a project maintainer, I want System-1 and the LLM candidates measured on the same abstained slice so that Phase 0 can fix numeric accuracy targets before any training starts.

**Why P1**: The PRD is explicitly "não aprovado até a Fase 0 fixar os alvos numéricos de acurácia" — every downstream gate depends on it.

**Acceptance Criteria**:

1. WHEN the harness runs THEN every number SHALL follow the §2 protocol: sequential, batch=1, warm-up excluded, same data rows, same metric implementation, **GPU declared next to the number**.
2. WHEN the slice is defined THEN it SHALL be the eval-set items with `confidence < τ`, **τ = 0.6** (reference value of §2), and the slice **size (denominator)** SHALL be recorded per eval set.
3. WHEN baselines are produced THEN System-1 accuracy, `ornith-9b` accuracy and `ling-tiny` accuracy on the **same slice** SHALL be reported side by side (§2 row "Acurácia no slice abstido").
4. WHEN the run completes THEN the measured numbers SHALL be written into PRD §2, replacing "a medir (Fase 0)" with fixed targets, and the Phase 0 output SHALL be registered in `.specs/project/STATE.md`.
5. WHEN a candidate fails the wire contract during measurement THEN the failure SHALL be recorded in the row (never silently dropped) — evidence rule of B-10/§7.1.

**Independent Test**: PRD §2 no longer contains "a medir"; a Phase 0 report exists with slice sizes + GPU per number.

### P1: Service context A/B (2,048 vs 4,096)

**User Story**: As a maintainer, I want the service-context candidate decided by measurement so that the truncation weakness of B-13/P0 is not repeated while latency stays within KPI.

**Why P1**: Context size drives prefill cost (p50 < 20 ms) and coverage of hard states (avg 1,079 tokens) simultaneously (§3.1, §1.3).

**Acceptance Criteria**:

1. WHEN both context candidates are evaluated on the abstained slice THEN accuracy and latency SHALL be reported for each, under the §2 protocol.
2. WHEN a winner is chosen THEN the decision SHALL be recorded (PRD §3.1 note + `.specs/project/STATE.md`) with the numbers that justified it.
3. WHEN neither candidate meets p50 < 20 ms THEN the result SHALL be reported as-is — the hypothesis is measured, not assumed (§3.1: "hipótese a medir, não premissa").

**Independent Test**: an A/B table exists with a recorded, justified choice.

### P2: Composite-accuracy yardstick

**User Story**: As a maintainer, I want the System-1-only reference numbers recorded for the composite gate so that Phase 4/5 can prove "≥ System-1-only" without re-deriving it.

**Why P2**: §7.2 requires no-regression evidence (`eval_en` 1.000, `eval_multi` 0.895, five-domain 0.9975 — §2).

**Acceptance Criteria**:

1. WHEN Phase 0 closes THEN the System-1-only references from `benchmarks/report.md` SHALL be recorded as the composite yardstick (§2 row "Acurácia composta").

**Independent Test**: yardstick numbers present in the Phase 0 report.

---

## Edge Cases

- WHEN the abstained slice is empty or tiny for a given eval set THEN the report SHALL record the slice size and flag it instead of publishing a percentage without denominator.
- WHEN τ produces a slice too large (> reasonable share) or too small THEN the report SHALL state the τ used and the resulting coverage, keeping τ = 0.6 as the reference unless the maintainer changes it (§5.3).
- WHEN hardware differs between runs (3060 vs L4) THEN each number SHALL declare its GPU (§2).
- WHEN measurement itself fails for a candidate THEN the failure SHALL be reported as a data point, not omitted.

---

## Requirement Traceability

| Requirement ID | Requirement | PRD | KPI / Criterion | Status |
| --- | --- | --- | --- | --- |
| BSL-01 | Harness protocol compliance for every number | §2 | all §2 rows | ✅ Done — `compare.py` protocol; datasets re-validated against golden hashes (46/46); GPU declared in every artifact; deviations listed in report §5 |
| BSL-02 | Slice definition `confidence < τ` (τ=0.6) + slice sizes recorded | §2 | Acurácia no slice abstido | ✅ Done — 1 / 4 / 18 / **264** (τ sweep 0.30–0.95 also recorded; tiny slices flagged per edge case) |
| BSL-03 | Baselines: System-1 vs `ornith-9b` vs `ling-tiny` on the same slice | §1.3, §2 | Acurácia slice (baseline) | ✅ Done — `eval_multi_domains` (n=264): 0.723 / 0.474 / 0.311 (+ SLM base 0.098) |
| BSL-04 | Fix exact numeric targets in PRD §2; unblock PRD approval | § Status, §6 Fase 0 | Acurácia slice → §7.2 | ✅ Done — PRD **v1.2.0** §2/§3.1/§6/§7.2/§8 updated; approval itself tracked as WS-B-015 |
| BSL-05 | Context A/B 2,048 vs 4,096 on the slice | §3.1 | enables p50 < 20 ms (§7.3) | ✅ Done — tie by construction (0 rows > 2,048 tok) → **2,048** (WS-AD-007) |
| BSL-06 | Composite yardstick (System-1-only) recorded | §2 | Acurácia composta → §7.2 | ✅ Done — 1.000 / 1.000 / 0.895 / 0.997 from `benchmarks/report.md` |
| BSL-07 | Contract failures of candidates recorded, not dropped | §7.1 | `JSON ok` evidence | ✅ Done — `JSON ok`: 1.000 (System-1) · 0.947 (ornith) · 0.561 (ling) · 0.466 (SLM base) |

**Coverage:** 7 requirements, all mapped to PRD sections, 0 unmapped. **7/7 delivered.**

---

## Verification (Phase 0 exit)

- **Artifacts:** ✅ Phase 0 measurement report `docs/phase0-baseline.md` (numbers + GPU + slice sizes + τ + deviations §5), PRD §2 updated (v1.2.0), context decision in `STATE.md` (WS-AD-007/008).
- **Gates:** `ruff check` · `ruff format --check` · `pyright` · `pytest` · `mkdocs build --strict` — green for anything touched (PRD §6). *This workspace ships no product code; `pytest tests/test_training_generate.py` 46/46 green on the datasets used (data integrity).*
- **Rule:** any metric not obtained in this run stays written as **"to be measured (Phase 0)"** (WS-AD-006) — no fabricated baselines. **Honoured:** only rows measured in this run carry numbers.

## Success Criteria

- [x] PRD §2 shows exact numeric accuracy targets for the abstained slice (placeholder gone).
- [x] System-1 + 2 LLM candidates measured on the identical slice with GPU declared. *(+ the SLM base itself.)*
- [x] Service context (2,048 or 4,096) chosen with evidence. *(2,048 — tie by construction.)*
- [x] Composite yardstick recorded for §7.2.
