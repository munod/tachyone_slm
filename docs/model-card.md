# Model Card — TachyOne SLM

> **Status:** 🟡 **TEMPLATE — to be completed in Phase 5** (PRD §6, §7.6).
> Fields marked `TODO(Phase 5)` must be filled with measured values; fields formerly marked **to be measured (Phase 0)** were filled from the Phase 0 run of 2026-10-03 (`docs/phase0-baseline.md`).
> **No metric in this card may be invented** (decision WS-AD-006). Configuration values below are copied from PRD **v1.2.0** §3 — they are *decisions*, not measurements.

---

## Model details

| Field | Value |
| --- | --- |
| Model name | TachyOne SLM (`tachyone-latest` on the wire) — final name `TODO(Phase 5)` |
| Base model | `Qwen/Qwen2.5-0.5B-Instruct` (~494M active parameters; vocab 151,643; native context 32,768) |
| Service context | **2,048 tokens — decided in Phase 0** (A/B 2,048 vs 4,096 was a tie by construction: 0 of 18,000 eval rows exceed 2,048 tokens, max 1,360 with system prompt — WS-AD-007) |
| Model version / checkpoint hash | `TODO(Phase 5)` |
| Date released (first version) | `TODO(Phase 5)` |
| Model type | Decoder-only SLM, SFT via LoRA (merged for export) |
| Frameworks | `transformers` + `peft` (embedded engine); export via vLLM or TensorRT-LLM — **per ADR-0017 (pending)** |
| Quantization | bf16 (reference) · INT4 via AWQ/GPTQ @ RTX 3060 · FP8 @ NVIDIA L4 — `TODO(Phase 5: measured VRAM)` |
| License | `TODO(Phase 5)` — must inherit/track base-model license terms |
| Repository | code: [`munod/tachyone`](https://github.com/munod/tachyone) · specs: this workspace `.specs/` |

## Intended use

- **Primary:** local, local-first **System-2** of the TachyOne hybrid — invoked only when the System-1 encoder abstains (`assess_response(τ)` → `system_two()`), answering within the frozen wire contract (`docs/protocol.md`, ADR-0001).
- **Out-of-scope uses (PRD §1.4):** general-purpose chat/free text; replacing System-1; JevBench submission with this SLM; models ≥ 1B / MoE variants; multi-tenant/cloud serving.
- **Users:** maintainers/operators of the `munod/tachyone` classifier.

## Factors

| Factor | Coverage |
| --- | --- |
| Languages | `en, pt, es, fr, de, it, nl` (the 7 training languages, PRD §3.3) |
| Domains | `support, ecommerce, agent_tools, documents, voice` |
| Primitives | `choice`, `score`, `noul` (scoring mode, §3.4) |
| Slice of record | Abstained slice `confidence < τ` (benchmark τ = 0.6 reference; τ configurable, no universal default) |
| Known weak spot | The abstained slice itself: System-1's own accuracy there is **0.474** (`eval_multi_domains`, n=264) and **0.278** (`eval_multi`, n=18) — the slice is hard *by construction*, and at τ=0.6 the English sets barely abstain (n=1 / n=4) (Phase 0, WS-AD-008) |

## Metrics

*Targets come from PRD §2. The `Measured` column is filled only by harness runs under the §2 protocol (sequential, batch=1, warm-up excluded, same rows/metric, GPU declared) — **except the slice-accuracy target, which Phase 0 fixed**. The untrained base's Phase 0 numbers are listed below the table as the starting point, not as the model's result.*

| Metric | Target (PRD §2) | Measured |
| --- | --- | --- |
| Latency p50 (in-engine) | < 20 ms (stretch < 8 ms with §4 preconditions) | to be measured (Phase 5) |
| Latency p95 (in-engine) | < 50 ms | to be measured (Phase 5) |
| Relative speed | ≥ 50× `ornith-9b` p50 (refs 3,315 ms home / 6,844 ms probe / 6,737 ms slice) | to be measured (Phase 5) |
| Throughput (batch=1) | ≥ 20 items/s | to be measured (Phase 5) |
| Contract compliance (`JSON ok`) | 1.000 (both sets) | to be measured (Phase 5) |
| Accuracy — abstained slice (τ=0.6) | **≥ 0.723 (LLM candidate) and ≥ 0.474 (System-1)** — `eval_multi_domains`, n=264; fixed by Phase 0 (WS-AD-008) | to be measured (Phase 5) |
| Accuracy — composite (System-1 + handoff) | ≥ System-1-only (`eval_en` 1.000 · `eval_multi` 0.895 · five-domain 0.9975) | to be measured (Phase 5) |
| ECE (10-bin, temperature fitted) | ≤ 0.030 | to be measured (Phase 4/5) |
| Brier + `Conf` | published alongside ECE (L-015 — never ECE alone) | to be measured (Phase 4/5) |
| Additional VRAM | ≤ 1.6 GB (bf16) · ≤ 1.0 GB (INT4/FP8) | to be measured (Phase 3/5) |
| Handoff coverage | 100% of abstined items (max 1 retry) | to be measured (Phase 4) |

**Phase 0 baselines — the untrained `qwen2.5:0.5b` base** (2026-10-03, RTX 3060, `docs/phase0-baseline.md` §2 — starting point, *not* this model's result):

| | `eval_multi_domains` (n=264) | `eval_multi` (n=18) |
| --- | ---: | ---: |
| Slice accuracy (base, no SFT) | 0.098 | 0.000 |
| `JSON ok` (base) | 0.466 | 0.667 |
| p50 / p95 (base) | 276 ms / 1.2 s | 162 ms / — |
| Slice accuracy, incumbents | `ornith-9b` 0.723 · `ling-tiny` 0.311 · System-1 0.474 | 0.889 / 0.000 / 0.278 |
| VRAM (base, Ollama) | **718 MiB** (622 MB weights, 100% GPU, ctx 4096) | same |

## Evaluation data

| Set | Role | Notes |
| --- | --- | --- |
| `eval_en`, `eval_multi` | Primary accuracy + `JSON ok` sets in `benchmarks/compare.py` | Frozen — never trained on, never used for temperature fit |
| `eval_en_domains`, `eval_multi_domains` | Five-domain accuracy | Frozen (golden-hashes must remain intact, §7.2) |
| Public probes (`benchmarks/probes.md`) | External contamination check | Frozen |
| Abstained slice (`confidence < τ`) | System-2 quality slice | Defined at Phase 0: **τ=0.6 → 1 / 4 / 18 / 264 rows** across the four eval sets; anchor `eval_multi_domains` (n=264); τ sweep 0.30–0.95 recorded |

## Training data

| Field | Value |
| --- | --- |
| Dataset | `Tachyone-SLM-Mixture-v1`, generated by `training/generate_data.py` (existing pipeline) — [dataset card](slm-mixture-v1.md) |
| Config | `training/configs/data_sft_slm.json` — 7 languages, 5 domains, **seed 20261003**, 85,500 raw → **50,180 clean** records |
| Label derivation | From text only (ADR-0014/ADR-0015): `noul` phrase bank · `score` tone · `choice` state-named option |
| Rendered as | *(prompt = wire request §5.1 + `Answer:`)* → *(gold label for §3.4 scoring)*, re-parsed by `tachyone.wire.parse_request` at generation — **50,180 pairs, 0 rejected** |
| Split | Deterministic by `sha256(record bytes) % 10` → **45,175 train / 5,005 val** (byte-idempotent, golden-hash tested) |
| Contamination audit | **pass — overlap 0/0** (mixture + temperature-fit val) over 18,000 frozen eval records; 35,320 raw records removed (41.31%); record `artifacts/slm-mixture-v1/audit.json` |

## Training procedure (hyperparameters fixed by PRD §3.2)

| Hyperparameter | Value |
| --- | --- |
| Method | LoRA in bfloat16 |
| Target modules | `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj` |
| LoRA rank / alpha / dropout | r = 16 · α = 32 · dropout 0.05 |
| Learning rate | 2e-4, Cosine Decay |
| Batch | 32 effective (gradient accumulation; effective batch declared) |
| Optimizer | AdamW (8-bit/bitsandbytes optional if VRAM is tight — recorded in manifest) |
| Epochs | 3–5 with early stopping on `eval_en` **+** abstained slice |
| Seed | Pinned (AD-009); config verified pre-run (L-011) |
| Gating | Worst domain/language — never the average; never a routed harness (L-013) |
| Stack | `training/finetune_rlcd.py` + peft recommended; **ADR-0017 pending** |
| GPU / duration | RTX 3060 12 GB or L4 23 GB · ~4–12 h estimated (PRD §6) |
| Actual run manifest | `TODO(Phase 2)` — config hash, seed, per-epoch metrics, control-vs-experiment |

## Quantization & deployment

| Variant | Precision | Target GPU | VRAM (additional) |
| --- | --- | --- | --- |
| Main path | bf16 or INT4 (AWQ/GPTQ) | RTX 3060 (Ampere — **no FP8**) | to be measured (Phase 3) |
| Stretch path | FP8 | NVIDIA L4 (Ada/SM89) | to be measured (Phase 3) |

Serving: embedded engine (transformers/peft) default; vLLM / TensorRT-LLM optional (**ADR-0017 pending**); prefix caching + warm-up shapes per §4.3–4.4. Embedded vs external comparison: **to be measured (Phase 5)**.

## Calibration

Temperature scaling via `training/fit_calibration.py`, **per (primitive, language)**, grid 0.25–20.00 step 0.05, fit on the **train-split validation set only** (never on eval sets). Fitted temperatures: `TODO(Phase 4)`. Unreadable calibration assets warn **by name** (B-8) — never silent degradation.

## Ethical considerations & limitations

- **Local-first, single-tenant** by design; no cloud/multi-tenant serving (PRD §1.4).
- Confidence is **fitted**, not free text; downstream automation must still choose τ consciously (≈0.3 safety · ≈0.5 routing · ≈0.8 automation, PRD §5.3).
- The SLM inherits System-1's abstention behavior: it only sees items the encoder already flagged as uncertain — selection bias must be considered when reading accuracy numbers.
- Failure of the SLM never fails silently: 1 retry, then the documented chain SLM → remote LLM → human review (§5.3).

## Citation & changelog

- Product specification: `docs/tachyone_prd.md` (**PRD v1.2.0** — Phase 0 targets fixed).
- Phase 0 baseline report: `docs/phase0-baseline.md` (2026-10-03).
- Training data: `docs/slm-mixture-v1.md` (dataset card, 2026-10-04).
- This card: `TODO(Phase 5)` — must be updated together with `benchmarks/report.md`, `CHANGELOG.md`, README and ADR-0017 (AD-009 "as a set" rule).
