#!/usr/bin/env bash
# Phase 0 — serialized candidate runs over the abstained slices (BSL-03 / BSL-07).
#
# One engine at a time: benchmark runs must never overlap or every latency number is
# polluted (benchmarks/README.md). Protocol per PRD §2: sequential, batch=1, warm-up
# excluded, same rows, same metric implementation, GPU declared in the artifact.
#
# Engines, in order:
#   1. Ollama  qwen2.5:0.5b-phase0  — the SLM base served locally (greedy variant:
#      temperature 0 / seed 42 / num_ctx 4096, created from qwen2.5:0.5b-instruct)
#   2. llama-server ling-tiny        — Q4_K_M, --temp 0 --seed 42 (published candidate)
#   3. llama-server ornith-9b        — Q4_K_M, --temp 0 --seed 42 (published candidate)
#   4. System-1 (encoder backend)    — same rows, for the slice-side latency/accuracy row
#
# Temperature is fitted on a 192-row validation split (64 per primitive, built from
# train_{en,multi}.jsonl) for slices with >= 10 rows; the 1- and 4-row English slices run
# with a fixed T=1.0 (a fit would burn 192 LLM calls to calibrate 1-4 test rows, and
# temperature does not move argmax accuracy).
#
# Idempotent: an existing artifact is skipped, so a killed run resumes where it stopped.
#
# Documented deviation from the 2026-09-26 published runs: llama-server is started with
# `-n 1024`. The wire payload carries no `max_tokens`, so the published `-c 8192` runs let a
# malformed answer generate up to 8192 tokens (observed here: 6,024 tokens ≈ 39 s for a
# single row, which alone made one dataset take ~1 h). A contract-valid answer needs well
# under 400 tokens; the cap only truncates pathological generations, which are parse
# failures either way — accuracy and JSON ok are unaffected, the failure-dominated p95 tail
# is shorter (the tail is documented as failure-dominated in docs/compare.md regardless).
set -uo pipefail

REPO=/tmp/opencode/tachyone
WS=/home/thiago/Documentos/Projetos/TachyOne_SLM
OUT=$WS/benchmarks/results
GGUF=$HOME/.cache/tachyone/gguf
LOGS=$OUT/logs
mkdir -p "$LOGS"
cd "$REPO" || exit 1
export TACHYONE_LLM_RETRIES=1

DATASETS=(eval_multi eval_multi_domains eval_en eval_en_domains)

have () { [[ -s "$1" ]]; }  # artifact already produced by a previous (possibly interrupted) run

slice_args () {
  local ds=$1 n
  n=$(wc -l < "$OUT/phase0_slice_${ds}.jsonl")
  local line="--format jsonl --data $OUT/phase0_slice_${ds}.jsonl --per-task 500"
  if (( n >= 10 )); then
    line+=" --warmup 3"
    if [[ "$ds" == eval_multi || "$ds" == eval_multi_domains ]]; then
      line+=" --val-data $OUT/phase0_val_multi.jsonl"
    else
      line+=" --val-data $OUT/phase0_val_en.jsonl"
    fi
  else
    line+=" --warmup 0 --temperature 1.0"
  fi
  echo "$line"
}

run_llm () {
  local tag=$1 base=$2 model=$3
  for ds in "${DATASETS[@]}"; do
    local -a extra
    if have "$OUT/phase0_${tag}_${ds}.json"; then
      echo "[$tag] $ds — skip (artifact exists)"
      continue
    fi
    read -ra extra < <(slice_args "$ds")
    echo "[$tag] $ds (model=$model) $(date +%H:%M:%S)"
    : > "$LOGS/phase0_${tag}_${ds}.log"
    uv run python -m benchmarks.compare run --engine llm \
      --llm-base-url "$base" --llm-model "$model" --llm-timeout 300 \
      "${extra[@]}" \
      --out "$OUT/phase0_${tag}_${ds}.json" \
      >> "$LOGS/phase0_${tag}_${ds}.log" 2>&1
    echo "  exit=$? -> phase0_${tag}_${ds}.json"
  done
}

run_encoder () {
  local tag=system1
  for ds in "${DATASETS[@]}"; do
    local -a extra
    if have "$OUT/phase0_${tag}_${ds}.json"; then
      echo "[$tag] $ds — skip (artifact exists)"
      continue
    fi
    read -ra extra < <(slice_args "$ds")
    echo "[$tag] $ds"
    : > "$LOGS/phase0_${tag}_${ds}.log"
    TACHYONE_BACKEND=encoder \
    TACHYONE_ADAPTERS="tachyone-en=checkpoints/en,tachyone-multi=checkpoints/multi" \
    uv run python -m benchmarks.compare run --engine tachyone --backend encoder \
      "${extra[@]}" \
      --out "$OUT/phase0_${tag}_${ds}.json" \
      >> "$LOGS/phase0_${tag}_${ds}.log" 2>&1
    echo "  exit=$? -> phase0_${tag}_${ds}.json"
  done
}

SERVER_PID=""
start_llama () { # <gguf> <port> <alias>
  # a server left over from an interrupted run would hold the port and the VRAM
  pkill -f "llama-server .*--port $2" 2>/dev/null && sleep 3
  echo "[llama-server] starting $3 on port $2 ($(date +%H:%M:%S))"
  llama-server -m "$1" --host 127.0.0.1 --port "$2" -ngl 99 \
    --temp 0 --seed 42 -c 8192 -n 1024 --alias "$3" \
    > "$LOGS/phase0_server_$3.log" 2>&1 &
  SERVER_PID=$!
  local tries=0
  until curl -sf "http://127.0.0.1:$2/health" >/dev/null 2>&1; do
    tries=$((tries + 1))
    if (( tries > 180 )); then
      echo "[llama-server] $3 did not become healthy; see $LOGS/phase0_server_$3.log"
      return 1
    fi
    sleep 1
  done
  echo "[llama-server] $3 healthy (pid $SERVER_PID)"
}

stop_llama () {
  [[ -n "$SERVER_PID" ]] || return 0
  kill "$SERVER_PID" 2>/dev/null
  wait "$SERVER_PID" 2>/dev/null
  SERVER_PID=""
  sleep 3
  echo "[llama-server] stopped; VRAM released"
}

echo "=== Phase 0 LLM runs — $(date -Is) ==="
echo "--- engine 1/4: Ollama qwen2.5:0.5b-phase0 (SLM base) ---"
run_llm ollama "http://127.0.0.1:11434/v1" "qwen2.5:0.5b-phase0"

echo "--- engine 2/4: llama-server ling-tiny ---"
start_llama "$GGUF/Ling-3.0-tiny-Q4_K_M.gguf" 8081 ling-tiny
run_llm ling "http://127.0.0.1:8081/v1" ling-tiny
stop_llama

echo "--- engine 3/4: llama-server ornith-9b ---"
start_llama "$GGUF/Ornith-1.5-9B-Q4_K_M.gguf" 8082 ornith-9b
run_llm ornith "http://127.0.0.1:8082/v1" ornith-9b
stop_llama

echo "--- engine 4/4: System-1 (encoder) ---"
run_encoder

echo "=== done — $(date -Is) ==="
ls -la "$OUT"/phase0_*.json | awk '{print $NF, $5}'
