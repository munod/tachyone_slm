# Phase 5 — Benchmark & Publication Specification

**Feature ID:** `slm-benchmark-docs` · **Prefix:** `DOC` · **Phase:** 5 (Days 9–10) · **Status:** Planned
**PRD source:** `docs/tachyone_prd.md` v1.1.0 — §2 (KPI table + protocol), §5.2 (measure both engine modes), §6 Fase 5, §7 (all acceptance criteria), §8 (stretch risk), §9 (traceability)

---

## Problem Statement

Nothing counts until it is measured under the repository's own protocol and published. Phase 5 is where every KPI of §2 becomes an evidenced number (GPU declared, protocol-compliant) and where the English publication set ships **as one unit** — the AD-009 pattern — so that `AGENTS.md` gates and §7.6 process criteria are satisfied.

## Goals

- [ ] New SLM engine row in `benchmarks/compare.py` (the 4 existing rows remain the yardstick).
- [ ] All §2 KPIs measured and published with GPU + method declared.
- [ ] Embedded local engine vs external servers (vLLM/TRT-LLM) measured side by side.
- [ ] English doc set updated as a set: ADR-0017, `docs/cookbook-handoff.md`, `README`, `docs/model-card.md`, `CHANGELOG.md`, `benchmarks/report.md`.
- [ ] PRD §7 checklist fully evidenced; PRD §2 targets confirmed (or honestly revised with data).

## Out of Scope

| Item | Reason |
| --- | --- |
| JevBench submission with the SLM | §1.4 — encoder artifact; composition is future work |
| Changing KPI definitions after seeing results | Targets fixed in Phase 0 (§6); revisions need maintainer review |
| Publishing `< 8 ms` as a promise | §8: stretch is measured, not promised |
| Training/data changes | Phases 1–2 (a miss is reported, not retrained ad hoc here) |

---

## User Stories

### P1: Engine row + full KPI measurement ⭐ MVP

**User Story**: As a maintainer, I want the SLM measured in the same harness as the 4 existing rows so that comparisons are apples-to-apples.

**Why P1**: §7 acceptance is entirely evidence-based.

**Acceptance Criteria**:

1. WHEN the row is added THEN `benchmarks/compare.py` SHALL include the SLM engine **without modifying the metric implementation or data rows** of the existing rows (§2 protocol).
2. WHEN any number is published THEN it SHALL follow: sequential, batch=1, warm-up excluded, same data rows, same metric implementation, **GPU declared next to the number** (§2).
3. WHEN latency is measured THEN p50 **< 20 ms** and p95 **< 50 ms** in-engine SHALL be evidenced (§7.3); the stretch `< 8 ms` SHALL appear **only** if FP8@L4 + minimal-output preconditions of §4 hold, and SHALL be labeled *stretch* (§7.3).
4. WHEN relative speed is measured THEN **≥ 50×** `ornith-9b` p50 in the same harness SHALL be reported against the reference 3,315 ms (home) / 6,844 ms (probe) (§2).
5. WHEN throughput is measured THEN **≥ 20 items/s** (batch=1) SHALL be evidenced (§2, §7.5).
6. WHEN contract compliance runs THEN `JSON ok` SHALL be **1.000 on both sets** (§7.1).
7. WHEN accuracy runs THEN slice accuracy (τ=0.6) vs the Phase 0 fixed targets **and** composite accuracy ≥ System-1-only (references `eval_en` 1.000 · `eval_multi` 0.895 · five-domain 0.9975) SHALL be reported (§2, §7.2), with no regression and dataset golden-hashes intact.
8. WHEN calibration is reported THEN **ECE (10-bin, fitted) + Brier + `Conf`** SHALL appear together, ECE ≤ 0.030 (§7.4).
9. WHEN resources are measured THEN additional VRAM ≤ **1.6 GB** (bf16) / ≤ **1.0 GB** (INT4/FP8) SHALL be evidenced in-harness (§7.5) and handoff coverage **100%** reported (§7.2).

**Independent Test**: a `benchmarks/report.md` table where every §2 row has a measured value + GPU + protocol note.

### P1: Publication set as one unit

**User Story**: As a maintainer, I want every doc surface updated together so that the repo never ships contradictory claims (AD-009).

**Why P1**: §7.6 process criterion.

**Acceptance Criteria**:

1. WHEN Phase 5 closes THEN **ADR-0017**, `docs/cookbook-handoff.md`, `README`, `docs/model-card.md`, `CHANGELOG.md` and `benchmarks/report.md` SHALL be updated **as a set** (§7.6, AD-009).
2. WHEN docs are written THEN they SHALL be in **English** (§6 gate) except the PRD, which remains Portuguese (DEC-004).
3. WHEN processes are checked THEN conventional commits and all daily gates SHALL be green (`ruff check`, `ruff format --check`, `pyright`, `pytest`, `mkdocs build --strict`) (§6).

**Independent Test**: PR checklist shows the 6 surfaces touched in the same change set; gates green.

