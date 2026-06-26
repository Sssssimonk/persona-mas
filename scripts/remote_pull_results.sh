#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/remote_common.sh"

mkdir -p "${PROJECT_ROOT}/outputs/remote_results"

rsync -avz \
  -e "${rsync_ssh}" \
  "${SSH_TARGET}:${REMOTE_PROJECT_DIR}/outputs/" \
  "${PROJECT_ROOT}/outputs/remote_results/"

echo "Pulled remote outputs to ${PROJECT_ROOT}/outputs/remote_results"

