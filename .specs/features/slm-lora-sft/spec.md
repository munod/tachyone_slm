# Phase 2 — LoRA / SFT Training Specification

**Feature ID:** `slm-lora-sft` · **Prefix:** `SFT` · **Phase:** 2 (Days 4–5) · **Status:** Planned — **gated by DEC-002 (local stack decision) + FROZEN by WS-B-022 until JevBench #182 closes**
**PRD source:** `docs/tachyone_prd.md` **v2.0.0** — §3.1 (base/context), §3.2 (training tactic), §6 Fase 2, §7.2 (no regression), §8 (variance / English regression risks)

---

## Problem Statement

The base model must be fine-tuned into a System-2 answerer that beats the Phase 0 slice targets **without** regressing `eval_en` (1.000) — on a single consumer GPU, in ~4–12 h, with a training loop whose own non-determinism already produced 0.76–0.79 on the same seed (L-005/L-006). The training stack choice itself is an open decision recorded **locally as DEC-002** — PRD v2.0 removed the upstream-ADR requirement because training code lives in *this* repo and `munod/tachyone` is read-only (`WS-AD-010`) — and it **must be recorded before any training code is written** (§6 Fase 2).

## Goals

- [ ] Stack decision recorded as **DEC-002 (local)** before training code exists.
- [ ] LoRA/SFT run with the hyperparameters frozen in §3.2, effective batch declared, pinned seed.
- [ ] Early stopping on `eval_en` **+** the abstained slice; gating on the worst domain/language.
- [ ] Checkpoint + eval report showing slice accuracy vs the Phase 0 target and no `eval_en` regression.

## Out of Scope

| Item | Reason |
| --- | --- |
| Choosing the training/export stack (decision content) | **DEC-002** (local, pending; upstream ADR-0017 out of scope since PRD v2.0) |
| Re-training or touching System-1 | PRD §1.4 |
| Export / quantization / serving | Phase 3 |
| Models ≥ 1B, MoE adapters | PRD §1.4 |
| Re-running data generation | Phase 1 (input is frozen for this phase) |

---

## User Stories

### P1: LoRA SFT run with frozen hyperparameters ⭐ MVP

**User Story**: As a trainer, I want the fine-tune executed exactly with the §3.2 recipe so that results are comparable and reproducible.

**Why P1**: This phase produces the artifact every later phase measures.

**Acceptance Criteria**:

1. WHEN training starts THEN **DEC-002** SHALL be recorded in this repo (§6 Fase 2 — hard gate; no upstream artifact, `WS-AD-010`).
2. WHEN configured THEN LoRA SHALL target `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj` in **bfloat16** with `r = 16`, `α = 32`, dropout `0,05`, LR `2e-4` + Cosine Decay, **effective batch 32 declared** (gradient accumulation), AdamW, 3–5 epochs (§3.2).
3. WHEN early stopping triggers THEN it SHALL consider `eval_en` **and** the abstained slice (§3.2).
4. WHEN the run ends THEN the checkpoint, the exact config, the seed and the metrics per epoch SHALL be recorded as run artifacts.
5. WHEN GPU time elapses THEN the run SHALL fit the estimated **~4–12 h** envelope (§6); an overrun SHALL be reported, not hidden.

**Independent Test**: run manifest exists with config hash + seed; config matches §3.2 line by line.

### P1: Experiment discipline enforced

**User Story**: As a maintainer, I want the repo's experiment discipline applied mechanically so that we never conclude from noise or a mis-configured run.

**Why P1**: L-006 (0.76–0.79 at same seed), L-011 (config mismatch), L-013 (routed harness) are recorded failures (§3.2).

**Acceptance Criteria**:

1. WHEN a run starts THEN the seed SHALL be **pinned** (AD-009) and the launch config SHALL be verified identical to the experiment config before running (L-011).
2. WHEN a metric moves THEN conclusions SHALL require a **control** run first — variance is never blamed without it (L-006).
3. WHEN gating THEN the **worst** domain/language SHALL be used, never the average (§3.2).
4. WHEN evaluating THEN the adapter SHALL be **explicit** — never a routed harness (L-013).
5. WHEN comparing runs THEN non-determinism of the loop SHALL be acknowledged (expected spread 0.76–0.79 on same seed) in the report.

**Independent Test**: report contains control-vs-experiment comparison and worst-cell numbers.

### P1: No-regression guard on English

**User Story**: As a maintainer, I want `eval_en` protected during fine-tuning so that the fix for System-2 does not break System-1 quality expectations.

