# DEC-005 — Product scope: SLM + serving shim in this repo; upstream read-only

**Status:** ✅ **Decided (2026-10-04)** · owner decision · recorded as `WS-AD-010` in `.specs/project/STATE.md`
**Supersedes:** the scope assumptions of PRD v1.1.0–v1.2.0 (§5.2 upstream surfaces, §7.6 upstream ADR-0017)
**PRD traceability:** **v2.0.0** §1.1 (product scope), §1.4 (non-goals), §3.4 (where scoring runs), §5.2 (integration by configuration), §6 Fases 2/4/5, §7.6 (process), §10 (references)

---

## Decision

1. **The product is the SLM + its serving shim**, living entirely in **this repository** (code, docs, specs, data tooling) with artifacts published to Hugging Face (weights `munod/tachyone_slm`, dataset `munod/tachyone_slm_mixture_v1`).
2. **`munod/tachyone` is a read-only dependency, permanently.** It supplies the frozen wire contract, `training/generate_data.py`, `benchmarks/compare.py` and `tachyone.handoff` as *reference* — never as a write target: no code, no docs, no ADRs, no releases, no PRs.
3. **Integration = configuration.** The shim exposes an **OpenAI-compatible endpoint**; Tachyone selects it through the `llm` backend it already ships:
   `TACHYONE_BACKEND=llm`, `TACHYONE_LLM_BASE_URL=<shim>`, `TACHYONE_LLM_MODEL=tachyone-slm`.
4. **The scoring of PRD §3.4 runs inside the shim.** It receives `chat/completions`, ranks candidate labels in the logits and **assembles the `answers` object at runtime** — the model never writes numbers, so `JSON ok` holds by construction and the "confidence is never generated text" rule survives intact.

## Why

* The owner's intent (clarified 2026-10-04): `munod/tachyone_slm` exists precisely so **nothing upstream changes**; the upstream repo is training/data-structure/evaluation *reference*.
* The previous framing (v1.2.0) assumed upstream integration surfaces (SDK export, CLI flag, cookbook migration, ADR-0017) — none of them is required to deliver a usable System-2 backend option.
* The JevBench submission (`fstandhartinger/jevbench#182`) clones upstream `main` **without a checkout**; a permanent read-only policy removes that vector entirely (`docs/jevbench-noninterference.md`).

## Trade-offs

* **Accepted:** no `tachyone.system_two` export, no CLI flag, no upstream cookbook migration — our cookbook ships in this repo instead.
* **Accepted:** no upstream `benchmarks/compare.py` row — we **import the harness read-only** (already the Phase 0 method) and record the SLM row in our own report.
* **Accepted:** §7.6 process criterion changed from "ADR-0017 published" to "stack decision recorded here (**DEC-002**)".
* **Rejected alternative:** adding a `TACHYONE_BACKEND=slm` upstream — it would require editing `build_backend()` (an `if`-chain over a fixed tuple) and violates point 2.

## Consequences

* PRD amended **v1.2.0 → v2.0.0** (§1.1, §1.4, §3.4, §5.2, §6, §7.6, §9/§10).
* Specs amended: `system-two-integration` (→ serving shim), `slm-lora-sft`, `slm-export-quant`, `slm-benchmark-docs`.
* `WS-AD-004` (pending upstream ADR) marked **superseded**; `WS-B-002` rewritten to "record DEC-002 locally".
* All execution phases (2–5) happen in this repo; `WS-B-022` keeps its pause trigger while its "never write upstream" half becomes permanent policy (point 2).
