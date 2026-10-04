# TachyOne SLM — Specification & Documentation Workspace

> *"Beyond the Speed of Light"* — the official **local System-2** of the TachyOne System-1/System-2 hybrid.

**Status:** 🟢 **Phase 0 complete (2026-10-03)** — PRD **v1.2.0** carries fixed numeric targets ([`docs/phase0-baseline.md`](docs/phase0-baseline.md)); workspace still holds **specs and documentation only — no product code, no git history yet** (code lives in [`munod/tachyone`](https://github.com/munod/tachyone)). Next: Phase 1 data.

---

## What is this?

TachyOne SLM is a **Qwen2.5-0.5B-Instruct** model fine-tuned with **SFT via LoRA**, invoked by the confidence handoff `assess_response(τ)` → `system_two()` on inputs where the System-1 encoder **abstains**. It replaces the current slow LLM candidates (`ornith-9b`, `ling-tiny` — 1.2–6.8 s p50, `JSON ok` ≤ 0.889, 4.8–5.5 GB VRAM) with a local engine that is **fast (< 20 ms p50)**, **calibrated (ECE ≤ 0.030)** and **contract-guaranteed (`JSON ok` = 1.000)** — without touching the frozen `/v1/systemone` wire or the System-1 encoder.

## Source of truth

| Document | Role | Language |
| --- | --- | --- |
| [`docs/tachyone_prd.md`](docs/tachyone_prd.md) — **PRD v1.2.0** | Product source of truth: KPIs (§2), architecture (§3), performance plan (§4), interface (§5), phases (§6), acceptance (§7), risks (§8), traceability (§9) | 🇧🇷 Portuguese (original, unmodified) |
| [`.specs/`](.specs/README.md) | Spec-driven artifacts: project vision/roadmap/state/backlog + 6 feature specs with requirement IDs | 🇬🇧 English |
| [`docs/`](docs/index.md) | Architecture, execution plan, decisions, model card | 🇬🇧 English |

**Language policy (explicit):** all **new** documentation produced in this workspace — `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `docs/**`, `.specs/**` — is written in **English**, per PRD §6 ("docs/PRs em inglês"). The PRD itself remains in **Portuguese** as the product source of truth (decision **DEC-004**, `docs/decisions/docs-language.md`).

## Quick links

- **PRD:** [`docs/tachyone_prd.md`](docs/tachyone_prd.md)
- **Specs:** [`.specs/README.md`](.specs/README.md) · [project](.specs/project/PROJECT.md) · [roadmap](.specs/project/ROADMAP.md) · [state](.specs/project/STATE.md) · [backlog](.specs/project/BACKLOG.md)
- **Feature specs (Phases 0–5):** [baseline-system2](.specs/features/baseline-system2/spec.md) · [slm-mixture-data](.specs/features/slm-mixture-data/spec.md) · [slm-lora-sft](.specs/features/slm-lora-sft/spec.md) · [slm-export-quant](.specs/features/slm-export-quant/spec.md) · [system-two-integration](.specs/features/system-two-integration/spec.md) · [slm-benchmark-docs](.specs/features/slm-benchmark-docs/spec.md)
- **Docs:** [architecture](docs/architecture.md) · [execution plan](docs/plan.md) · [model card (template)](docs/model-card.md) · [decisions](docs/decisions/README.md)
- **Contributing:** [`CONTRIBUTING.md`](CONTRIBUTING.md) · **Changelog:** [`CHANGELOG.md`](CHANGELOG.md)

## Phases at a glance (PRD §6)

| Phase | Name | Days | Status |
| --- | --- | --- | --- |
| 0 | Baseline System-2 — fix numeric accuracy targets | 1 | ✅ **DONE** (2026-10-03) — targets `≥0.723`/`≥0.474`, context 2,048 |
| 1 | SFT mixture data (`Tachyone-SLM-Mixture-v1`, ≈50k) | 2–3 | PLANNED — next |
| 2 | LoRA/SFT training (**ADR-0017 first**) | 4–5 | PLANNED — blocked by ADR-0017 |
| 3 | Export & quantization (INT4@3060 / FP8@L4) | 6 | PLANNED |
| 4 | `system_two()` integration, calibration, τ/retry/fallback | 7–8 | PLANNED |
| 5 | Benchmark + English publication set | 9–10 | PLANNED |

**Daily gates (PRD §6):** `ruff check` · `ruff format --check` · `pyright` · `pytest` · `mkdocs build --strict` · conventional commits · docs/PRs in English.

## Repository structure

```
TachyOne_SLM/                     ← this specification workspace
├── .gitignore                    # Python/ML/IDE ignores; docs & configs ARE versioned
├── README.md                     # this file
├── CHANGELOG.md                  # Keep a Changelog / SemVer
├── CONTRIBUTING.md               # commits, gates, language policy
├── docs/
│   ├── tachyone_prd.md           # PRD v1.2.0 (source of truth, Portuguese — do not overwrite)
│   ├── index.md · architecture.md · plan.md · model-card.md
│   └── decisions/                # spec-decisions (DEC-001…), incl. pending ADR-0017 record
├── mkdocs.yml                    # docs nav (mkdocs build --strict gate)
└── .specs/                       # spec-driven artifacts (PROJECT / ROADMAP / STATE / BACKLOG / features)
```

## Explicit non-goals of this workspace

- No `.py` files, no training/benchmark runs, no `git init`/commits — unless explicitly requested later (decision **WS-AD-005**, `.specs/project/STATE.md`).
- No metric is ever invented: anything unmeasured reads **"to be measured (Phase 0/5)"** (decision **WS-AD-006**).
- The wire contract and the System-1 encoder are **frozen** (ADR-0001, PRD §1.4).
