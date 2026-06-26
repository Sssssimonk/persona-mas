#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/remote_common.sh"

REMOTE_PYTHON_BIN="${REMOTE_PYTHON_BIN:-/root/miniconda3/bin/python}"

read -r -d '' REMOTE_SETUP <<'REMOTE_SCRIPT' || true
set -euo pipefail

PYTHON_BIN="${REMOTE_PYTHON_BIN}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Python not found or not executable: ${PYTHON_BIN}" >&2
  exit 1
fi

echo "Using python: ${PYTHON_BIN}"
"${PYTHON_BIN}" --version

"${PYTHON_BIN}" - <<'PY'
import torch
print("existing torch", torch.__version__)
print("existing torch cuda", torch.version.cuda)
print("cuda available", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu", torch.cuda.get_device_name(0))
PY

"${PYTHON_BIN}" -m pip install --upgrade \
  "transformers>=4.52.0" \
  "peft>=0.15.0" \
  "accelerate>=1.7.0" \
  "datasets==3.6.0" \
  pandas \
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

"${PYTHON_BIN}" - <<'PY'
import importlib
import torch

mods = [
    "torch",
    "transformers",
    "peft",
    "accelerate",
    "datasets",
    "pandas",
    "numpy",
    "openai",
    "pydantic",
    "jsonlines",
    "safetensors",
    "sentencepiece",
]

for name in mods:
    mod = importlib.import_module(name)
    print(name, getattr(mod, "__version__", "installed"))

print("torch.cuda", torch.version.cuda)
print("cuda available", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu", torch.cuda.get_device_name(0))
PY

echo "Base environment dependencies are ready."
REMOTE_SCRIPT

"${ssh_cmd[@]}" \
  "cd '${REMOTE_PROJECT_DIR}' && REMOTE_PYTHON_BIN='${REMOTE_PYTHON_BIN}' bash -s" \
  <<< "${REMOTE_SETUP}"

