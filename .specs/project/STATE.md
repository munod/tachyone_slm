# State

**Last Updated:** 2026-10-04
**Current Work:** **Phase 1 delivered** — `Tachyone-SLM-Mixture-v1` (50,180 clean SFT pairs, audit pass, 16 tests green); next: **ADR-0017 gate** then Phase 2 training (PRD §6)

> **ID convention:** decisions/blockers/lessons created **in this workspace** use the `WS-` prefix (`WS-AD-NNN`, `WS-B-NNN`, `WS-L-NNN`) so they never collide with the canonical `AD-009`, `B-5…B-13`, `L-005…L-016` IDs owned by the upstream repository `munod/tachyone` (see PRD §10). Upstream IDs are **referenced, not duplicated**.

---

## Recent Decisions (Last 60 days)

### WS-AD-001: Specs live in `.specs/` (2026-10-03)

**Decision:** Use `.specs/` (hidden dir), not `specs/`.
**Reason:** skill `tlc-spec-driven` canonical layout **and** the upstream `munod/tachyone` repo already uses `.specs/project/BACKLOG.md`, `.specs/project/STATE.md`, `.specs/features/...` (PRD §10) — same paths keep the workspace merge-compatible with the target repo.
**Trade-off:** hidden directory is less discoverable for newcomers (mitigated by `README.md` links).
**Impact:** all specs, roadmap and state files follow `.specs/`.

### WS-AD-002: New documentation in English (2026-10-03)

**Decision:** All new docs in this workspace (`README`, `CHANGELOG`, `CONTRIBUTING`, `docs/**`, `.specs/**`) are written in **English**; the PRD (`docs/tachyone_prd.md`) stays in **Portuguese** as the product source of truth.
**Reason:** PRD §6 gate — "conventional commits · docs/PRs em inglês" (`AGENTS.md`/`CONTRIBUTING.md`).
**Trade-off:** two languages coexist in one repo; readers must switch.
**Impact:** language policy made explicit in `README.md` and `CHANGELOG.md` (task requirement).

### WS-AD-003: Default decoding = candidate scoring (2026-10-03)

**Decision:** The default answer construction is **scoring of candidates** (logprobs → softmax/sigmoid), not free generation, for `choice`, `score` and `noul`; constrained generation is an experimental opt-in in Phase 4.
**Reason:** recorded in PRD v1.1.0 §3.4 — compliance by construction, native distributions for the wire invariants, stable cost even with 255 `options`, coherent with the "single forward pass" identity. Evidence: B-10 measured 46 s per 52-option free-generation attempt.
**Trade-off:** no free-form reasoning by default; the hard slice can only benefit from it in the experimental mode.
**Impact:** SFT targets render as scoring pairs (§3.4); `probabilities`/`confidence` always come from logits + temperature fit — never generated text.
**Recorded in:** `docs/decisions/decoding-strategy.md` (DEC-001).

### WS-AD-004: ADR-0017 (training/export stack) is PENDING — planned, not drafted here (2026-10-03)

**Decision:** The stack decision (LoRA training stack; vLLM vs TensorRT-LLM export; extras `serve`/`train`/`fast`) is **not** decided in this workspace. ADR-0017 will be published in `munod/tachyone` during Phases 2–3 (PRD §4.1, §6). This workspace only records its *planned* status and decision criteria.
**Reason:** task scope forbids writing an ADR as if it were upstream; and PRD §6 says "ADR-0017 antes de codar".
**Trade-off:** Phase 2 cannot start until it exists (tracked as blocker WS-B-002).
**Impact:** `.specs/features/slm-lora-sft` and `slm-export-quant` have a hard prerequisite.
**Recorded in:** `docs/decisions/training-export-stack.md` (DEC-002).

### WS-AD-005: This workspace stays documentation-only (2026-10-03)

