# Backlog

**Workspace:** `TachyOne_SLM` (specification workspace for the `munod/tachyone` epic)
**Last Updated:** 2026-10-03 *(after Phase 0)*
**Source of truth:** `docs/tachyone_prd.md` **v1.2.0**

> **Scope note:** items **owned by this workspace / this epic** are listed here as `WS-B-NNN`. The upstream backlog of `munod/tachyone` (`B-5`, `B-10`, `B-11`, `B-12`, `B-13/P0`, …) lives in that repo's `.specs/project/BACKLOG.md` and is only **referenced** below — not copied, not re-numbered.

---

## Open Items

| ID | Item | Priority | Phase | PRD ref | Status |
| --- | --- | --- | --- | --- | --- |
| WS-B-002 | **Publish ADR-0017** (training stack + export/serving stack) — planned only; must exist before any training code | P0 | 2 (draft) / 3 (final) | §4.1, §5.4, §6, §7.6 | Open — blocks Phase 2 |
| WS-B-004 | Contamination **overlap audit** record for `Tachyone-SLM-Mixture-v1` (prompts + temperature-fit val split vs eval sets) | P0 | 1 | §3.3, §8 | Open |
| WS-B-005 | Golden-hash idempotence test + deterministic train/val split wired into `pytest` | P1 | 1 | §3.3 | Open |
| WS-B-006 | Temperature-scaling fit per (primitive, language) with ECE + Brier + `Conf` reported together | P0 | 4 | §3.5, §7.4 | Open |
| WS-B-007 | New engine row in `benchmarks/compare.py` + KPI tables in `benchmarks/report.md` (GPU declared) | P0 | 5 | §2, §7.3, §7.5 | Open |
| WS-B-008 | Fill `docs/model-card.md` placeholders (metrics, eval data, VRAM, license) | P1 | 5 | §7.6 | Open |
| WS-B-009 | Migrate `docs/cookbook-handoff.md` example from `system_two()` stub to the real implementation | P1 | 4–5 | §5.2, §7.6 | Open |
| WS-B-010 | Publish the JSON Schema/grammar annex of the contract (annex of ADR-0017, tested against `tests/test_contract_wire.py`) | P1 | 4 | §5.4 | Open |
| WS-B-011 | Measure embedded local engine **vs** external servers (vLLM/TRT-LLM) side by side | P2 | 5 | §5.2 | Open |
| WS-B-012 | Record stretch `< 8 ms` only with preconditions met (FP8@L4 + minimal output); otherwise mark "not measured / not met" | P2 | 5 | §4.5, §7.3, §8 | Open |
| WS-B-013 | Extend `mkdocs.yml` nav as new documentation pages land; keep `mkdocs build --strict` green | P3 | ongoing | §6 gates | Open |
| WS-B-014 | `git init` + first conventional commit of this workspace — **only on explicit request** | P3 | on request | — | ✅ Done (2026-10-03) — `git init -b main`, remote `git@github.com:munod/tachyone_slm.git`, commit `2122616` pushed |
| WS-B-015 | **Approve PRD v1.2.0** — Phase 0 fixed the numbers; the approval itself is the last gate of the status line | P0 | 0 | Status line, §7 | Open — closes Phase 0 |
| WS-B-016 | Wire payload carries **no `max_tokens`** → free-generation clients run away (6,024 tokens/row measured). Cap the engine (`-n 1024`) in every future run, or fix it once the scoring mode lands (Phase 4) | P1 | 4–5 | §3.4, §4.5 | Open — WS-L-002 |
| WS-B-017 | **English abstained slice has no usable denominator** at τ=0.6 (n=1 / n=4). Decide before Phase 5: higher τ (sweep in `docs/phase0-baseline.md` §1), harder English eval set, or accept a multilingual anchor | P2 | 5 | §2, §8 | Open — WS-AD-008 |
| WS-B-018 | Five-domain fitted-bank checkpoints (`multi_b5b_fit_bank`, `en_jev_bank`) are **not distributed** (no Hub model, no release asset) while `benchmarks/report.md` quotes their 0.997 — ask upstream to publish them or stop quoting the number | P2 | 5 | §2 baseline col. | Open — WS-L-003 |
| WS-B-019 | **Publish `Tachyone-SLM-Mixture-v1` to Hugging Face** (`munod/tachyone_slm`) — dataset card + files; only on explicit request, nothing uploads automatically | P2 | 1 → 5 | §3.3, §7.6 | Open — awaiting maintainer |
| WS-B-020 | Public-probe contamination audit (`typed-decisions`/`MASSIVE`/`XNLI`) — recorded as `skipped — absent locally`; re-run when probe data exists | P3 | 5 | §3.3, §8 | Open — structural argument recorded instead |
| WS-B-021 | `noul` is the thinnest primitive after dedup (**13,607** pairs vs 19,131 `choice`) and `en`×`support` the smallest cell (451) — Phase 2 must gate on these worst cells (§3.2) | P2 | 2 | §3.2, §7.2 | Open — surfaced by DAT-07 |

