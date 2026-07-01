#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_DIR}"

mkdir -p logs
MASTER_LOG="logs/exp0_n50_deception_abstention.master.log"

set -a
if [[ -f .env.secrets ]]; then
  source .env.secrets
fi
set +a

export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
export HF_HOME="${HF_HOME:-/root/autodl-tmp/hf-cache}"

{
  echo "[START] deception_l1_self_n50"
  date
  PYTHONPATH=src /root/miniconda3/bin/python run_experiment0.py \
    --config configs/experiment0_deception_l1_self_n50.json \
    2>&1 | tee logs/deception_l1_self_n50.log

  echo "[START] abstention_natural_n50"
  date
  PYTHONPATH=src /root/miniconda3/bin/python run_experiment0.py \
    --config configs/experiment0_abstention_natural_n50.json \
    2>&1 | tee logs/abstention_natural_n50.log

  echo "[DONE] exp0_n50_deception_abstention"
  date
} 2>&1 | tee "${MASTER_LOG}"
