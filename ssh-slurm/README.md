# SSH SLURM

`ssh-slurm` is a read-only FastMCP plugin for SLURM operational guidance and safe SBATCH script generation from embedded guidance.

Despite the name, this server does not SSH into machines, submit jobs, cancel jobs, read files at runtime, call the network, inspect GPUs, or pass through shell commands. It only returns embedded guidance and generates an SBATCH script from the embedded s10 sample template.

## Requirements

- Python 3.10+
- `mcp` Python package with FastMCP support

Install the dependency in the environment that will launch the MCP server:

```bash
python -m pip install mcp
```

## Claude MCP Registration

```bash
claude mcp add ssh-slurm -- python ~/mcp-servers/ssh-slurm/server.py
```

If you use this repo-local copy directly, replace the path with the local `server.py` path.

## MCP Surface

Tools:

- `get_queue_guide()`
- `get_sample_job_script()`
- `get_server_info()`
- `generate_sbatch_script(train_cmd, job_name="pipe-train", gpus=1, time="24:00:00", mem="32G", cpus=8)`
- `diagnose(symptom)`
- `get_checklist()`
- `list_commands()`

## SBATCH Generation Scope

`generate_sbatch_script` extracts the embedded sample bash script, updates only the safe template slots, forces `#SBATCH --chdir=/tmp` and `#SBATCH --output=/srv/workspace/pipe/slurm-%j.out`, preserves the GPU memory guard and wrapper invocation, and replaces only the `TRAIN_CMD=` assignment using shell-safe quoting.

It rejects `train_cmd` values containing `CUDA_VISIBLE_DEVICES=`, `pkill`, or `dist_train.sh`.

## Future Privileged Expansion

Real SSH, job submission, cancellation, or live GPU checks should be implemented as separate privileged tools, not added to this read-only guidance server. Any future privileged support should include credential isolation, least privilege, explicit confirmation gates, audit logs, allowlisted commands, no raw shell passthrough, and a clear separation between read-only guidance and state-changing operations.