### P1: Model card completion

**User Story**: As a downstream user, I want a complete model card so that I know what this SLM is, what it was trained on, and how it behaves.

**Acceptance Criteria**:

1. WHEN Phase 5 completes THEN every `TODO(Phase 5)` / `to be measured` placeholder in `docs/model-card.md` SHALL be replaced with measured/cited content (§7.6).

**Independent Test**: no `TODO(Phase …)` markers remain in `docs/model-card.md`.

### P2: Embedded vs external engine comparison

**User Story**: As an operator, I want both serving modes measured so that the default (embedded) is a data-backed choice.

**Why P2**: §5.2 — "motor local embarcado … com servidores externos (vLLM/TRT-LLM) como opcional — medir ambos na Fase 5".

**Acceptance Criteria**:

1. WHEN both modes run THEN p50/p95/`JSON ok`/VRAM SHALL be reported for each; if the external engine wins materially, the recommendation SHALL be recorded in the report (§5.2).

**Independent Test**: two-column comparison exists.

### P2: Honest miss reporting

**User Story**: As a maintainer, I want misses reported plainly so that the PRD can "registrar o resultado e reavaliar o papel" (§8).

**Acceptance Criteria**:

1. WHEN a KPI misses its target THEN the report SHALL publish the measured value, the target and the gap — without re-defining the target; PRD §2 SHALL be updated only with maintainer review.
2. WHEN the stretch is not met or not measurable on available hardware THEN it SHALL be recorded as *not met / not measured* (§8, WS-AD-006).

**Independent Test**: report contains a misses section (or an explicit "none").

---

## Edge Cases

- WHEN hardware for FP8 (Ada) is unavailable during Phase 5 THEN stretch results SHALL be marked *not measured — hardware unavailable*; main-path KPIs proceed on 3060 (§8).
- WHEN the harness result differs from Phase 4's internal test THEN the harness number is authoritative (§2 protocol rule).
- WHEN a doc surface has no change to publish (e.g., ADR-0017 already final) THEN the set-update SHALL still touch/confirm it (AD-009).
- WHEN `mkdocs build --strict` fails on a new page's nav entry THEN `mkdocs.yml` SHALL be updated in the same change (WS-B-013).

---

## Requirement Traceability

| Requirement ID | Requirement | PRD | KPI / Criterion | Status |
| --- | --- | --- | --- | --- |
| DOC-01 | New engine row in `compare.py`, existing rows/protocol untouched | §2, §6 | all §2 rows | Pending |
| DOC-02 | p50 < 20 ms / p95 < 50 ms; stretch < 8 ms only with §4 preconditions | §4, §7.3 | G1 latency | Pending |
| DOC-03 | ≥ 50× `ornith-9b` p50; ≥ 20 items/s | §2, §7.3, §7.5 | G2 speed/throughput | Pending |
| DOC-04 | `JSON ok` = 1.000 on both sets | §2, §7.1 | G3 contract | Pending |
| DOC-05 | Slice accuracy vs Phase 0 targets; composite ≥ System-1-only; no regression; golden-hashes intact | §2, §7.2 | G4 accuracy | Pending |
| DOC-06 | ECE ≤ 0.030 with Brier + `Conf` | §2, §7.4 | G5 calibration | Pending |
| DOC-07 | VRAM ≤ 1.6 GB bf16 / ≤ 1.0 GB INT4·FP8; 100% handoff coverage | §2, §7.2, §7.5 | G6 resources | Pending |
| DOC-08 | Embedded vs external engine comparison | §5.2 | serving choice | Pending |
| DOC-09 | English publication set updated as a set (6 surfaces) | §6, §7.6 | G7 process | Pending |
| DOC-10 | Model card placeholders filled | §7.6 | G7 | Pending |
| DOC-11 | Honest miss/stretch reporting (no re-defined targets) | §8, §9 | integrity of all KPIs | Pending |

**Coverage:** 11 requirements, 0 unmapped.

---

## Verification (Phase 5 exit — PRD §7 checklist)

| §7 | Evidence required |
| --- | --- |
| 7.1 | `JSON ok` = 1.000, both sets, report table |
| 7.2 | Coverage 100%; slice + composite accuracy tables; `eval_en` = 1.000; golden-hashes intact |
| 7.3 | p50/p95 + ≥50× table with GPU/method; stretch labeled |
| 7.4 | ECE/Brier/`Conf` triple |
| 7.5 | VRAM + throughput rows |
| 7.6 | ADR-0017 published; gates green; 6-surface publication set |

**Gates:** `ruff check` · `ruff format --check` · `pyright` · `pytest` · `mkdocs build --strict` · conventional commits · English docs (§6).

## Success Criteria

- [ ] Every §2 row has a measured number with GPU declared — no placeholders left in the report.
- [ ] The 6-surface doc set ships together; `docs/model-card.md` fully filled.
- [ ] All §7 criteria evidenced or explicitly, honestly marked as missed.
