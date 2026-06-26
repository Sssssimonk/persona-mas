#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/remote_common.sh"

if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
  read -rsp "DeepSeek API key: " DEEPSEEK_API_KEY
  echo
fi

if [[ -z "${DEEPSEEK_API_KEY}" ]]; then
  echo "DEEPSEEK_API_KEY is empty." >&2
  exit 1
fi

DEEPSEEK_BASE_URL="${DEEPSEEK_BASE_URL:-https://api.deepseek.com}"

"${ssh_cmd[@]}" "cd '${REMOTE_PROJECT_DIR}' && umask 077 && cat > .env.secrets" <<EOF
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
DEEPSEEK_BASE_URL=${DEEPSEEK_BASE_URL}
EOF

"${ssh_cmd[@]}" "cd '${REMOTE_PROJECT_DIR}' && chmod 600 .env.secrets && test -s .env.secrets"

echo "Remote judge secret written to ${SSH_TARGET}:${REMOTE_PROJECT_DIR}/.env.secrets"

