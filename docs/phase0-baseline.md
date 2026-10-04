# Phase 0 — System-2 baseline on the abstained slice

**Feature:** `baseline-system2` (BSL-01…07) · **Phase:** 0 · **Status:** measured

*GPU:* NVIDIA GeForce RTX 3060 · *run:* 2026-10-03T12:41:32+00:00 · *protocol:* PRD §2 (sequential, batch=1, warm-up excluded, same rows, same metric implementation, GPU declared) · *harness:* `benchmarks/compare.py`

Every table below is rendered from the artifacts in `benchmarks/results/`; an absent artifact renders as **not measured**.

## 1. Slice sizes (BSL-02)

Slice = eval-set rows where System-1's wire confidence is below τ (`tachyone.handoff.assess_response` rule: `max(probabilities)` for `choice`/`score`, `max(p, 1-p)` for `noul`).

| Eval set | rows | System-1 acc (full) | τ=0.6 slice | share | System-1 acc on slice | kept |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `eval_en` | 1500 | 1.000 | **1** | 0.0007 | 1.000 | 1499 |
| `eval_en_domains` | 7500 | 1.000 | **4** | 0.0005 | 1.000 | 7496 |
| `eval_multi` | 1500 | 0.893 | **18** | 0.0120 | 0.278 | 1482 |
| `eval_multi_domains` | 7500 | 0.914 | **264** | 0.0352 | 0.473 | 7236 |

### τ sensitivity (a slice must have a denominator to be quotable)

| Eval set | τ=0.30 | τ=0.50 | τ=0.60 | τ=0.70 | τ=0.80 | τ=0.90 | τ=0.95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `eval_en` | 0 (0.0000) | 1 (0.0007) | 1 (0.0007) | 1 (0.0007) | 2 (0.0013) | 4 (0.0027) | 25 (0.0167) |
| `eval_en_domains` | 0 (0.0000) | 3 (0.0004) | 4 (0.0005) | 4 (0.0005) | 9 (0.0012) | 56 (0.0075) | 363 (0.0484) |
| `eval_multi` | 0 (0.0000) | 6 (0.0040) | 18 (0.0120) | 50 (0.0333) | 67 (0.0447) | 104 (0.0693) | 119 (0.0793) |
| `eval_multi_domains` | 17 (0.0023) | 170 (0.0227) | 264 (0.0352) | 375 (0.0500) | 527 (0.0703) | 721 (0.0961) | 833 (0.1111) |

## 2. Candidate accuracy on the identical slice (BSL-03 / BSL-07)

Accuracy counts a contract failure as wrong; `JSON ok` is the share of rows that produced a contract-valid payload at all (failures are recorded, never dropped).

### `eval_en`

n = **1** abstained rows (of 1500; τ = 0.6)