**Why P1**: §8 lists "regressão em inglês por fine-tuning" with the B-11/B-12 retrain history.

**Acceptance Criteria**:

1. WHEN validation runs during training THEN `eval_en` SHALL be tracked each epoch; a drop below **1.000** SHALL stop or flag the run (early stopping, §3.2).
2. WHEN the final checkpoint is chosen THEN it SHALL not regress `eval_en` relative to the baseline recorded in Phase 0 (§7.2).

**Independent Test**: per-epoch `eval_en` series present; selected checkpoint passes the no-regression check.

### P2: VRAM-safe optimizer fallback

**User Story**: As a trainer on the RTX 3060, I want an 8-bit optimizer option so that training fits 12 GB without changing the recipe's semantics.

**Why P2**: §3.2 allows bitsandbytes 8-bit AdamW "se a 3060 apertar".

**Acceptance Criteria**:

1. WHEN full-precision AdamW does not fit THEN the run MAY switch to 8-bit AdamW, and the switch SHALL be recorded in the run manifest (§3.2).

**Independent Test**: manifest records which optimizer was used.

### P2: Slice-vs-target readout

**User Story**: As a maintainer, I want the trained model's abstained-slice accuracy compared directly against the Phase 0 fixed target so that go/no-go for Phase 4 is explicit.

**Acceptance Criteria**:

1. WHEN eval completes THEN slice accuracy SHALL be reported next to the Phase 0 target and to the LLM/System-1 baselines (§2), with the same τ = 0.6 and the same metric implementation.
2. WHEN the target is missed THEN the report SHALL state it plainly (§8: "se não ganhar, o PRD registra o resultado e reavalia o papel").

**Independent Test**: readout table exists with target vs measured.

---

## Edge Cases

- WHEN the same seed yields different metrics across reruns THEN the control rule (L-006) applies before any conclusion.
- WHEN a run OOMs on the 3060 THEN batch stays 32 **effective** via accumulation — effective batch is never silently reduced (§3.2).
- WHEN the abstained slice shrinks/changes after Phase 0 THEN the same slice definition (τ, sets) SHALL be reused for comparability.
- WHEN training data changes mid-phase THEN the Phase 1 golden hash SHALL be re-verified first (L-011 guard).

---

## Requirement Traceability

| Requirement ID | Requirement | PRD | KPI / Criterion | Status |
| --- | --- | --- | --- | --- |
| SFT-01 | Stack decision (DEC-002) recorded before training code | §4.1, §6 Fase 2 | §7.6 (process) | Pending — frozen by WS-B-022 |
| SFT-02 | LoRA recipe frozen (modules, r, α, dropout, LR+cosine, batch 32 effective, AdamW, 3–5 ep) | §3.2 | enables G4 | Pending |
| SFT-03 | Early stopping on `eval_en` + abstained slice | §3.2 | §7.2 no regression | Pending |
| SFT-04 | Discipline: pinned seed, config verification, control-first, worst-cell gating, explicit adapter | §3.2 | validity of §7.2 | Pending |
| SFT-05 | `eval_en` no-regression guard (stays 1.000) | §7.2 | §7.2 | Pending |
| SFT-06 | Slice accuracy readout vs Phase 0 target (τ=0.6, same metric) | §2, §8 | Acurácia slice → §7.2 | Pending |
| SFT-07 | Run manifest: config hash, seed, per-epoch metrics, optimizer variant | §3.2 (AD-009, L-011) | §7.6 | Pending |
| SFT-08 | Optional 8-bit AdamW recorded if used | §3.2 | resource envelope | Pending |

**Coverage:** 8 requirements, 0 unmapped.

---

## Verification (Phase 2 exit)

- **Hard gate:** DEC-002 recorded in this repo **and** the JevBench freeze lifted (else STOP — WS-B-022).
- **Gates:** `ruff check` · `ruff format --check` · `pyright` · `pytest` · `mkdocs build --strict`.
- **Artifacts:** checkpoint/adapter, run manifest (config + seed), per-epoch metrics, control-vs-experiment comparison, worst-cell table, slice-vs-target readout.
- **Numeric honesty:** slice target values are those fixed in Phase 0 — never re-guessed here (WS-AD-006).

## Success Criteria

- [ ] Adapter trained with the frozen §3.2 recipe, reproducible from the manifest.
- [ ] `eval_en` not regressed; slice accuracy vs Phase 0 target reported (pass or honest fail).
- [ ] Worst domain/language reported; no routed-harness numbers anywhere.
