# SSH SLURM

`ssh-slurm` is a read-only FastMCP plugin for shared GPU SLURM server guidance and generic SBATCH script generation.

Despite the name, this server does not SSH into machines, submit jobs, cancel jobs, read files at runtime, call the network, inspect GPUs, or pass through shell commands. It only returns embedded guidance and generates an SBATCH script string from explicit arguments.

## Requirements

- Python 3.10+
- `mcp` Python package with FastMCP support

Install the dependency in the environment that will launch the MCP server:

```bash
python3 -m pip install mcp
```

## Codex Plugin Registration

The Codex plugin manifest points at the bundled `.mcp.json` file. That file
sets `cwd` for the bundled MCP server so the relative `./server.py` argument is
resolved from the installed plugin directory, not from the Codex session's
current working directory.

## Claude MCP Registration

```bash
claude mcp add ssh-slurm -- python3 ~/mcp-servers/ssh-slurm/server.py
```

If you use this repo-local copy directly, replace the path with the local `server.py` path.

## MCP Surface

Tools:

- `get_queue_guide()`
- `get_sample_job_script()`
- `get_gpu_server_context()`
- `get_server_info()` backward-compatible alias for `get_gpu_server_context()`
- `generate_sbatch_script(train_cmd="python train.py", job_name="slurm-job", gpus=1, time="24:00:00", mem="32G", cpus=8, partition=None, chdir=None, output="slurm-%j.out", extra_sbatch_options=None, env=None, workdir=None, wrapper_cmd=None, gpu_guard="skip_if_missing")`
- `diagnose(symptom)`
- `get_checklist()`
- `list_commands()`

## SBATCH Generation Scope

`generate_sbatch_script` builds a portable bash script from explicit inputs. With no arguments, it returns a generic script with:

- `#!/bin/bash`
- `#SBATCH --job-name=slurm-job`
- `#SBATCH --gpus=1`
- `#SBATCH --cpus-per-task=8`
- `#SBATCH --mem=32G`
- `#SBATCH --time=24:00:00`
- `#SBATCH --output=slurm-%j.out`
- `set -euo pipefail`
- `TRAIN_CMD='python train.py'`

It rejects `train_cmd` values containing `CUDA_VISIBLE_DEVICES=`, `pkill`, or `dist_train.sh`. `partition`, `chdir`, `workdir`, `wrapper_cmd`, `extra_sbatch_options`, and `env` are inserted only when the caller provides them.

`gpu_guard` controls generic GPU checks:

- `skip_if_missing` (default): check `CUDA_VISIBLE_DEVICES`; use `nvidia-smi` when present and warn when it is missing.
- `error_if_missing`: fail clearly when `nvidia-smi` is unavailable.
- `disabled`: omit the generated GPU guard.

## Site-specific Example

Deployment-specific paths and wrappers are documentation examples, not default behavior. For example, an s10/pipe-style profile can be expressed explicitly:

```json
{
  "partition": "gpu_h200",
  "chdir": "/tmp",
  "output": "/srv/workspace/pipe/slurm-%j.out",
  "workdir": "/workspace",
  "wrapper_cmd": "sudo -n /usr/local/bin/pipe-mcp-s10",
  "train_cmd": "python3 -c 'import torch; print(torch.cuda.is_available(), torch.cuda.device_count())'"
}
```

## Future Privileged Expansion

Real SSH, job submission, cancellation, or live GPU checks should be implemented as separate privileged tools, not added to this read-only guidance server. Any future privileged support should include credential isolation, least privilege, explicit confirmation gates, audit logs, allowlisted commands, no raw shell passthrough, and a clear separation between read-only guidance and state-changing operations.
