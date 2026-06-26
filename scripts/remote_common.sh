#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env.remote"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}" >&2
  echo "Copy .env.remote.example to .env.remote and adjust values." >&2
  exit 1
fi

set -a
source "${ENV_FILE}"
set +a

: "${REMOTE_HOST:?REMOTE_HOST is required}"
: "${REMOTE_PORT:?REMOTE_PORT is required}"
: "${REMOTE_USER:?REMOTE_USER is required}"
: "${REMOTE_PROJECT_DIR:?REMOTE_PROJECT_DIR is required}"
: "${REMOTE_TMUX_SESSION:=persona_mas_exp}"
: "${REMOTE_LOG_FILE:=logs/remote_run.log}"
: "${REMOTE_IDENTITY_FILE:=}"

SSH_TARGET="${REMOTE_USER}@${REMOTE_HOST}"

ssh_base_args=(
  -p "${REMOTE_PORT}"
  -o ServerAliveInterval=60
  -o ServerAliveCountMax=5
)

if [[ -n "${REMOTE_IDENTITY_FILE}" ]]; then
  ssh_base_args+=(-i "${REMOTE_IDENTITY_FILE}")
fi

ssh_cmd=(ssh "${ssh_base_args[@]}" "${SSH_TARGET}")
rsync_ssh="ssh -p ${REMOTE_PORT} -o ServerAliveInterval=60 -o ServerAliveCountMax=5"
if [[ -n "${REMOTE_IDENTITY_FILE}" ]]; then
  rsync_ssh="${rsync_ssh} -i ${REMOTE_IDENTITY_FILE}"
fi

