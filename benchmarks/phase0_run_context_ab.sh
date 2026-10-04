#!/usr/bin/env bash
# Phase 0 — service-context A/B: 2,048 vs 4,096 tokens (BSL-05 / PRD §3.1).
#
# Same engine, same rows, same flags — only `-c` changes. Accuracy answers "does the extra
# context buy coverage?", latency answers "what does it cost?" (§3.1: a hypothesis to
# measure, not an assumption). Sequential, one server at a time.
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
MODEL=$GGUF/Qwen2.5-0.5B-Instruct-Q4_K_M.gguf
PORT=8083

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

for CTX in 2048 4096; do
  echo "--- context $CTX ---"
  pkill -f "llama-server .*--port $PORT" 2>/dev/null && sleep 3
  llama-server -m "$MODEL" --host 127.0.0.1 --port "$PORT" -ngl 99 \
    --temp 0 --seed 42 -c "$CTX" -n 1024 --alias "qwen05b-ctx$CTX" \
    > "$LOGS/phase0_server_qwen_ctx$CTX.log" 2>&1 &
  PID=$!
  tries=0
  until curl -sf "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; do
    tries=$((tries + 1))
    if (( tries > 180 )); then
      echo "server ctx$CTX unhealthy; see $LOGS/phase0_server_qwen_ctx$CTX.log"
      kill "$PID" 2>/dev/null
      exit 1
    fi
    sleep 1
  done
  for ds in "${DATASETS[@]}"; do
    if [[ -s "$OUT/phase0_ctx${CTX}_${ds}.json" ]]; then
      echo "  ctx=$CTX $ds — skip (artifact exists)"
      continue
    fi
    local_args=()
    read -ra local_args < <(slice_args "$ds")
    echo "  ctx=$CTX $ds ($(date +%H:%M:%S))"
    uv run python -m benchmarks.compare run --engine llm \
      --llm-base-url "http://127.0.0.1:$PORT/v1" --llm-model "qwen05b-ctx$CTX" \
      --llm-timeout 300 \
      "${local_args[@]}" \
      --out "$OUT/phase0_ctx${CTX}_${ds}.json" \
      >> "$LOGS/phase0_ctx${CTX}_${ds}.log" 2>&1
    echo "    exit=$? -> phase0_ctx${CTX}_${ds}.json"
  done
  kill "$PID" 2>/dev/null
  wait "$PID" 2>/dev/null
  sleep 3
done
echo "=== context A/B done — $(date -Is) ==="
