#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/remote_common.sh"

REMOTE_ENV_NAME="${REMOTE_ENV_NAME:-persona-mas}"
REMOTE_CONDA_BIN="${REMOTE_CONDA_BIN:-/root/miniconda3/bin/conda}"

read -r -d '' REMOTE_SETUP <<'REMOTE_SCRIPT' || true
set -euo pipefail

ENV_NAME="${REMOTE_ENV_NAME}"
CONDA_BIN="${REMOTE_CONDA_BIN}"

if [[ ! -x "${CONDA_BIN}" ]]; then
  echo "Conda not found or not executable: ${CONDA_BIN}" >&2
  exit 1
fi

echo "Using conda: ${CONDA_BIN}"
"${CONDA_BIN}" --version

if ! "${CONDA_BIN}" env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
  echo "Creating conda env: ${ENV_NAME}"
  "${CONDA_BIN}" create -y -n "${ENV_NAME}" python=3.11
else
  echo "Conda env already exists: ${ENV_NAME}"
fi

PYTHON="$("${CONDA_BIN}" run -n "${ENV_NAME}" which python)"
echo "Using python: ${PYTHON}"
"${CONDA_BIN}" run -n "${ENV_NAME}" python --version

"${CONDA_BIN}" run -n "${ENV_NAME}" python -m pip install --upgrade pip setuptools wheel

"${CONDA_BIN}" run -n "${ENV_NAME}" python -m pip install \
  torch==2.7.0 torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/cu128

"${CONDA_BIN}" run -n "${ENV_NAME}" python -m pip install \
  "transformers>=4.52.0" \
  "peft>=0.15.0" \
  "accelerate>=1.7.0" \
  "datasets==3.6.0" \
  pandas \
  numpy \
  tqdm \
  pydantic \
  jsonlines \
  requests \
  wget \
  gdown \
  openai \
  safetensors \
  sentencepiece \
  protobuf

"${CONDA_BIN}" run -n "${ENV_NAME}" python - <<'PY'
import torch
print("torch", torch.__version__)
print("torch cuda", torch.version.cuda)
print("cuda available", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu", torch.cuda.get_device_name(0))
    print("capability", torch.cuda.get_device_capability(0))
PY

echo "Environment ready: ${ENV_NAME}"
REMOTE_SCRIPT

"${ssh_cmd[@]}" \
  "cd '${REMOTE_PROJECT_DIR}' && REMOTE_ENV_NAME='${REMOTE_ENV_NAME}' REMOTE_CONDA_BIN='${REMOTE_CONDA_BIN}' bash -s" \
  <<< "${REMOTE_SETUP}"