| Engine | n answered | Accuracy | JSON ok | p50 (ms) | p95 (ms) | items/s | VRAM (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| System-1 (encoder) | 1 | 1.000 | 1.000 | 401.94 | 401.94 | 2.5 | 1743 |
| SLM base qwen2.5:0.5b (Ollama) | 0 | 0.000 | 0.000 | 576.31 | 576.31 | 1.7 | 0 |
| ling-tiny (llama-server Q4) | 1 | 1.000 | 1.000 | 1079.34 | 1079.34 | 0.9 | 4906 |
| ornith-9b (llama-server Q4) | 1 | 1.000 | 1.000 | 1715.64 | 1715.64 | 0.6 | 5512 |

### `eval_en_domains`

n = **4** abstained rows (of 7500; τ = 0.6)

| Engine | n answered | Accuracy | JSON ok | p50 (ms) | p95 (ms) | items/s | VRAM (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| System-1 (encoder) | 4 | 1.000 | 1.000 | 364.04 | 464.90 | 2.6 | 1776 |
| SLM base qwen2.5:0.5b (Ollama) | 0 | 0.000 | 0.000 | 891.64 | 1917.96 | 0.9 | 0 |
| ling-tiny (llama-server Q4) | 3 | 0.500 | 0.750 | 1735.09 | 11548.29 | 0.2 | 4908 |
| ornith-9b (llama-server Q4) | 4 | 1.000 | 1.000 | 3241.37 | 5089.88 | 0.3 | 5512 |

### `eval_multi`

n = **18** abstained rows (of 1500; τ = 0.6)

| Engine | n answered | Accuracy | JSON ok | p50 (ms) | p95 (ms) | items/s | VRAM (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| System-1 (encoder) | 18 | 0.278 | 1.000 | 25.87 | 101.89 | 24.0 | 2868 |
| SLM base qwen2.5:0.5b (Ollama) | 12 | 0.000 | 0.667 | 261.92 | 35920.71 | 0.1 | 0 |
| ling-tiny (llama-server Q4) | 13 | 0.000 | 0.722 | 1856.74 | 100824.66 | 0.1 | 4922 |
| ornith-9b (llama-server Q4) | 18 | 0.889 | 1.000 | 5834.05 | 8098.47 | 0.2 | 5512 |

### `eval_multi_domains`

n = **264** abstained rows (of 7500; τ = 0.6)

| Engine | n answered | Accuracy | JSON ok | p50 (ms) | p95 (ms) | items/s | VRAM (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| System-1 (encoder) | 264 | 0.473 | 1.000 | 56.36 | 76.63 | 16.4 | 3033 |
| SLM base qwen2.5:0.5b (Ollama) | 123 | 0.098 | 0.466 | 554.30 | 1214.97 | 0.8 | 0 |
| ling-tiny (llama-server Q4) | 148 | 0.311 | 0.561 | 3980.93 | 13179.47 | 0.1 | 4922 |
| ornith-9b (llama-server Q4) | 250 | 0.723 | 0.947 | 6736.86 | 37374.23 | 0.1 | 5512 |

## 3. Context coverage: 2,048 vs 4,096 (BSL-05)

Static token count under the Qwen2.5 tokenizer (wire = state + questions + JSON overhead; `+system` adds the measured system prompt).

| Eval set | view | rows | p50 | p95 | max | over 2048 | over 4096 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `eval_en` | full (+system) | 1500 | 503.0 | 566.0 | 1328 | **0** | 0 |
| `eval_en` | slice (+system) | 1 | 959.0 | 959.0 | 959 | **0** | 0 |
| `eval_en_domains` | full (+system) | 7500 | 505.0 | 580.0 | 1427 | **0** | 0 |
| `eval_en_domains` | slice (+system) | 4 | 917.5 | 973.5 | 976 | **0** | 0 |
| `eval_multi` | full (+system) | 1500 | 512.0 | 602.0 | 1482 | **0** | 0 |
| `eval_multi` | slice (+system) | 18 | 506.0 | 654.2 | 1075 | **0** | 0 |
| `eval_multi_domains` | full (+system) | 7500 | 518.0 | 645.0 | 1778 | **0** | 0 |
| `eval_multi_domains` | slice (+system) | 264 | 589.0 | 641.6 | 1573 | **0** | 0 |

## 4. Composite yardstick — System-1 only (BSL-06)

Published references (`benchmarks/report.md`, git `18bdc27`, RTX 3060) — the bar Phase 4/5 must not regress against:

| Eval set | published entry | n | Accuracy | ECE |
| --- | --- | ---: | ---: | ---: |
| `eval_en` | english | 1500 | 1.000 | 0.006 |
| `eval_en_domains` | english five-domain | 7500 | 1.000 | 0.009 |
| `eval_multi` | multilingual | 1500 | 0.895 | 0.062 |
| `eval_multi_domains` | multilingual five-domain | 7500 | 0.997 | 0.001 |

## 5. Protocol notes and deviations (read before quoting a number)

1. **`-n 1024` generation cap on `llama-server`** (rows `ling`, `ornith` and both context arms). The wire payload carries no `max_tokens`, so the published runs let a malformed answer generate up to `-c 8192` tokens — measured here at **6,024 tokens ≈ 39 s for a single row**. A contract-valid answer needs < 400 tokens; the cap only truncates pathological generations, which are parse failures either way. **Accuracy and `JSON ok` are unaffected; the failure-dominated p95 tail is shorter than the published one** (`docs/compare.md` documents that tail as failure-dominated regardless).
2. **Ollama rows ran before the cap** (`num_predict` unlimited, context 4096), so their p95 tail is *not* directly comparable with the capped llama-server rows.
3. **Temperature**: fitted by the harness on a 192-row validation split (64 rows per primitive from `train_{en,multi}.jsonl`), never on the reported slice. The 1- and 4-row English slices ran with a fixed `T=1.0` — a fit would burn 192 LLM calls to calibrate 1–4 test rows and does not move argmax accuracy.
4. **Ollama greedy variant**: the payload carries no `temperature`, so `qwen2.5:0.5b-phase0` was created locally from `qwen2.5:0.5b-instruct` with `PARAMETER temperature 0 / seed 42 / num_ctx 4096` (published protocol is `--temp 0 --seed 42`). Nothing was pushed to the Ollama registry.
5. **System-1 adapters are the deployable Hub ones** (`munod/tachyone-en`/`-multi`). The five-domain fitted-bank checkpoints quoted in `benchmarks/report.md` (`multi_b5b_fit_bank`, 0.997) are **not distributed** (no Hub model, no release asset), so they cannot be measured here: System-1 on `eval_multi_domains` scores **0.9145 full-set / 0.4735 on the slice** with the deployable adapter.
6. **Ollama VRAM is not in the artifacts** — the harness resolves the server pid by matching `llama-server` only. Measured separately after the runs: **718 MiB** (`ollama ps` + `nvidia-smi`, 622 MB weights resident, 100% GPU, ctx 4096).
7. **`eval_en` / `eval_en_domains` slices are 1 and 4 rows.** Their percentages are reported with the denominator, per the spec's edge case — they are too small to carry a published target.

## 6. Environment

```json
{
  "command": "/home/thiago/Documentos/Projetos/TachyOne_SLM/benchmarks/phase0_build_slice.py --data data/eval_en.jsonl --slice-out /home/thiago/Documentos/Projetos/TachyOne_SLM/benchmarks/results/phase0_slice_eval_en.jsonl --report-out /home/thiago/Documentos/Projetos/TachyOne_SLM/benchmarks/results/phase0_slice_eval_en.json",
  "cwd": "/tmp/opencode/tachyone",
  "gpu": "NVIDIA GeForce RTX 3060",
  "platform": "Linux-6.12.108-1-MANJARO-x86_64-with-glibc2.44",
  "processor": "x86_64",
  "python": "3.12.13",
  "timestamp": "2026-10-03T12:41:32+00:00",
  "torch": "2.14.0+cu130",
  "vram_total_mb": 11906
}
```