**Decision:** No `git init`, no commits, no `.py` files, no training/benchmark runs here — even though the folder is not a git repo yet. `.gitignore` is pre-created so a later `git init` starts clean.
**Reason:** explicit task scope; product code belongs to `munod/tachyone`.
**Trade-off:** nothing runnable exists here yet.
**Impact:** `tasks.md` files (skill Tasks phase) are deferred to the implementation repo; `docs/architecture.md` serves as the architecture reference instead.
**Status:** **superseded 2026-10-03** — the maintainer explicitly requested the Phase 0 run (measurement tooling now lives in `benchmarks/phase0_*.py|sh`, product code still untouched) and provided a dedicated remote (`munod/tachyone_slm`), so `git init` + the first commit happened. The "product code belongs upstream" half of the decision remains in force.

### WS-AD-006: No invented metrics — placeholders instead (2026-10-03)

**Decision:** Every metric the PRD marks as *a medir (Fase 0)* or not yet measured is written as **"to be measured (Phase 0/5)"** — never as a number.
**Reason:** PRD v1.1.0 changelog removed v1.0 numbers that did not reproduce; fabricating baselines would repeat that failure.
**Trade-off:** docs read less "complete".
**Impact:** `docs/model-card.md`, `docs/plan.md`, feature specs all use placeholders.
**Status:** superseded **only** for the Phase 0 rows, which are now measured (WS-AD-007/008); every other placeholder stays until its own phase runs.

### WS-AD-007: Service context = 2,048 tokens — decided by measurement (2026-10-03)

**Decision:** The SLM service context is **2,048 tokens** (PRD §3.1 updated); 4,096 is dropped.
**Reason:** Phase 0 A/B on the abstained slice was a **tie by construction**: accuracy 0.212 = 0.212, `JSON ok` 0.958 = 0.958, p50 276.2 vs 276.3 ms — because **0 of 18,000 rows across the four eval sets exceed 2,048 tokens** (max 1,360 including the 418-token system prompt).
**Trade-off:** if a future eval set (or the JevBench hard tier) brings >2k-token inputs, 2,048 must be revisited — the measurement says nothing about data the eval sets do not contain.
**Impact:** KV-cache sized for 2,048 (PRD §3.1); re-measure if the input distribution changes.

### WS-AD-008: Slice-accuracy target anchored on `eval_multi_domains` (2026-10-03)

**Decision:** The §2 slice-accuracy target (`≥0.723` LLM candidate, `≥0.474` System-1) is anchored on **`eval_multi_domains`, n = 264** at τ = 0.6; `eval_multi` (n = 18) is secondary and `eval_en` / `eval_en_domains` (n = 1 / 4) carry **no publishable target**.
**Reason:** measured slice sizes — System-1 is near-certain on the in-sample English sets (mean confidence 0.99–0.994, p50 = 1.0), so τ = 0.6 barely abstains there.
**Trade-off:** the anchor set is multilingual five-domain; English-specific behaviour of the abstained slice stays unmeasured (alternatives recorded in PRD §8: higher τ — sweep 0.3–0.95 in `docs/phase0-baseline.md` §1 — or harder eval sets).
**Impact:** PRD §2, §7.2; Phase 4/5 acceptance runs against this denominator.

### WS-AD-009: Contamination handling = dedup + raw/clean file naming (2026-10-04)

**Decision:** Raw generation is written to `data/*.raw.jsonl`; the canonical `tachyone_slm_mixture_v1.jsonl` name belongs to the **deduplicated** dataset. Records matching a frozen eval set by *state text* or *prompt fingerprint* are removed **before** split and rendering, then the audit is re-run.
**Reason:** the phrase banks are shared between our mixture and the frozen sets, so a distinct seed is not enough — **41.31%** of raw records collide (measured 2026-10-03). DAT-04 AC2 sanctions exactly this remedy ("records be removed and the audit re-run — never proceed silently").
**Trade-off:** `per_type` had to rise 3333 → **5700** (85,500 raw) to land ≈50k clean; 41% of generation is discarded and `noul` loses most (its states are the most templated → 13,607 pairs left).
**Impact:** `training/configs/data_sft_slm.json`, `slm_pipeline/prepare_sft.py`, dataset card §2; Phase 2 must train from the clean/split files only, never from `*.raw.jsonl`.
**Recorded in:** `docs/slm-mixture-v1.md` §2.

---

## Active Blockers

### WS-B-001: PRD v1.1.0 is "in review" until Phase 0 fixes accuracy targets — ✅ RESOLVED (2026-10-03)

