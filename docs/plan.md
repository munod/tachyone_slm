# Execution Plan — Phases 0–5

> ⏸️ **PAUSED (2026-10-04)** — see `docs/jevbench-noninterference.md` (freeze until JevBench
> #182 closes + board published) and `.specs/HANDOFF.md` (resume protocol).
> Derived from **PRD v1.2.0** (`tachyone_prd.md`) §6 (plan), §7 (acceptance), §8 (risks), §9 (traceability).
> Status of every phase: **Phase 0 ✅ (2026-10-03)** and **Phase 1 ✅ (2026-10-04)** complete;
> Phases 2–5 **PAUSED** (WS-B-022; Phase 2 also gated by ADR-0017) — see `.specs/project/ROADMAP.md`.

---

## 1. Timeline

```
[Phase 0: Baseline System-2] ► [Phase 1: Data] ► [Phase 2: SFT/LoRA] ► [Phase 3: Export] ► [Phase 4: Integration] ► [Phase 5: Benchmark & Docs]
       (Day 1)                    (Days 2–3)         (Days 4–5)          (Day 6)            (Days 7–8)                (Days 9–10)
```

| Phase | Days | Objective | Key outputs | Spec |
| --- | --- | --- | --- | --- |
| **0 — Baseline System-2** ✅ | 1 | Measure System-1 + LLM candidates on the abstained slice; **fix numeric accuracy targets in PRD §2**; A/B context 2,048 vs 4,096 | ✅ `docs/phase0-baseline.md` + 24 artifacts; PRD §2 fixed (`≥0.723`/`≥0.474`, anchor n=264); context decided **2,048** | `.specs/features/baseline-system2/spec.md` |
| **1 — SFT Mixture** ✅ | 2–3 | Generate `Tachyone-SLM-Mixture-v1` from the existing pipeline | ✅ config + 85,500 raw → **50,180 clean** (dedup 41.31%), split 45,175/5,005, 50,180 pairs, audit **pass 0/0**, 16 tests, `docs/slm-mixture-v1.md` | `.specs/features/slm-mixture-data/spec.md` |
| **2 — SFT/LoRA Training** | 4–5 | Fine-tune the 0.5B base with the frozen §3.2 recipe | **ADR-0017 first**, adapter/checkpoint, run manifest, worst-cell eval, slice-vs-target readout (~4–12 h GPU) | `.specs/features/slm-lora-sft/spec.md` |
| **3 — Export & Quantization** | 6 | Merge + deployable artifacts within the VRAM budget | Merged weights, bf16/INT4@3060/FP8@L4 variants, VRAM table, engine flags manifest | `.specs/features/slm-export-quant/spec.md` |
| **4 — Integration** | 7–8 | Official `system_two()`, scoring decoding, calibration, τ/retry/fallback | SDK/CLI surfaces, cookbook migrated, calibration fit, coverage/`JSON ok` evidence; **contract suite untouched** | `.specs/features/system-two-integration/spec.md` (+ `design.md`) |
| **5 — Benchmark & Docs** | 9–10 | Measure all KPIs; publish the English doc set as one unit | New `compare.py` engine row, `benchmarks/report.md`, ADR-0017/cookbook/README/model-card/CHANGELOG updated together | `.specs/features/slm-benchmark-docs/spec.md` |

---

## 2. Daily gates (PRD §6 — every day)

| Gate | Command |
| --- | --- |
| Lint | `ruff check` |
| Format | `ruff format --check` |
| Types | `pyright` |
| Tests | `pytest` |
| Docs | `mkdocs build --strict` |
| Commits | Conventional Commits |
| Language | Docs/PRs in **English** (`AGENTS.md` / `CONTRIBUTING.md`) |

**Hard prerequisites (stop conditions):**

- Phase 2 cannot start before **ADR-0017** is published ("ADR-0017 antes de codar", §6) — tracked as blocker **WS-B-002**.
- Phase 4/5 acceptance numbers depend on Phase 0 fixing the slice targets — blocker **WS-B-001 ✅ RESOLVED** (PRD v1.2.0 §2).

---

## 3. Acceptance gates (PRD §7 ↔ evidence)

| # | Criterion | Evidence produced by | Target |
| --- | --- | --- | --- |
| 7.1 | Contract compliance | Phase 4/5 harness | `JSON ok` = **1.000**, both sets |
| 7.2 | Quality in the System-2 role | Phases 0/2/4/5 | Coverage **100%**; slice ≥ LLM candidate **and** ≥ System-1 (target fixed in Phase 0); composite ≥ System-1-only; `eval_en` stays **1.000**; dataset golden-hashes intact |
| 7.3 | Latency | Phase 5 | p50 **< 20 ms**, p95 **< 50 ms** in-engine; **≥ 50×** `ornith-9b`; stretch **< 8 ms** only with §4 preconditions |
| 7.4 | Calibration | Phase 4/5 | ECE (10-bin, fitted per primitive × language) **≤ 0.030**, Brier + `Conf` published alongside |
| 7.5 | Resources | Phases 3/5 | Additional VRAM ≤ **1.6 GB** (bf16) / ≤ **1.0 GB** (INT4/FP8); throughput ≥ **20 items/s** |
| 7.6 | Process | Phase 5 | ADR-0017 published; gates green; doc surfaces updated **as a set** |

**KPI ↔ section ↔ acceptance traceability** lives in PRD §9; requirement-level traceability lives in each feature spec (`Requirement Traceability` tables).

---

## 4. Risks (PRD §8) and how the plan answers them

| Risk | Evidence | Mitigation in the plan | Watch phase |
| --- | --- | --- | --- |
| Training variance (same seed → 0.76–0.79) | L-005/L-006 (B-9) | Control runs before any conclusion; pinned seed (SFT-04) | 2 |
| The abstained slice does not improve with 0.5B | JevBench hard ≈ chance; `noul` blind to rubric | **Phase 0 fixes the target before training**; a miss is recorded and the role re-evaluated (BSL-04, DOC-11) | 0, 5 |
| Eval contamination via synthetic mixture | L-005 + frozen-eval rule | Overlap audit in Phase 1; public probes as external check (DAT-04) | 1 |
| Stretch < 8 ms unreachable | Roofline: decode is bandwidth-bound; full JSON ≈ 60 tok | Hard meta stays **< 20 ms**; stretch conditioned on FP8@L4 + minimal output, *measured, not promised* (DOC-02, WS-B-012) | 5 |
| New serving deps (vLLM/TRT-LLM) vs `uv` stack | extras `serve`/`train`/`fast` precedent | Decision in ADR-0017; extras **opt-in** (EXP-08) | 3 |
| No Ada GPU for the stretch | L4 availability varies | Main path (3060/INT4) never depends on Ada (EXP-05) | 3, 5 |
| English regression from fine-tuning | B-11/B-12 retrain history | Early stopping on `eval_en`; System-1 never retrained (SFT-05) | 2 |

---

## 5. Current status — Phases 0 and 1 **COMPLETE**

**Phase 0 (2026-10-03):** 24 artifacts + `docs/phase0-baseline.md`; PRD **v1.1.0 → v1.2.0**; spec `baseline-system2` 7/7; `STATE.md` `WS-AD-007/008` + `WS-L-001…004`.

**Phase 1 (2026-10-04):** `Tachyone-SLM-Mixture-v1` — 85,500 raw → **50,180 clean** records (41.31% frozen-set collisions removed per DAT-04 AC2), split **45,175/5,005**, **50,180 validated SFT pairs** (0 rejected), audit **pass** (overlap 0/0 over 18,000 frozen records), 35/35 cells, 16 tests green; dataset card `docs/slm-mixture-v1.md`.

**Headline numbers** (RTX 3060, `benchmarks/compare.py` protocol, τ = 0.6):

| Slice | n | System-1 | `ornith-9b` | `ling-tiny` | SLM base 0.5B |
| --- | ---: | ---: | ---: | ---: | ---: |
| `eval_multi_domains` **(anchor)** | **264** | 0.474 | **0.723** | 0.311 | 0.098 |
| `eval_multi` (secondary) | 18 | 0.278 | 0.889 | 0.000 | 0.000 |
| `eval_en` / `eval_en_domains` | 1 / 4 | 1.000 / 1.000 | — *no usable denominator* | — | — |

- **Context A/B → 2,048** (both arms identical; 0 of 18,000 rows exceed 2,048 tokens; max 1,360 with system prompt).
- **`JSON ok` on the slice:** 1.000 (System-1) · 0.947 (ornith) · 0.561 (ling) · **0.466 (SLM base)** — the gap Phases 1–2 must close.
- **VRAM of the SLM base:** 718 MiB (budget ≤1.0 GB already met).
- **p50 of the SLM base without SFT:** 276 ms (llama-server) / 554 ms (Ollama) → still 10–25× off the < 20 ms KPI; the scoring mode (§3.4) + a dedicated engine are what must close it.

**Pending (next):**

1. Maintainer approval of PRD v1.2.0 (**WS-B-015** — closes Phase 0).
2. **ADR-0017 before any training code** (**WS-B-002**, gates Phase 2 — the only blocker left between here and GPU time).
3. Publish `Tachyone-SLM-Mixture-v1` to HF `munod/tachyone_slm` (**WS-B-019**, only on request — nothing uploads automatically).
4. Phase 2 must gate on the worst cells: `noul` (13,607 pairs) and `en`×`support` (451 records) — **WS-B-021**.
5. Decide the English-slice denominator question (WS-B-017) before Phase 5 acceptance.
