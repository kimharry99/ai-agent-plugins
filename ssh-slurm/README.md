# SSH SLURM

`ssh-slurm` is a read-only FastMCP plugin for SLURM operational guidance and safe SBATCH script generation from embedded Knowledge DB records.

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
- `generate_sbatch_script(train_cmd, job_name="pipe-train", gpus=1, time="24:00:00", mem="32G", cpus=8, server="s10")`
- `diagnose(symptom)`
- `get_checklist()`
- `list_commands()`

Resources:

- `slurm://queue-guide`
- `slurm://sample-job`
- `slurm://synthesis/shared-gpu`
- `slurm://synthesis/vggt-det`

## Embedded Sources

The server embeds these canonical Knowledge DB files verbatim at generation time:

- `/mnt/Data2/Users/DongMinKim/Documents/80_Resources/99_Knowledge_db/90_references/ref_slurm-s10-queue-guide.md`
- `/mnt/Data2/Users/DongMinKim/Documents/80_Resources/99_Knowledge_db/90_references/ref_slurm-s10-sample-job.md`
- `/mnt/Data2/Users/DongMinKim/Documents/80_Resources/99_Knowledge_db/20_syntheses/syn_slurm-shared-gpu-queue-batching-pattern.md`
- `/mnt/Data2/Users/DongMinKim/Documents/80_Resources/99_Knowledge_db/20_syntheses/syn_vggt-det-shared-server-slurm-smoke-pattern.md`

## SBATCH Generation Scope

`generate_sbatch_script` extracts the embedded sample bash script, updates only the safe template slots, forces `#SBATCH --chdir=/tmp` and `#SBATCH --output=/srv/workspace/pipe/slurm-%j.out`, preserves the GPU memory guard and wrapper invocation, and replaces only the `TRAIN_CMD=` assignment using shell-safe quoting.

It rejects `train_cmd` values containing `CUDA_VISIBLE_DEVICES=`, `pkill`, or `dist_train.sh`.

The `server` argument is metadata-only for now. It remains in the tool signature, but generation uses the embedded s10 sample template. Server-specific facts are exposed through `get_server_info()`.

## Future Privileged Expansion

Real SSH, job submission, cancellation, or live GPU checks should be implemented as separate privileged tools, not added to this read-only guidance server. Any future privileged support should include credential isolation, least privilege, explicit confirmation gates, audit logs, allowlisted commands, no raw shell passthrough, and a clear separation between read-only guidance and state-changing operations.
