#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: scripts/remote_tmux_start.sh <session_name> '<command to run inside tmux>' [log_file]" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/remote_common.sh"

SESSION_NAME="$1"
shift
REMOTE_COMMAND="$1"
LOG_FILE="${2:-logs/${SESSION_NAME}.log}"

if [[ ! "${SESSION_NAME}" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "session_name may only contain letters, numbers, dot, underscore, and hyphen" >&2
  exit 1
fi

printf -v REMOTE_COMMAND_Q "%q" "${REMOTE_COMMAND}"

"${ssh_cmd[@]}" "cd '${REMOTE_PROJECT_DIR}' && \
  mkdir -p \"\$(dirname '${LOG_FILE}')\" && \
  tmux new-session -d -s '${SESSION_NAME}' \
    \"cd '${REMOTE_PROJECT_DIR}' && bash -lc ${REMOTE_COMMAND_Q} 2>&1 | tee -a '${LOG_FILE}'\""

echo "Started tmux session '${SESSION_NAME}' on ${SSH_TARGET}"
echo "Log: ${REMOTE_PROJECT_DIR}/${LOG_FILE}"
