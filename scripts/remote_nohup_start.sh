#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: scripts/remote_nohup_start.sh <job_name> '<command to run on remote>'" >&2
  exit 1
fi

JOB_NAME="$1"
shift
REMOTE_COMMAND="$*"

if [[ ! "${JOB_NAME}" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "job_name may only contain letters, numbers, dot, underscore, and hyphen" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/remote_common.sh"

REMOTE_LOG_PATH="logs/${JOB_NAME}.log"
REMOTE_PID_PATH="logs/${JOB_NAME}.pid"
printf -v REMOTE_COMMAND_Q "%q" "${REMOTE_COMMAND}"

"${ssh_cmd[@]}" "cd '${REMOTE_PROJECT_DIR}' && \
  mkdir -p logs && \
  ( nohup bash -lc ${REMOTE_COMMAND_Q} > '${REMOTE_LOG_PATH}' 2>&1 < /dev/null & echo \$! > '${REMOTE_PID_PATH}' ) && \
  echo \"Started ${JOB_NAME} pid=\$(cat '${REMOTE_PID_PATH}')\" && \
  echo \"Log: ${REMOTE_PROJECT_DIR}/${REMOTE_LOG_PATH}\""

