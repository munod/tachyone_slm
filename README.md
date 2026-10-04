# TachyOne SLM — Specification & Documentation Workspace

> *"Beyond the Speed of Light"* — the official **local System-2** of the TachyOne System-1/System-2 hybrid.

**Status:** 🟢 **Phases 0 and 1 complete** — PRD **v1.2.0** carries fixed numeric targets ([`docs/phase0-baseline.md`](docs/phase0-baseline.md)) and `Tachyone-SLM-Mixture-v1` is built: **50,180 clean SFT pairs**, contamination audit pass, 16 tests green ([`docs/slm-mixture-v1.md`](docs/slm-mixture-v1.md)). **Product code still lives in [`munod/tachyone`](https://github.com/munod/tachyone)** — this repo holds specs, docs and data tooling. Next: **ADR-0017 → Phase 2 training**.

---

## What is this?

TachyOne SLM is a **Qwen2.5-0.5B-Instruct** model fine-tuned with **SFT via LoRA**, invoked by the confidence handoff `assess_response(τ)` → `system_two()` on inputs where the System-1 encoder **abstains**. It replaces the current slow LLM candidates (`ornith-9b`, `ling-tiny` — 1.2–6.8 s p50, `JSON ok` ≤ 0.889, 4.8–5.5 GB VRAM) with a local engine that is **fast (< 20 ms p50)**, **calibrated (ECE ≤ 0.030)** and **contract-guaranteed (`JSON ok` = 1.000)** — without touching the frozen `/v1/systemone` wire or the System-1 encoder.

## Source of truth

| Document | Role | Language |
| --- | --- | --- |
| [`docs/tachyone_prd.md`](docs/tachyone_prd.md) — **PRD v1.2.0** | Product source of truth: KPIs (§2), architecture (§3), performance plan (§4), interface (§5), phases (§6), acceptance (§7), risks (§8), traceability (§9) | 🇧🇷 Portuguese (original, unmodified) |
| [`.specs/`](.specs/README.md) | Spec-driven artifacts: project vision/roadmap/state/backlog + 6 feature specs with requirement IDs | 🇬🇧 English |
| [`docs/`](docs/index.md) | Architecture, execution plan, decisions, model card, **Phase 0 baseline**, **dataset card** | 🇬🇧 English |

**Language policy (explicit):** all **new** documentation produced in this workspace — `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `docs/**`, `.specs/**` — is written in **English**, per PRD §6 ("docs/PRs em inglês"). The PRD itself remains in **Portuguese** as the product source of truth (decision **DEC-004**, `docs/decisions/docs-language.md`).

## Quick links

- **PRD:** [`docs/tachyone_prd.md`](docs/tachyone_prd.md)
- **Specs:** [`.specs/README.md`](.specs/README.md) · [project](.specs/project/PROJECT.md) · [roadmap](.specs/project/ROADMAP.md) · [state](.specs/project/STATE.md) · [backlog](.specs/project/BACKLOG.md)
- **Feature specs (Phases 0–5):** [baseline-system2](.specs/features/baseline-system2/spec.md) · [slm-mixture-data](.specs/features/slm-mixture-data/spec.md) · [slm-lora-sft](.specs/features/slm-lora-sft/spec.md) · [slm-export-quant](.specs/features/slm-export-quant/spec.md) · [system-two-integration](.specs/features/system-two-integration/spec.md) · [slm-benchmark-docs](.specs/features/slm-benchmark-docs/spec.md)
- **Docs:** [architecture](docs/architecture.md) · [execution plan](docs/plan.md) · [Phase 0 baseline](docs/phase0-baseline.md) · [dataset card (SLM Mixture v1)](docs/slm-mixture-v1.md) · [model card (template)](docs/model-card.md) · [decisions](docs/decisions/README.md)
- **Contributing:** [`CONTRIBUTING.md`](CONTRIBUTING.md) · **Changelog:** [`CHANGELOG.md`](CHANGELOG.md)

## Phases at a glance (PRD §6)

| Phase | Name | Days | Status |
| --- | --- | --- | --- |
| 0 | Baseline System-2 — fix numeric accuracy targets | 1 | ✅ **DONE** (2026-10-03) — targets `≥0.723`/`≥0.474`, context 2,048 |
| 1 | SFT mixture data (`Tachyone-SLM-Mixture-v1`, ≈50k) | 2–3 | ✅ **DONE** (2026-10-04) — 50,180 clean pairs, audit pass |
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
├── mkdocs.yml                    # docs nav (mkdocs build --strict gate)
├── conftest.py                   # test path setup
├── docs/
│   ├── tachyone_prd.md           # PRD v1.2.0 (source of truth, Portuguese — do not overwrite)
│   ├── phase0-baseline.md        # Phase 0 measured baselines + protocol deviations
│   ├── slm-mixture-v1.md         # dataset card / provenance (DAT-08)
│   ├── index.md · architecture.md · plan.md · model-card.md
│   └── decisions/                # spec-decisions (DEC-001…), incl. pending ADR-0017 record
├── .specs/                       # spec-driven artifacts (PROJECT / ROADMAP / STATE / BACKLOG / features)
├── training/configs/             # DAT-01: data_sft_slm.json (config only — code lives upstream)
├── slm_pipeline/                 # Phase 1 tooling: generate → dedup → split → render → audit
├── benchmarks/                   # Phase 0 tooling: slice builder, run scripts, context A/B, renderer
├── tests/                        # pytest (16 Phase 1 tests: golden hash, split, render, audit)
├── artifacts/slm-mixture-v1/     # versioned evidence: manifest, split/render report, audit
└── data/                         # GITIGNORED (~130 MB, regenerable in ~4 s)
```

## Explicit non-goals of this workspace

- **Product code stays upstream.** No runtime/training code of `munod/tachyone` is written, patched or forked here — the upstream pipeline is *imported read-only* (decision **WS-AD-005**, marked superseded for measurement tooling and `git init`, which were explicitly requested).
- **No metric is ever invented**: anything unmeasured reads **"to be measured (Phase 0/5)"** (decision **WS-AD-006**); Phase 0 rows now carry measured values, everything else waits for its phase.
- **Nothing uploads on its own**: no HF push, no Ollama registry push — publication is always an explicit, separate step (WS-B-019).
- The wire contract and the System-1 encoder are **frozen** (ADR-0001, PRD §1.4).
