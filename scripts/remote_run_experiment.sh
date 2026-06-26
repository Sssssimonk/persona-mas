#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: scripts/remote_run_experiment.sh <config.json>" >&2
  exit 1
fi

CONFIG_PATH="$1"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/remote_common.sh"

"${ssh_cmd[@]}" "cd '${REMOTE_PROJECT_DIR}' && \
  set -a && [[ -f .env.secrets ]] && source .env.secrets || true && set +a && \
  export HF_ENDPOINT=\"\${HF_ENDPOINT:-https://hf-mirror.com}\" && \
  export HF_HOME=\"\${HF_HOME:-/root/autodl-tmp/hf-cache}\" && \
  PYTHONPATH=src /root/miniconda3/bin/python run_experiment0.py --config '${CONFIG_PATH}'"
