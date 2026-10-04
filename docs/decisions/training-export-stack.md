# DEC-002 — Training & export/serving stack → **upstream ADR-0017 (PENDING)**

**Status:** ⏳ **Pending — ADR-0017 is PLANNED only.** It will be authored in [`munod/tachyone`](https://github.com/munod/tachyone) (Phases 2–3). **It is deliberately NOT drafted here** as if it were an upstream ADR.
**Workspace ID:** WS-AD-004 (`.specs/project/STATE.md`) · Blocker: **WS-B-002**
**PRD traceability:** §4.1 (fusion/export), §4.2 (hardware matrix), §5.4 (schema annex), §6 Fase 2 ("ADR-0017 antes de codar"), §8 (dependency risk) → acceptance §7.6

---

## Context

Two stack choices gate the implementation and must be recorded as architecture decisions upstream:

1. **Training stack (Phase 2):** how to run the LoRA/SFT fine-tune on RTX 3060 / L4.
2. **Export & serving stack (Phase 3):** vLLM (FP8) vs TensorRT-LLM, plus quantization tooling (AWQ/GPTQ) — and the **JSON Schema annex** of the contract used by constrained decoding (§5.4).

PRD §6 makes publication of ADR-0017 a **hard prerequisite of Phase 2**: *"ADR-0017 antes de codar"*. PRD §8 flags the dependency risk: new serving deps vs the repo's `uv` stack (precedent: extras `serve`/`train`/`fast` already exist).

## Planned scope of ADR-0017 (what it must decide)

| Topic | Candidates / constraints from PRD | PRD ref |
| --- | --- | --- |
| Training stack | **Recommended:** `training/finetune_rlcd.py` + `peft` of the repo itself; **Unsloth** only as an explicitly justified new extra | §6 Fase 2 |
| Export target | vLLM (FP8) **or** TensorRT-LLM | §4.1 |
| Quantization tooling | INT4 via **AWQ or GPTQ** for RTX 3060; **FP8 native only on Ada (L4)** | §4.2 |
| Dependency policy | extras **opt-in** under the existing `uv` extras pattern | §8 |
| Schema annex | Contract JSON Schema/grammar for constrained decoding, tested against `tests/test_contract_wire.py` | §5.4 |

## Decision criteria (to be applied when drafting)

- Main path must run on **RTX 3060 (Ampere, no FP8)** — the choice cannot make the primary path depend on Ada (§4.2, §8).
- Must support **prefix caching** and **warm-up/CUDA Graphs reuse as flags** (§4.3–4.4).
- Must fit the **additional VRAM budget**: ≤ 1.6 GB (bf16) / ≤ 1.0 GB (INT4/FP8) measured in-harness (§2).
- Must keep the repo gates green (`ruff`, `pyright`, `pytest`, `mkdocs --strict`) and follow conventional commits / English docs (§6).

## Consequences while pending

- 🚧 **Phase 2 is blocked** (blocker WS-B-002): no training code before the ADR exists.
- 🚧 Phase 3 cannot pick an export engine; specs `slm-lora-sft` and `slm-export-quant` reference the ADR instead of deciding.
- ✅ This workspace stays honest: no fabricated ADR content, no invented stack verdict (WS-AD-006).

## Traceability

- Requirement IDs: `SFT-01` (hard gate), `EXP-02`, `EXP-08`, `INT-14` (schema annex)
- Acceptance: §7.6 ("ADR-0017 publicado") — the only criterion that can close with an upstream artifact
- Next action: draft ADR-0017 in `munod/tachyone` at the start of Phase 2 → review → publish; then update `.specs/project/STATE.md` (close WS-B-002) and this record's status.
