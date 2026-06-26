# Remote GPU Workflow

This workspace can be edited locally by Codex and executed on the remote GPU server through SSH.

The current remote defaults are stored in `.env.remote`:

```text
REMOTE_HOST=region-9.autodl.pro
REMOTE_PORT=40122
REMOTE_USER=root
REMOTE_PROJECT_DIR=/root/persona-mas-exp
```

Passwords are intentionally not stored in this repo. SSH will prompt for the password unless key-based login is configured.

## 1. Check Connection

```bash
scripts/remote_check.sh
```

This runs `hostname` and `nvidia-smi` on the remote server.

## 2. Sync Local Workspace to Remote

```bash
scripts/remote_sync.sh
```

This syncs the local workspace to:

```text
root@region-9.autodl.pro:/root/persona-mas-exp
```

Generated result folders under `outputs/` are excluded from upload by default.

## 3. Run a One-off Remote Command

```bash
scripts/remote_exec.sh "pwd && ls -la"
scripts/remote_exec.sh "python --version"
scripts/remote_exec.sh "nvidia-smi"
```

The command runs from `REMOTE_PROJECT_DIR`.

## 4. Start a Long Experiment in tmux

```bash
scripts/remote_tmux_start.sh "python run_exp.py"
```

The command runs in a detached tmux session named by `REMOTE_TMUX_SESSION`.
Stdout and stderr are appended to:

```text
logs/remote_run.log
```

## 5. Check Logs

```bash
scripts/remote_tail.sh
scripts/remote_tail.sh 200
```

## 6. Attach to tmux

```bash
scripts/remote_tmux_attach.sh
```

Detach from tmux with `Ctrl-b`, then `d`.

## 6.1 Start a Long Experiment with nohup

Use this path when `tmux` is not installed on the remote server:

```bash
scripts/remote_nohup_start.sh gpqa_trial "set -a && [[ -f .env.secrets ]] && source .env.secrets || true && set +a && export HF_ENDPOINT=https://hf-mirror.com && export HF_HOME=/root/autodl-tmp/hf-cache && PYTHONPATH=src /root/miniconda3/bin/python run_experiment0.py --config configs/experiment0_gpqa_trial.json"
```

Check the process and log:

```bash
scripts/remote_nohup_status.sh gpqa_trial 120
```

## 7. Pull Results Back

```bash
scripts/remote_pull_results.sh
```

Remote `outputs/` are copied into:

```text
outputs/remote_results/
```

## 8. Recommended SSH Key Setup

Password login works, but key login is better for repeated Codex operations.

If you already have a local public key:

```bash
cat ~/.ssh/id_rsa.pub
```

Append that public key to this file on the remote server:

```text
/root/.ssh/authorized_keys
```

After key login works, update `.env.remote` if you want to force a specific key:

```text
REMOTE_IDENTITY_FILE=/Users/simonchen/.ssh/id_rsa
```

Do not put passwords in `.env.remote`, scripts, notebooks, or logs.
