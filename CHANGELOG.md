# Changelog

All notable changes to this **specification & documentation workspace** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Language note:** entries are written in **English** (PRD §6 gate: docs/PRs in English). The product source of truth, `docs/tachyone_prd.md` (**PRD v1.2.0**), is versioned separately in its own header and remains in **Portuguese** — it is referenced here, never overwritten (decision DEC-004).

## [0.4.0] - 2026-10-04

**⏸️ Project paused** — awaiting the public JevBench evaluation of the submitted System-1 checkpoint.

### Added

- **`docs/jevbench-noninterference.md`** — the audit that justifies the pause (read-only, 7/7 pass):
  - pins declared by [`fstandhartinger/jevbench#182`](https://github.com/fstandhartinger/jevbench/issues/182) (weights `1c88ebef`, inference commit `538ac68`, harness `bb05a335`, licence lock, calibration assets);
  - reachability of all 7 URLs (**all 200**), **sha256 of the 5 pinned files matched 5/5** and the method file hash matched exactly;
  - upstream untouched (`git status` empty, HEAD `164ed3b`), our pushes only in `munod/tachyone_slm`, no identifier collision;
  - **interference matrix** (everything done/planned × evaluation surfaces) and the single real vector: the issue's snippet clones `main` **without `checkout`**;
  - do-not-touch list, freeze policy, resume checklist.
- **`.specs/HANDOFF.md`** — pause handoff per the `tlc-spec-driven` protocol (completed / pending / blockers / context + resume steps).

### Changed

- **Freeze recorded as `WS-B-022`** (P0): no pushes to `munod/tachyone` (code/docs/ADR-0017/releases), no HF revision changes on `tachyone-en`, no edits to #182 — **owner decisions 2026-10-04**; this repo keeps receiving pushes.
- **Resume trigger:** #182 **closed** + **board published** → re-run the reachability audit → ADR-0017 (explicit go-ahead) → Phase 2.
- `.specs/project/ROADMAP.md` — header reflects the pause; Milestones 2–5 → **⏸️ PAUSED**; `STATE.md` — current work, blocker `WS-B-022`, todos; `BACKLOG.md` — `WS-B-002` paused, `WS-B-022` opened; `README.md` — ⏸️ status; `docs/plan.md` — pause banner; `mkdocs.yml`/`docs/index.md` — report added to the nav.

## [0.3.1] - 2026-10-04

### Changed

- **Dataset published to Hugging Face:** [`datasets/munod/tachyone_slm_mixture_v1`](https://huggingface.co/datasets/munod/tachyone_slm_mixture_v1) (public, Apache-2.0, 62.6 MB) — `records/` + `pairs/` (train/validation), `provenance/` (manifest, split/render report, audit, config), HF dataset card and `LICENSE`. Uploaded **only on explicit request**; the model repo [`munod/tachyone_slm`](https://huggingface.co/munod/tachyone_slm) remains reserved for the SLM weights (Phase 3/5).
- **Verified end-to-end:** `load_dataset("munod/tachyone_slm_mixture_v1", "records"|"pairs")` → 45,175 / 5,005 rows on both configs, samples spot-checked (wire-request prompt, gold label).
- `docs/slm-mixture-v1.md` §8 — "not yet published" replaced by the published URL + verification; `BACKLOG` `WS-B-019` closed; `STATE` todo checked.

### Fixed

- HF dataset-card schema: `license_name` dropped (must be lowercase) and `dataset_info` uses `num_examples` (not `num_rows`) — the first upload attempt was rejected by `/api/validate-yaml` and the first `load_dataset` failed on the wrong key; both corrected and re-published.

## [0.3.0] - 2026-10-04

**Phase 1 (`slm-mixture-data`) delivered** — `Tachyone-SLM-Mixture-v1`, the SFT training data of the epic (DAT-01…08, 8/8).

### Added

- **`slm_pipeline/`** — Phase 1 tooling under a package name that never shadows the upstream `training` package (WS-L-006):
  - `generate_mixture.py` — config-driven generation (the JSON *is* the run: no duplicated CLI flags) + manifest with sha256, per-primitive/per-language/per-cell counts.
  - `prepare_sft.py` — contamination **dedup → deterministic split → render → audit → reports**; fails the build on any overlap.
  - `render_sft.py` — wire-request prompt (§5.1) + gold label target (§3.4); every prompt re-parsed by `tachyone.wire.parse_request`, targets validated against their own candidate set.
  - `audit_contamination.py` — content-based fingerprints (state + prompt), frozen sets vs mixture **and** vs the temperature-fit val side; empty states counted, never matched.
- **`training/configs/data_sft_slm.json`** — 7 languages × 5 domains, seed `20261003`, `per_type` 5700 (DAT-01 path preserved as plain config data).
- **`tests/test_sft_mixture.py`** — 16 tests (3 s): byte-idempotence, config↔manifest golden hash, split stability, rendering per primitive, rejection paths, audit **pass and fail**.
- **`docs/slm-mixture-v1.md`** — dataset card / provenance (DAT-08): identity, contamination handling, split, rendering, coverage, sha256 of every artifact, caveats.
- **`artifacts/slm-mixture-v1/`** — `manifest.json`, `split_render.json`, `audit.json` (versioned evidence).
- `conftest.py` — test path setup.

### Changed

- **Dataset built:** 85,500 raw → **50,180 clean** records (41.31% collided with frozen eval sets and were removed per DAT-04 AC2) → split **45,175 / 5,005** → **50,180 validated SFT pairs, 0 rejected**; audit **pass** with overlap **0/0** over 18,000 frozen records; 35/35 language×domain cells (min 451, max 1,837).
- `.specs/features/slm-mixture-data/spec.md` — status **Complete**, 8/8 requirements, success criteria checked.
- `.specs/project/ROADMAP.md` — Milestone 1 **COMPLETE**.
- `.specs/project/STATE.md` — `WS-AD-009` (dedup + raw/clean naming), lessons `WS-L-005/006`, quick task 008, todos.
- `.specs/project/BACKLOG.md` — DAT-01…08 to Done; new `WS-B-019` (publish dataset to HF, on request), `WS-B-020` (probe audit), `WS-B-021` (worst cells for Phase 2).
- `.gitignore` — `data/` (≈130 MB of regenerable datasets) excluded; configs/artifacts/docs stay versioned.
- `mkdocs.yml` / `docs/index.md` — dataset card added to the nav.

## [0.2.0] - 2026-10-03

**Phase 0 (`baseline-system2`) executed and delivered** — the measurement run that unblocks PRD approval.

### Added

- `docs/phase0-baseline.md` — Phase 0 report rendered from artifacts: slice sizes, τ sweep (0.30–0.95), candidate accuracy per slice, context coverage, composite yardstick, **§5 protocol notes and deviations**, environment (GPU declared).
- `benchmarks/phase0_build_slice.py` — abstained-slice builder driving the frozen wire path with `tachyone.handoff`'s rule; writes slice JSONL + report (slice size, System-1 accuracy full/slice/kept, τ sweep).
- `benchmarks/phase0_run_llms.sh` — serialized engine runs (Ollama SLM base → `ling-tiny` → `ornith-9b` → System-1) over 4 slices; idempotent (skips existing artifacts), resumable.
- `benchmarks/phase0_run_context_ab.sh` — 2,048 vs 4,096 A/B (same engine, same rows, only `-c` differs).
- `benchmarks/phase0_context_lengths.py` — static token coverage per eval set/slice under the Qwen2.5 tokenizer (system prompt measured, not guessed).
- `benchmarks/phase0_render.py` — renders every `phase0_*.json` artifact into the report; missing artifacts render as **not measured**.
- `benchmarks/results/` — 24 artifacts (`phase0_{slice,ollama,ling,ornith,system1,ctx2048,ctx4096}_*.json`) + val splits + logs.

### Changed

- **PRD `docs/tachyone_prd.md` v1.1.0 → v1.2.0** (source of truth, Portuguese):
  - §2 — "a medir (Fase 0)" replaced by fixed targets: slice accuracy **≥0.723** (LLM candidate) **and ≥0.474** (System-1), anchor `eval_multi_domains` (n=264); baselines for `JSON ok`, p50/p95, VRAM (718 MiB) filled from this run; latency/throughput rows annotated with the SLM base measurement.
  - §3.1 — service context **decided: 2,048 tokens** (A/B was a tie by construction: 0 rows exceed 2,048 tokens).
  - §6 — Phase 0 marked ✅ CONCLUÍDA; §7.2 acceptance now carries the numbers; §8 gains the tiny-denominator risk row.
- `.specs/features/baseline-system2/spec.md` — status **Complete**, 7/7 requirements delivered, success criteria checked.
- `.specs/project/ROADMAP.md` — Milestone 0 **COMPLETE**.
- `.specs/project/STATE.md` — `WS-AD-007` (context 2,048) and `WS-AD-008` (anchor dataset) recorded; `WS-B-001` **resolved**; lessons `WS-L-001…004` added; todos updated.
- `.specs/project/BACKLOG.md` — `WS-B-001`/`WS-B-003` moved to **Done**; new open items `WS-B-015…018` (approve PRD v1.2.0, `max_tokens` gap, English-slice denominator, non-distributed fitted-bank checkpoints).
- `mkdocs.yml` — nav gains *Phase 0 Baseline*; PRD label bumped to v1.2.0.

## [0.1.0] - 2026-10-03

Initial specification release of the **TachyOne SLM** epic (System-2 local of the TachyOne hybrid). Documentation only — **no product code**.

### Added

- **PRD reference:** `docs/tachyone_prd.md` (PRD v1.1.0, Portuguese) registered as the immutable source of truth for KPIs (§2), architecture (§3–§5), phases (§6), acceptance (§7), risks (§8) and traceability (§9).
- **Spec structure (`.specs/`):**
  - `project/PROJECT.md` — vision, measurable goals (G1–G7 from §2/§7), stack, scope, constraints.
  - `project/ROADMAP.md` — Phases 0–5 as milestones with feature statuses (all PLANNED).
  - `project/STATE.md` — workspace decisions `WS-AD-001…006`, blockers `WS-B-001/002`, inherited lessons, deferred ideas, todos.
  - `project/BACKLOG.md` — workspace-owned open items `WS-B-001…014` + pointers to upstream backlog IDs (referenced, not copied).
  - Six feature specs with traceable requirement IDs: `baseline-system2` (Phase 0), `slm-mixture-data` (Phase 1), `slm-lora-sft` (Phase 2), `slm-export-quant` (Phase 3), `system-two-integration` (Phase 4, incl. `design.md`), `slm-benchmark-docs` (Phase 5) — every requirement mapped to PRD §2/§7.
- **Documentation set (English):**
  - `README.md` — project vision, status, structure, language policy.
  - `CONTRIBUTING.md` — conventional commits, daily gates, language policy, spec workflow.
  - `docs/index.md` — documentation home; `mkdocs.yml` nav (`mkdocs build --strict` gate).
  - `docs/architecture.md` — System-1/System-2 hybrid, handoff, SLM scoring flow, fallback chain (diagrams).
  - `docs/plan.md` — Phases 0–5 execution plan, gates, risks (PRD §8).
  - `docs/model-card.md` — model card **template** with `TODO(Phase 5)` / `to be measured (Phase 0)` placeholders.
  - `docs/decisions/` — DEC-001 decoding by scoring (decided), DEC-002 training/export stack (**pending — ADR-0017 planned, not drafted here**), DEC-003 spec location, DEC-004 language policy.
- **`.gitignore`** — compiled binaries, `.opencode/`, Python/ML tooling, ML weight artifacts (`models/`, `*.safetensors`, `*.gguf`, …), large datasets (`data/raw/`, `*.parquet`), IDE/OS/logs — with `docs/`, `*.md`, configs and `.specs/` explicitly **not** ignored.

### Notes

- No metrics or baselines were invented; unmeasured values read **"to be measured (Phase 0)"**.
- ADR-0017 is recorded as **planned/pending only** — it will be authored in `munod/tachyone`, not here.
- Git was **not** initialized; no commits were made.

[Keep a Changelog]: https://keepachangelog.com/en/1.1.0/
[Semantic Versioning]: https://semver.org/spec/v2.0.0.html