---

## Referenced (owned upstream — `munod/tachyone`, not this workspace)

| Upstream ID | What it is | Why it matters to this epic | PRD ref |
| --- | --- | --- | --- |
| B-13 / P0 | Encoder truncates at 512 tokens; `noul` ignores the rubric | Motivates reading the full text with the SLM (hypothesis tested in Phases 0/4) | §1.3 |
| B-10 | Small LLMs fail the wire contract under free generation (`JSON ok` 0.889; 46 s / 52 options) | Evidence for the scoring decision (DEC-001) and the `JSON ok` = 1.000 KPI | §1.3, §3.4, §7.1 |
| B-11 / B-12 | Indexing label bugs cost 3 retrains | Forces label derivation from text (ADR-0014/0015) in Phase 1 | §3.3 |
| B-8 | Silent calibration-asset degradation | Loud-warning fallback required in Phase 4 | §3.5 |
| B-3 | Handoff mechanism (`assess_response(τ)` → `system_two()`) | The plug-in point of this entire feature | §1.2, §5.2 |
| AD-009 | Pinned seeds; doc surfaces updated as a set | Phase 2 discipline; Phase 5 publication set | §3.2, §7.6 |
| L-005…L-016 | Experiment lessons (variance, in-sample synthetic, routed harness, ECE-alone, context) | Constraints on training/gating/measurement | §3.2, §3.5 |

---

## Done (this workspace)

| ID | Item | Date |
| --- | --- | --- |
| DAT-01…08 | **Phase 1 delivered** — `Tachyone-SLM-Mixture-v1`: 85,500 raw → **50,180 clean pairs**, audit **pass** (0/0 over 18,000 frozen records), split 45,175/5,005, 16 tests green, dataset card `docs/slm-mixture-v1.md` | 2026-10-04 |
| WS-B-014 | `git init` + first conventional commit — executed on request: `git init -b main`, remote `munod/tachyone_slm`, commit `2122616` | 2026-10-03 |
| WS-B-001 | **Phase 0 baselines measured** (System-1 + `ornith-9b` + `ling-tiny` + SLM base × 4 slices, τ sweep, yardstick) and **PRD §2 targets fixed** → PRD v1.2.0; evidence `docs/phase0-baseline.md` + 24 artifacts | 2026-10-03 |
| WS-B-003 | **Context A/B executed**: 2,048 vs 4,096 identical (0 rows exceed 2,048 tokens) → **2,048 chosen** (WS-AD-007, PRD §3.1) | 2026-10-03 |
| WS-B-000a | Read and reconciled PRD v1.1.0; extracted KPI/phase/traceability matrix into specs | 2026-10-03 |
| WS-B-000b | Authored `.specs/` (PROJECT, ROADMAP, STATE, BACKLOG, 6 feature specs, 1 design) | 2026-10-03 |
| WS-B-000c | Authored documentation set (`README`, `CHANGELOG`, `CONTRIBUTING`, `docs/**`, `mkdocs.yml`) and root `.gitignore` | 2026-10-03 |
