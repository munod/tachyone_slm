# Phase 1 — SFT Mixture Data Specification (`Tachyone-SLM-Mixture-v1`)

**Feature ID:** `slm-mixture-data` · **Prefix:** `DAT` · **Phase:** 1 (Days 2–3) · **Status:** Planned
**PRD source:** `docs/tachyone_prd.md` v1.1.0 — §3.3 (dataset), §3.4 (rendering targets), §7.2 (golden-hash / no regression), §8 (contamination risk)

---

## Problem Statement

The SLM needs ~50k SFT pairs whose labels are *derived from the text* and whose prompts are the real wire requests. A parallel ad-hoc dataset would repeat the label-indexing bugs that cost 3 retrains (B-11/B-12) and would risk contaminating the frozen eval sets (L-005). The training signal must come from the **existing** `training/generate_data.py` pipeline — reproducible, byte-idempotent, and audited.

## Goals

- [ ] New pipeline config `training/configs/data_sft_slm.json` producing ≈ **50,000 records** across 7 languages × 5 domains with a pinned seed.
- [ ] Labels derived from text per ADR-0014/ADR-0015 (`noul` phrase bank, `score` tone, `choice` state-named option).
- [ ] Golden-hash idempotence test + deterministic train/val split in `pytest`.
- [ ] Contamination audit proving eval sets never appear in prompts nor in the temperature-fit validation split.
- [ ] SFT rendering: prompt = rendered wire request; target = PRD §3.4 strategy; validation grammar applied at pair generation.

## Out of Scope

| Item | Reason |
| --- | --- |
| Running the LoRA training itself | Phase 2 |
| Temperature scaling fit (uses the split, but is executed later) | Phase 4 (`fit_calibration.py`) |
| Hand-writing a static dataset (`Tachyone-SML-Dataset-v1` was removed in PRD v1.1) | §3.3: use the existing pipeline |
| Changing ADR-0014/ADR-0015 label rules | They "são lei" (§3.3) |

---

## User Stories

### P1: Mixture generation config ⭐ MVP

**User Story**: As a trainer, I want a single pipeline config that generates the SFT mixture reproducibly so that any run can be re-created byte-for-byte.

**Why P1**: Reproducibility (pinned seed, golden hash) is the guard against the variance/labeling lessons (L-005, B-11/B-12).

**Acceptance Criteria**:

1. WHEN the config is committed THEN it SHALL be `training/configs/data_sft_slm.json` with `--languages en,pt,es,fr,de,it,nl` and `--domains support,ecommerce,agent_tools,documents,voice` (§3.3).
2. WHEN the pipeline runs THEN it SHALL produce ≈ **50,000 records** with a **pinned seed** and per-record RNG (§3.3).
3. WHEN the same config + seed run twice THEN the output SHALL be **byte-idempotent** (golden-hash test) and the train/val split SHALL be deterministic (§3.3).
4. WHEN the split is written THEN train/val membership SHALL be stable across runs (same records, same sides).

**Independent Test**: `pytest` golden-hash test passes; two consecutive runs produce identical bytes.

### P1: Labels derived from text

**User Story**: As a trainer, I want every label computed from the record's own text so that indexing bugs cannot re-enter the dataset.

**Why P1**: B-11/B-12 label-indexing bugs cost 3 retrains; ADR-0014/ADR-0015 are binding (§3.3).

**Acceptance Criteria**:

1. WHEN a `noul` label is produced THEN it SHALL come from the **phrase bank** (§3.3).
2. WHEN a `score` label is produced THEN it SHALL be derived from the **tone** of the text (§3.3).
3. WHEN a `choice` label is produced THEN it SHALL be the option **named by the state** (§3.3).
4. WHEN any label cannot be derived THEN the record SHALL be rejected (fail loud) rather than defaulted.

**Independent Test**: spot-check sample records per primitive against the derivation rules; rejection path covered by a test.

### P1: Contamination audit

**User Story**: As a maintainer, I want proof that no eval data leaked into training prompts or into the validation split used for temperature fitting, so that Phase 4/5 numbers mean something.

**Why P1**: L-005 (in-sample synthetic) + the frozen-eval rule are explicit §8 risks.

**Acceptance Criteria**:

