#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: scripts/remote_exec.sh '<command to run on remote>'" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/remote_common.sh"

REMOTE_COMMAND="$*"

"${ssh_cmd[@]}" "cd '${REMOTE_PROJECT_DIR}' && ${REMOTE_COMMAND}"

