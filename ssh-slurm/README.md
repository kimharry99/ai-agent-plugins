# SSH SLURM

`ssh-slurm` is a read-only FastMCP plugin for shared GPU SLURM server guidance and safe SBATCH script generation from embedded guidance.

Despite the name, this server does not SSH into machines, submit jobs, cancel jobs, read files at runtime, call the network, inspect GPUs, or pass through shell commands. It only returns embedded guidance and generates an SBATCH script from the embedded GPU server sample template.

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
- `get_gpu_server_context()`
- `get_server_info()` backward-compatible alias for `get_gpu_server_context()`
- `generate_sbatch_script(train_cmd, job_name="pipe-train", gpus=1, time="24:00:00", mem="32G", cpus=8)`
- `diagnose(symptom)`
- `get_checklist()`
- `list_commands()`

## SBATCH Generation Scope

`generate_sbatch_script` extracts the embedded sample bash script, validates and updates the single-line SBATCH template slots, applies this deployment's GPU-server defaults for `#SBATCH --chdir=/tmp` and `#SBATCH --output=/srv/workspace/pipe/slurm-%j.out`, preserves the GPU memory guard and wrapper invocation, and replaces the `TRAIN_CMD=` assignment using shell-safe quoting.

Those defaults are deployment defaults for this shared GPU server role, not universal SLURM settings. Review the embedded GPU server context before adapting generated scripts to a different cluster, partition layout, container wrapper, or log path convention.

It rejects `train_cmd` values containing `CUDA_VISIBLE_DEVICES=`, `pkill`, or `dist_train.sh`.

## Future Privileged Expansion

Real SSH, job submission, cancellation, or live GPU checks should be implemented as separate privileged tools, not added to this read-only guidance server. Any future privileged support should include credential isolation, least privilege, explicit confirmation gates, audit logs, allowlisted commands, no raw shell passthrough, and a clear separation between read-only guidance and state-changing operations.
