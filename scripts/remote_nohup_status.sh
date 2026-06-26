#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: scripts/remote_nohup_status.sh <job_name> [tail_lines]" >&2
  exit 1
fi

JOB_NAME="$1"
TAIL_LINES="${2:-80}"

if [[ ! "${JOB_NAME}" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "job_name may only contain letters, numbers, dot, underscore, and hyphen" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/remote_common.sh"

REMOTE_LOG_PATH="logs/${JOB_NAME}.log"
REMOTE_PID_PATH="logs/${JOB_NAME}.pid"

"${ssh_cmd[@]}" "cd '${REMOTE_PROJECT_DIR}' && \
  if [[ -f '${REMOTE_PID_PATH}' ]]; then \
    PID=\$(cat '${REMOTE_PID_PATH}'); \
    ps -o pid,ppid,etime,stat,cmd -p \"\${PID}\" || true; \
  else \
    echo 'No pid file: ${REMOTE_PID_PATH}'; \
  fi; \
  echo '--- log tail ---'; \
  tail -n '${TAIL_LINES}' '${REMOTE_LOG_PATH}' 2>/dev/null || true"

