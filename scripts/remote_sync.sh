#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/remote_common.sh"

"${ssh_cmd[@]}" "mkdir -p '${REMOTE_PROJECT_DIR}'"

rsync -avz --delete \
  -e "${rsync_ssh}" \
  --exclude '.git/' \
  --exclude '.env.remote' \
  --exclude '.env.secrets' \
  --exclude '__pycache__/' \
  --exclude '.pytest_cache/' \
  --exclude '.mypy_cache/' \
  --exclude '.ruff_cache/' \
  --exclude '.venv-abstention/' \
  --exclude 'data/' \
  --exclude 'logs/' \
  --exclude 'analysis_examples/' \
  --exclude 'benchmarks/raw/' \
  --exclude 'benchmarks/abstentionbench/abstention_full.jsonl' \
  --exclude 'benchmarks/deceptionbench/deception_full.jsonl' \
  --exclude 'benchmarks/gpqa/gpqa_diamond.csv' \
  --exclude 'benchmarks/gpqa/gpqa_diamond_epoch_scores.csv' \
  --exclude 'outputs/raw_generations/' \
  --exclude 'outputs/aggregations/' \
  --exclude 'outputs/judge/' \
  --exclude 'outputs/metrics/' \
  --exclude 'outputs/smoke/' \
  --exclude 'outputs/hf_remote_smoke/' \
  --exclude 'outputs/hf_trial/' \
  --exclude 'outputs/gpqa_trial/' \
  --exclude 'outputs/gpqa_full/' \
  --exclude 'outputs/abstention_hf_trial/' \
  --exclude 'outputs/abstention_n100/' \
  --exclude 'outputs/deception_hf_trial/' \
  --exclude 'outputs/deception_n50/' \
  --exclude 'outputs/deception_n100/' \
  --exclude 'outputs/gpqa_cot_full/' \
  --exclude 'outputs/gpqa_cot_n20/' \
  --exclude 'outputs/gpqa_cot_n50/' \
  --exclude 'outputs/abstention_natural_n100/' \
  --exclude 'outputs/deception_l1_self_n100/' \
  --exclude 'outputs/protocol_v1_trial_gpqa_cot_n2/' \
  --exclude 'outputs/protocol_v1_trial_abstention_natural_n2/' \
  --exclude 'outputs/protocol_v1_trial_abstention_unanswerable_n2/' \
  --exclude 'outputs/protocol_v1_trial_deception_l1_self_n2/' \
  --exclude 'outputs/control_template/' \
  --exclude 'outputs/prompt_only_template/' \
  --exclude 'outputs/remote_results/' \
  "${PROJECT_ROOT}/" \
  "${SSH_TARGET}:${REMOTE_PROJECT_DIR}/"

echo "Synced ${PROJECT_ROOT} -> ${SSH_TARGET}:${REMOTE_PROJECT_DIR}"
