#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/remote_common.sh"

"${ssh_cmd[@]}" \
  "echo 'Connected to:' \$(hostname) && \
   echo 'Project dir:' ${REMOTE_PROJECT_DIR} && \
   command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi || true"