1. WHEN generation completes THEN an overlap audit SHALL be recorded showing `eval_en`, `eval_multi`, `eval_en_domains`, `eval_multi_domains` and public probes are **absent** from prompts and from the temperature-fit val split (§3.3).
2. WHEN overlap is found THEN the run SHALL fail (or the records be removed and the audit re-run) — never proceed silently.
3. WHEN the audit is written THEN it SHALL be stored alongside the dataset artifacts as a Phase 1 deliverable (§6 Fase 1).

**Independent Test**: audit artifact exists with a pass result; a seeded-overlap fixture makes the check fail in tests.

### P1: SFT rendering (prompt → target)

**User Story**: As a trainer, I want each record rendered as *(wire request → target)* pairs so that the model learns exactly the contract it will serve.

**Why P1**: §3.3 defines rendering as prompt = rendered wire request, target per §3.4 strategy.

**Acceptance Criteria**:

1. WHEN a record is rendered THEN the prompt SHALL be the **wire request** (state + questions, §5.1 format) — no free-text prompt format of the removed v1.0 (§5.1).
2. WHEN the target is built THEN it SHALL follow the §3.4 scoring strategy for `choice`/`score`/`noul` (or the experimental generation format when that mode is on).
3. WHEN pairs are emitted THEN the grammar/filter of §5.4 SHALL validate them **at generation time**; invalid pairs SHALL be dropped with a count.
4. WHEN rendering covers the dataset THEN all 7 languages and 5 domains SHALL be represented (worst-cell visibility for Phase 2 gating).

**Independent Test**: renderer unit tests for each primitive; invalid-pair fixture rejected by the filter.

### P2: Dataset card / provenance record

**User Story**: As a reviewer, I want a short provenance record for `Tachyone-SLM-Mixture-v1` so that Phase 5's model card can cite the training data exactly.

**Acceptance Criteria**:

1. WHEN Phase 1 closes THEN a provenance note SHALL exist: config name, seed, record count, languages, domains, split sizes, audit result — consumed later by `docs/model-card.md`.

**Independent Test**: provenance note exists and matches the config.

---

## Edge Cases

- WHEN a domain/language cell has too few records THEN the generation report SHALL show per-cell counts (Phase 2 gates on the **worst** cell, §3.2).
- WHEN the pipeline version changes THEN the golden hash SHALL change **only** with an explicit, reviewed config change (never silently).
- WHEN `criteria` options exceed the wire limits (up to 255 `options`, §3.4) THEN rendering SHALL keep them intact (scoring cost is stable by design).
- WHEN a record's state mentions no option for a `choice` question THEN label derivation SHALL reject it (B-11/B-12 guard).

---

## Requirement Traceability

| Requirement ID | Requirement | PRD | KPI / Criterion | Status |
| --- | --- | --- | --- | --- |
| DAT-01 | Config `data_sft_slm.json`: 7 languages, 5 domains, ≈50k, pinned seed | §3.3 | enables G4 accuracy | Pending |
| DAT-02 | Labels from text (phrase bank / tone / state-named option) per ADR-0014/0015 | §3.3 | no-regression (§7.2) | Pending |
| DAT-03 | Byte-idempotent output (golden-hash) + deterministic split + per-record RNG | §3.3 | §7.2 golden-hash intact | Pending |
| DAT-04 | Contamination audit vs eval sets + probes; fail on overlap | §3.3, §8 | validity of §7.2/§7.4 | Pending |
| DAT-05 | SFT rendering: wire-request prompt → §3.4 target | §3.3, §3.4 | enables §7.1 (`JSON ok`) | Pending |
| DAT-06 | §5.4 grammar/filter applied at pair generation | §3.3, §5.4 | §7.1 | Pending |
| DAT-07 | Per-cell (language × domain) counts reported | §3.2 | worst-cell gating (§7.2) | Pending |
| DAT-08 | Provenance record for model card | §3.3 | §7.6 publication set | Pending |

**Coverage:** 8 requirements, 0 unmapped.

---

## Verification (Phase 1 exit)

- **Gates:** `ruff check` · `ruff format --check` · `pyright` · `pytest` (includes golden-hash + renderer + audit tests) · `mkdocs build --strict` (PRD §6).
- **Artifacts:** generated mixture, golden-hash test green, contamination audit record, per-cell counts, provenance note.
- **Regression check:** dataset golden-hashes of **existing** eval assets remain intact (§7.2).

## Success Criteria

- [ ] ≈50k records generated deterministically from one config with pinned seed.
- [ ] Golden-hash test and contamination audit green in CI.
- [ ] Every SFT pair validated against the §5.4 grammar at generation time.
- [ ] No eval-set leakage (audit record attached).