**Discovered:** 2026-10-03 · **Resolved:** 2026-10-03 (Phase 0 measurement run)
**Resolution:** PRD bumped to **v1.2.0**; §2 carries fixed targets (`≥0.723` LLM candidate, `≥0.474` System-1, anchor `eval_multi_domains` n=264), §3.1 records the context decision, §7.2 updated. Evidence: `docs/phase0-baseline.md` + 24 artifacts in `benchmarks/results/`. Remaining step: **maintainer approval of v1.2.0**.

### WS-B-002: ADR-0017 not published → Phase 2 blocked

**Discovered:** 2026-10-03
**Impact:** training code must not be written before the stack ADR exists (PRD §6 Fase 2: "ADR-0017 antes de codar").
**Workaround:** none (intentional gate).
**Resolution:** draft → review → publish ADR-0017 in `munod/tachyone` at the start of Phase 2 (decision criteria in DEC-002).

---

## Lessons Learned

### Inherited from `munod/tachyone` (canonical source upstream — referenced, not copied)

| ID | Reminder | Where it applies here |
| --- | --- | --- |
| L-006 | Control before blaming variance (same seed already produced 0.76–0.79) | Phase 2 experiment discipline |
| L-011 | Verify the launch config is identical to the experiment config before running | Phase 2 |
| L-013 | Never gate on a *routed* harness — use an explicit adapter | Phases 2, 4, 5 |
| L-014 | More context did not save the encoder — context helps the SLM only as a Phase 0 hypothesis | Phase 0 A/B |
| L-015 | ECE alone is not a quality metric — publish Brier + `Conf` alongside | Phases 4, 5 |
| B-8 | An unreadable calibration asset must warn **by name**, never degrade silently | Phase 4 |
| AD-009 | Doc surfaces updated **as a set**; seed pinning | Phases 2, 5 |
| B-10 | Small LLMs fail the contract under free generation (46 s / 52 options; `JSON ok` 0.889) | Decoding decision DEC-001 |
| B-11/B-12 | Indexing label bugs cost 3 retrains — labels must be derived from text (ADR-0014/0015) | Phase 1 |

### Created in this workspace (`WS-` prefix)

| ID | Lesson | Date | Where it applies |
| --- | --- | --- | --- |
| WS-L-001 | **Record the denominator, always**: at τ = 0.6 the abstained slice was 1/1500 (`eval_en`), 4/7500 (`eval_en_domains`), 18/1500 (`eval_multi`) — System-1's mean confidence is 0.99–0.994 on in-sample synthetic data, so it barely abstains. A slice %, without its n, would have read as a real target. | 2026-10-03 | PRD §2, Phases 4–5 acceptance |
| WS-L-002 | **The wire payload carries no `max_tokens`**: free-generation clients ran away (measured 6,024 tokens ≈ 39 s for one row, which alone made a dataset take ~1 h). llama-server must be capped (`-n 1024`) or the scoring mode (§3.4) must be used — both recorded as protocol notes. | 2026-10-03 | Phases 4–5, benchmark harness |
| WS-L-003 | **The five-domain fitted-bank checkpoints are not distributed** (no Hub model, no release asset): System-1 with the deployable Hub adapters scores 0.9145 on `eval_multi_domains`, not the 0.997 quoted for `multi_b5b_fit_bank`. Never mix the two in one table. | 2026-10-03 | PRD §2 baseline column, Phase 5 |
| WS-L-004 | **Harness protocol deviations must be written next to the number**: `-n 1024` cap, Ollama rows uncapped, 192-row val fit, fixed T=1.0 on the 1- and 4-row slices. All seven are listed in `docs/phase0-baseline.md` §5. | 2026-10-03 | every future benchmark |
| WS-L-005 | **A different seed does not buy contamination isolation** when two datasets share phrase banks: 41.31% of raw mixture records matched a frozen eval row despite seed 20261003 vs 2. Audit by *content* (state + prompt fingerprint), dedup, re-audit — and budget for the drop when sizing `per_type`. | 2026-10-04 | Phase 1, any future data generation |
| WS-L-006 | **Never let the workspace package shadow an upstream one**: a workspace `training/` package hid the clone's `training.generate_data` (PEP 420 gives a regular package priority). Workspace tooling lives in `slm_pipeline/`; `training/configs/` stays as plain data (DAT-01 path). | 2026-10-04 | all workspace tooling |

