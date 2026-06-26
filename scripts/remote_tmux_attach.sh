#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/remote_common.sh"

SESSION_NAME="${1:-${REMOTE_TMUX_SESSION}}"

"${ssh_cmd[@]}" -t "tmux attach -t '${SESSION_NAME}'"
