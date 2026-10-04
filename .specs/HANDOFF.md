# Handoff

**Date:** 2026-10-04 (paused after Phase 1 publication)
**Project:** TachyOne SLM — spec & documentation workspace (`munod/tachyone_slm`)
**Task:** **PROJECT PAUSED** pending external event: JevBench evaluation of `munod/tachyone-en`

## Completed ✓

- **Phase 0 (`baseline-system2`, 7/7):** 24 artifacts, PRD v1.1.0 → **v1.2.0** (slice targets
  fixed: ≥0.723 LLM / ≥0.474 System-1, anchor `eval_multi_domains` n=264), context decided
  (**2,048**), report `docs/phase0-baseline.md`.
- **Phase 1 (`slm-mixture-data`, 8/8):** `Tachyone-SLM-Mixture-v1` — 85,500 raw → **50,180
  clean** (41.31% frozen-set collisions removed), split 45,175/5,005, **50,180 validated pairs
  (0 rejected)**, audit **pass 0/0**, 16 tests, dataset card `docs/slm-mixture-v1.md`.
- **Published:** dataset [`datasets/munod/tachyone_slm_mixture_v1`](https://huggingface.co/datasets/munod/tachyone_slm_mixture_v1)
  (verified with `load_dataset`); GitHub repo `munod/tachyone_slm` @ `f82b5f2` (4 commits).
- **JevBench non-interference audit (7/7):** `docs/jevbench-noninterference.md`.

## In Progress

- Nothing. Clean stopping point: gates 5/5 green, work tree committed, no process running.

## Pending (on resume — trigger: **#182 closed + board published**)

1. Re-run the reachability audit (`docs/jevbench-noninterference.md` §2) — pins may move.
2. Record **DEC-002** (training/export stack) **in this repo** — the upstream ADR was dropped by PRD v2.0.0 (DEC-005).
3. Phase 2 SFT/LoRA training (gated by DEC-002) → Phase 3 export → Phase 4 serving shim → Phase 5.
4. Maintainer approval of **PRD v1.2.0** (WS-B-015).

## Blockers

- **Freeze until JevBench #182 closes** — no pushes to `munod/tachyone`, no ADR-0017 upstream, no
  releases, no edits to #182. Reason: the issue's snippet clones `main` **without checkout**
  (matrix §3 of the non-interference report). Maintainer decisions 2026-10-04.
- **WS-B-002** — DEC-002 not recorded yet (gates Phase 2; PRD v2.0 dropped the upstream ADR).

## Context

- Branch: `main` @ `f82b5f2` · remote: `git@github.com:munod/tachyone_slm.git` · **uncommitted: none**
- Pushes allowed: this repo only. Upstream clone `/tmp/opencode/tachyone` (read-only, HEAD `164ed3b`).
- JevBench pins: weights `1c88ebef` · inference commit `538ac68` · harness `bb05a335` · issue open, 1 comment.
- Decisions: `WS-AD-007/008/009`, `WS-AD-005` (superseded), `WS-AD-006` (no invented metrics).
- Resume protocol: load this file → `STATE.md` → summarize → propose next action.
