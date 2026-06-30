#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_DIR}"

mkdir -p logs
MASTER_LOG="logs/exp0_abstention_deception_shutdown.master.log"

{
  echo "[START] exp0_abstention_deception_shutdown"
  date

  set -a
  if [[ -f .env.secrets ]]; then
    source .env.secrets
  fi
  set +a

  export HF_ENDPOINT="https://hf-mirror.com"
  export HF_HOME="/root/autodl-tmp/hf-cache"

  echo "[ENV] HF_ENDPOINT=${HF_ENDPOINT}"
  echo "[ENV] HF_HOME=${HF_HOME}"

  echo "[RUN] abstention_n100"
  PYTHONPATH=src /root/miniconda3/bin/python run_experiment0.py \
    --config configs/experiment0_abstention_n100.json \
    2>&1 | tee logs/abstention_n100.log
  echo "[DONE] abstention_n100"
  date

  echo "[RUN] deception_n100"
  PYTHONPATH=src /root/miniconda3/bin/python run_experiment0.py \
    --config configs/experiment0_deception_n100.json \
    2>&1 | tee logs/deception_n100.log
  echo "[DONE] deception_n100"
  date

  echo "[SHUTDOWN] all experiments succeeded"
  /usr/bin/shutdown
} 2>&1 | tee "${MASTER_LOG}"
