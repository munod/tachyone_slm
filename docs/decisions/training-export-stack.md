# DEC-002 — Training & export/serving stack (local record)

**Status:** ⏳ **Pending — to be recorded in this repository before Phase 2 coding starts.** Since **PRD v2.0.0** there is **no upstream ADR**: `munod/tachyone` is read-only (`WS-AD-010` / DEC-005), so *this file* is the authoritative record of the decision.
**Workspace ID:** WS-AD-004 (superseded) → **WS-AD-010** · Blocker: **WS-B-002** (rewritten by PRD v2.0)
**PRD traceability:** §4.1 (fusion/export), §4.2 (hardware matrix), §5.4 (schema annex), §6 Fase 2 (*"decisão de stack registrada em DEC-002 antes de codar"*), §8 (dependency risk) → acceptance §7.6

---

## Context

Two stack choices gate the implementation and must be recorded as architecture decisions **here**:

1. **Training stack (Phase 2):** how to run the LoRA/SFT fine-tune on RTX 3060 / L4.
2. **Export & serving stack (Phase 3):** vLLM (FP8) vs TensorRT-LLM, plus quantization tooling (AWQ/GPTQ) — and the **JSON Schema annex** of the contract used by constrained decoding (§5.4).

PRD §6 (Fase 2) makes recording this decision a **hard prerequisite of Phase 2** (v1.x's "ADR-0017 antes de codar" became "decisão de stack registrada em DEC-002" when v2.0.0 removed upstream writes). PRD §8 still flags the dependency risk: new serving deps vs the repo's `uv` stack (precedent: extras `serve`/`train`/`fast` already exist) — for **our** dependencies now, since training/serving code lives in this repo.

## Planned scope of the decision (what it must decide)

| Topic | Candidates / constraints from PRD | PRD ref |
| --- | --- | --- |
| Training stack | **Recommended:** `training/finetune_rlcd.py` + `peft` of the repo itself; **Unsloth** only as an explicitly justified new extra | §6 Fase 2 |
| Export target | vLLM (FP8) **or** TensorRT-LLM | §4.1 |
| Quantization tooling | INT4 via **AWQ or GPTQ** for RTX 3060; **FP8 native only on Ada (L4)** | §4.2 |
| Dependency policy | extras **opt-in** under the existing `uv` extras pattern | §8 |
| Schema annex | Contract JSON Schema/grammar for constrained decoding, validated against `tests/test_contract_wire.py` **read-only** | §5.4 |

## Decision criteria (to be applied when drafting)

- Main path must run on **RTX 3060 (Ampere, no FP8)** — the choice cannot make the primary path depend on Ada (§4.2, §8).
- Must support **prefix caching** and **warm-up/CUDA Graphs reuse as flags** (§4.3–4.4).
- Must fit the **additional VRAM budget**: ≤ 1.6 GB (bf16) / ≤ 1.0 GB (INT4/FP8) measured in-harness (§2).
- Must keep the repo gates green (`ruff`, `pyright`, `pytest`, `mkdocs --strict`) and follow conventional commits / English docs (§6).

## Consequences while pending

- 🚧 **Phase 2 is blocked** (blocker WS-B-002): no training code before *this record* carries the decision — and not before the JevBench freeze lifts (`WS-B-022`).
- 🚧 Phase 3 cannot pick an export engine; specs `slm-lora-sft` and `slm-export-quant` reference **this record** instead of deciding.
- ✅ This workspace stays honest: no fabricated ADR content, no invented stack verdict (WS-AD-006).
- ✅ Nothing is written to `munod/tachyone` — ever (DEC-005 / `WS-AD-010`).

## Traceability

- Requirement IDs: `SFT-01` (hard gate), `EXP-02`, `EXP-08`, `INT-14` (schema annex)
- Acceptance: §7.6 (**"decisão de stack registrada (DEC-002, local)"** — amended by PRD v2.0.0)
- Next action: fill this record with the actual stack verdict at the start of Phase 2 (freeze permitting) → update `.specs/project/STATE.md` (close WS-B-002) and this status line.
