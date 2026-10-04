# TachyOne SLM — Documentation

> The official **local System-2** of the TachyOne System-1/System-2 hybrid: a Qwen2.5-0.5B-Instruct SLM (SFT + LoRA) invoked by the confidence handoff when the encoder abstains.
> *"Beyond the Speed of Light."*

## Start here

| Page | What you'll find |
| --- | --- |
| [Product Requirement Document (v2.0.0)](tachyone_prd.md) | **Source of truth** — KPIs, architecture, interface, phases, acceptance, risks (🇧🇷 Portuguese) |
| [Phase 0 Baseline](phase0-baseline.md) | Measured abstained-slice baselines: slice sizes, τ sweep, candidate accuracy, context coverage, protocol deviations (2026-10-03) |
| [Dataset Card — SLM Mixture v1](slm-mixture-v1.md) | `Tachyone-SLM-Mixture-v1` provenance: 50,180 clean SFT pairs, contamination audit, split, rendering, sha256 (2026-10-04) |
| [JevBench Non-Interference](jevbench-noninterference.md) | **Why the project is paused:** evaluation pins, reachability audit 7/7, interference matrix, do-not-touch list, resume checklist (2026-10-04) |
| [Architecture](architecture.md) | System-1/System-2 hybrid, handoff contract, SLM scoring flow, calibration, fallback chain |
| [Execution Plan](plan.md) | Phases 0–5, daily gates, acceptance gates, risks, current status |
| [Model Card](model-card.md) | Template with `TODO(Phase 5)` placeholders — Phase 0 baselines (untrained base) already recorded |
| [Decisions](decisions/README.md) | Spec-decisions DEC-001…DEC-005 (incl. the v2.0 re-scope and DEC-002) |

## Specifications

Spec-driven artifacts live in **`.specs/`** (at the repository root): project vision, roadmap, state, backlog and six feature specs with requirement IDs traceable to PRD §2/§7 — see `.specs/README.md` (repository root, intentionally outside this doc site).

## Language policy

New documentation on this site is written in **English** (PRD §6 gate: docs/PRs in English). The PRD itself remains in **Portuguese** as the product source of truth — see [Decisions → DEC-004](decisions/docs-language.md).

## Status

Specification phase — **no product code in this workspace**; code lives in [`munod/tachyone`](https://github.com/munod/tachyone). Unmeasured metrics read *"to be measured (Phase 0/5)"* — nothing here is fabricated.
