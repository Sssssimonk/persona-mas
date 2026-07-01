#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: scripts/launch_tmux_experiment.sh <session> <config.json> <log-file>" >&2
  exit 1
fi

SESSION="$1"
CONFIG_PATH="$2"
LOG_FILE="$3"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"
mkdir -p "$(dirname "${LOG_FILE}")"

if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "tmux session already exists: ${SESSION}"
  tmux ls
  exit 0
fi

tmux new-session -d -s "${SESSION}" "\
  cd '${PROJECT_ROOT}' && \
  export HF_ENDPOINT=https://hf-mirror.com && \
  export HF_HOME=/root/autodl-tmp/hf-cache && \
  PYTHONPATH=src /root/miniconda3/bin/python run_experiment0.py --config '${CONFIG_PATH}' \
  2>&1 | tee '${LOG_FILE}'"

tmux ls
