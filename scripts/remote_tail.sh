#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/remote_common.sh"

LOG_FILE="${1:-${REMOTE_LOG_FILE}}"
LINES="${2:-100}"

"${ssh_cmd[@]}" "cd '${REMOTE_PROJECT_DIR}' && \
  if [[ -f '${LOG_FILE}' ]]; then \
    tail -n '${LINES}' '${LOG_FILE}'; \
  else \
    echo 'No log file found at ${LOG_FILE}'; \
  fi"