---

## Quick Tasks Completed

| # | Description | Date | Commit | Status |
| --- | --- | --- | --- | --- |
| 001 | Read PRD v1.1.0 in full; extracted KPIs, phases, constraints | 2026-10-03 | — (no git yet) | ✅ Done |
| 002 | Authored `.specs/` (project + 6 feature specs + design) | 2026-10-03 | — | ✅ Done |
| 003 | Authored `docs/` set (architecture, plan, model-card, decisions, index) + `mkdocs.yml` | 2026-10-03 | — | ✅ Done |
| 004 | Authored root docs (README, CHANGELOG, CONTRIBUTING) + `.gitignore` | 2026-10-03 | — | ✅ Done |
| 005 | **Phase 0 executed** — clone + env, datasets (golden 46/46), slices, 4 engines × 4 slices, context A/B, report `docs/phase0-baseline.md` | 2026-10-03 | — | ✅ Done |
| 006 | PRD v1.1.0 → **v1.2.0**: §2 targets fixed, §3.1 context decided, §6/§7/§8 updated | 2026-10-03 | — | ✅ Done |
| 007 | **Git bootstrap** — `git init -b main`, remote `origin git@github.com:munod/tachyone_slm.git`, initial commit pushed (`2122616`, 71 files / 748 KB); `.opencode/`, `site/` and `logs/` excluded by `.gitignore` | 2026-10-03 | `2122616` | ✅ Done |
| 008 | **Phase 1 delivered** — `slm_pipeline/` (generate → dedup → split → render → audit), config `data_sft_slm.json`, 16 tests, dataset card `docs/slm-mixture-v1.md` | 2026-10-04 | pending commit | ✅ Done |

---

## Deferred Ideas

- [ ] Speculative decoding experiment — only if measured gain justifies it (PRD §4.6) — captured during: spec authoring
- [ ] Scratchpad reasoning before the `answers` wrapper in experimental generation mode for the hard slice (PRD §3.4) — captured during: Phase 4 spec
- [ ] Composed System-1 + System-2 JevBench submission (currently out of scope, PRD §1.4) — captured during: PRD review
- [ ] External server (vLLM/TRT-LLM) as default if Phase 5 shows the embedded engine misses p50 (PRD §5.2) — captured during: Phase 4 spec
- [ ] 8-bit AdamW (bitsandbytes) if RTX 3060 VRAM is tight (PRD §3.2) — captured during: Phase 2 spec

---

## Todos

- [x] Run Phase 0 baselines and fix numeric accuracy targets in PRD §2 — **done 2026-10-03** (PRD v1.2.0)
- [x] Build `Tachyone-SLM-Mixture-v1` (config, dedup, split, render, audit, provenance) — **done 2026-10-04** (DAT-01…08)
- [ ] **Appro PRD v1.2.0** (maintainer) — closes Phase 0
- [ ] Publish ADR-0017 (training/export stack) + schema annex (PRD §5.4) in `munod/tachyone` — **gates Phase 2**
- [ ] Publish `Tachyone-SLM-Mixture-v1` to HF (`munod/tachyone_slm`) — **only on request** (WS-B-019)
- [ ] Fill `docs/model-card.md` placeholders in Phase 5
- [ ] Add the SLM engine row to `benchmarks/compare.py` (Phase 5)
- [x] Extend `mkdocs.yml` nav as new pages land (`phase0-baseline` + `slm-mixture-v1` added — WS-B-013 covered)
- [ ] Re-run the probe contamination audit when probe data exists (WS-B-020)
- [x] `git init` + initial commit — **only if/when explicitly requested** — **done 2026-10-03** (remote `munod/tachyone_slm`, commit `2122616`)
- [ ] Update ROADMAP statuses as phases start/complete — **Milestones 0 and 1 complete**

---

## Preferences

**Model Guidance Shown:** never
