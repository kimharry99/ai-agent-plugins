"""Read-only FastMCP server for embedded SLURM guidance."""

from __future__ import annotations

import re
import shlex

from mcp.server.fastmcp import FastMCP


APP = FastMCP("ssh-slurm")

GENERIC_DEFAULT_JOB_NAME = "slurm-job"
GENERIC_DEFAULT_OUTPUT = "slurm-%j.out"
GENERIC_DEFAULT_TRAIN_CMD = "python train.py"
DEFAULT_GPU_MEMORY_USED_MB_THRESHOLD = 1000
S10_SAMPLE_CONTAINER_WRAPPER = "/usr/local/bin/pipe-mcp-s10"
S10_SAMPLE_CONTAINER_WORKDIR = "/workspace"
S10_SAMPLE_HOST_LOG_PATH = "/srv/workspace/pipe/slurm-%j.out"
S10_SAMPLE_HOST_CHDIR = "/tmp"
S10_SAMPLE_PARTITION = "gpu_h200"
S10_SAMPLE_TRAIN_CMD = (
    "python3 -c "
    "'import torch; print(torch.cuda.is_available(), torch.cuda.device_count())'"
)

NOT_FOUND = "The requested information could not be found in the embedded knowledge base."
REJECTED_TRAIN_CMD = (
    "Rejected train_cmd: do not set CUDA_VISIBLE_DEVICES, call pkill, or use "
    "dist_train.sh from generated SLURM scripts. Start from the embedded sample "
    "job and let SLURM assign CUDA_VISIBLE_DEVICES."
)
REJECTED_SBATCH_VALUE = (
    "Rejected request: SBATCH directive values must be non-empty single-line "
    "values without control characters."
)
REJECTED_ENV_VALUE = (
    "Rejected env: names must be shell identifiers and values must be "
    "single-line strings without control characters."
)
REJECTED_GPU_GUARD = (
    "Rejected gpu_guard: use skip_if_missing, error_if_missing, or disabled."
)


def render_default_placeholders(text: str) -> str:
    """Render embedded guidance placeholders for documented examples."""
    replacements = {
        "{{CONTAINER_WRAPPER}}": S10_SAMPLE_CONTAINER_WRAPPER,
        "{{CONTAINER_WORKDIR}}": S10_SAMPLE_CONTAINER_WORKDIR,
        "{{HOST_LOG_PATH}}": S10_SAMPLE_HOST_LOG_PATH,
        "{{JOB_NAME}}": GENERIC_DEFAULT_JOB_NAME,
        "{{HOST_CHDIR}}": S10_SAMPLE_HOST_CHDIR,
        "{{GPU_MEMORY_THRESHOLD_MB}}": str(DEFAULT_GPU_MEMORY_USED_MB_THRESHOLD),
        "{{PARTITION_EXAMPLE}}": S10_SAMPLE_PARTITION,
        "{{SAMPLE_TRAIN_CMD}}": S10_SAMPLE_TRAIN_CMD,
    }
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)
    return text


def get_gpu_server_context_text() -> str:
    """Return deployment-scoped context from embedded guidance."""
    try:
        return MarkdownExtractor.safe_section(
            SHARED_GPU_PATTERN,
            "Environment Notes",
        )
    except Exception:
        return NOT_FOUND


QUEUE_GUIDE = r'''---
summary: GPU server SLURM command table, SBATCH option reference, and
  troubleshooting guide for a shared GPU server deployment.
---

# GPU Server Queue Guide

## TL;DR

```bash
sbatch sample-job.sh
squeue -u "$USER"
scancel <JOBID>
sacct -X
```

`train.py` itself does not need to be modified. Start from the sample job
script and change only the training command.

## Common Commands

| Command | Description |
|---|---|
| `sbatch s.sh` | Submit the s.sh job to the queue |
| `squeue -u "$USER"` | My pending/running jobs |
| `squeue` | Entire queue |
| `scancel <id>` | Cancel one of my jobs |
| `scancel -u "$USER"` | Cancel all of my jobs |
| `sacct -X` | My job history |
| `sacct -X --starttime=now-7days` | History from the last 7 days |
| `sinfo` | Node/partition status |
| `scontrol show job <id>` | Detailed job information |

## Job Script Pattern

Core skeleton:

```bash
#!/bin/bash
#SBATCH --job-name=slurm-job
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --output=slurm-%j.out
set -euo pipefail

TRAIN_CMD='python train.py'
bash -lc "$TRAIN_CMD"
```

## Common SBATCH Options

| Option | Example | Meaning |
|---|---|---|
| `--gpus=N` | `--gpus=2` | Request N GPUs |
| `--gpus-per-node=N` | `--gpus-per-node=4` | N GPUs per node |
| `--time=HH:MM:SS` | `--time=12:00:00` | Maximum wall time |
| `--mem=NG` | `--mem=64G` | Request N GB of memory |
| `--cpus-per-task=N` | `--cpus-per-task=8` | N CPU cores per job |
| `--job-name=NAME` | `--job-name=baseline` | Job name |
| `--partition=PART` | `--partition={{PARTITION_EXAMPLE}}` | Specific partition |
| `--output=FILE` | `--output=run-%j.log` | stdout path |

## Interactive Jobs

```bash
srun --gpus=1 -t 1:00:00 --pty bash
```

## Troubleshooting

### Job Rejected With `Invalid account`
- Your OS account may not be registered with SLURM. Ask the administrator to
  register your account.

### Job Fails Immediately (ExitCode 1:0)
- `--chdir` may be missing. SLURM jobs start on the host, so using a
  container-only path as the working directory can fail.
  -> Use `#SBATCH --chdir=/host/visible/path`.

### Job Output Is Not Visible
- Specify the stdout path with `--output=`.
  -> Recommended: `#SBATCH --output=slurm-%j.out`.

### Package Installation Needed During Training
There are three options inside the container:
1. `pip install --user xxx`
2. `pip install xxx`
3. `conda create -n myenv python=3.10 && conda activate myenv`

For SBATCH jobs, include any required environment activation or `PYTHONPATH`
settings in the training command.

### Job Cannot Find the GPU
- Check that the GPU is exposed inside the container.
'''
QUEUE_GUIDE = render_default_placeholders(QUEUE_GUIDE)

SAMPLE_JOB_SCRIPT = r'''---
summary: GPU server sample SBATCH template with a GPU memory guard and
  optional GPU guard.
---

# GPU Server sample-job.sh

## sample-job.sh

```bash
#!/bin/bash
# Sample SLURM job
#
# Usage:
#   sbatch sample-job.sh
#
# Change TRAIN_CMD for your training command; adjust SBATCH resources
# deliberately when needed.
#SBATCH --job-name={{JOB_NAME}}
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --output=slurm-%j.out
set -euo pipefail

if [ -z "${CUDA_VISIBLE_DEVICES:-}" ]; then
    echo "[ERROR] SLURM did not assign a GPU. Check #SBATCH --gpus." >&2
    exit 1
fi
echo "[INFO] SLURM assigned GPU: $CUDA_VISIBLE_DEVICES"

if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "[WARN] nvidia-smi is unavailable; skipping GPU memory guard." >&2
else
for gpu_idx in $(echo "$CUDA_VISIBLE_DEVICES" | tr ',' ' '); do
    USED_MB=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits --id=$gpu_idx 2>/dev/null | tr -d ' ')
    if [ -z "$USED_MB" ]; then
        echo "[ERROR] Failed to query GPU $gpu_idx." >&2
        exit 1
    fi
    if [ "$USED_MB" -gt {{GPU_MEMORY_THRESHOLD_MB}} ]; then
        echo "[ERROR] GPU $gpu_idx is already using ${USED_MB} MB. Exiting." >&2
        exit 1
    fi
done
fi
echo "[INFO] Hardware check passed. Starting training."

TRAIN_CMD="{{SAMPLE_TRAIN_CMD}}"

bash -lc "$TRAIN_CMD"
```

## Site-specific profile example

The following example is documentation only. These values are not generic
defaults and are not inserted unless a caller explicitly passes equivalent
arguments to `generate_sbatch_script`.

```bash
#SBATCH --partition={{PARTITION_EXAMPLE}}
#SBATCH --chdir={{HOST_CHDIR}}
#SBATCH --output={{HOST_LOG_PATH}}

TRAIN_CMD='{{SAMPLE_TRAIN_CMD}}'
sudo -n {{CONTAINER_WRAPPER}} bash -lc "cd {{CONTAINER_WORKDIR}} && $TRAIN_CMD"
```
'''
SAMPLE_JOB_SCRIPT = render_default_placeholders(SAMPLE_JOB_SCRIPT)

SHARED_GPU_PATTERN = r'''---
summary: Shared GPU servers should run CUDA work through SLURM with job-local
  safety guards.
---

# Shared-GPU SLURM Queueing & Batching Pattern

## Core Pattern

```text
read the server queue guide
  -> copy the sample job script
  -> request GPU count through SLURM
  -> let SLURM set CUDA_VISIBLE_DEVICES
  -> optionally pass execution through a site wrapper
  -> optionally inspect assigned GPU memory before training
  -> run the training command
```

SLURM owns reservation, the job script owns the physical-state sanity check, and
the training command owns only the project-specific run.

## Submission & Monitoring Commands

```bash
sbatch <script>.sbatch
squeue -u "$USER"
squeue -j <ids> -o '%i %t %M %R %j'
sacct -j <id> --format=JobID,JobName%32,State,ExitCode,Elapsed,Start,End -P
scontrol show job <id>
tail -f slurm-<jobid>.out
command -v sbatch && command -v squeue && command -v srun
```

## Recurring Gotchas

### Scheduler/Physical GPU Mismatch

SLURM can assign a GPU that is already heavily used by a process it does not
account for. A job-local guard can inspect `nvidia-smi` memory for the assigned
physical GPU and abort if usage exceeds the accepted threshold. On clusters
without `nvidia-smi`, choose whether the generated script should fail clearly,
warn and continue, or omit the guard.

### `sbatch --wrap` Runs Under `/bin/sh`

Using `sbatch --wrap '...'` can make the job run under `/bin/sh`, which does
not support `set -o pipefail`. Write an explicit bash script instead:

```bash
#!/bin/bash
set -euo pipefail
```

### Host vs Container Working Directory

SLURM jobs start on the host filesystem, not inside the container. Use
`#SBATCH --chdir=/host/visible/path` when needed, write logs to a host-visible
path, and use any required wrapper explicitly.

### Munge / SLURM Outage

If the scheduler is unavailable, halt and report. Do not fall back to a direct
`CUDA_VISIBLE_DEVICES=N python ...` invocation outside the queue.

## Anti-Patterns

- Encoding a physical GPU id inside `TRAIN_CMD`.
- Using helper scripts that kill broad process sets on a shared server.
- Submitting via `sbatch --wrap` when the script body needs bash features.
- Installing packages into the base container environment during a smoke run.
- Writing output to container-only paths in `#SBATCH` directives.

## Reuse Checklist

- Read the GPU server queue guide before writing any script.
- Start from the GPU server sample job script.
- Request GPU count; do not encode a physical GPU number.
- Begin the script with `#!/bin/bash` and `set -euo pipefail`.
- Use a host-visible `--output` path, such as `slurm-%j.out`.
- Add `#SBATCH --chdir=...` only when the target cluster needs it.
- Pass a wrapper command only when the target site requires it.
- Add an early `nvidia-smi` memory guard when appropriate.
- Chain long training jobs after a short smoke job when appropriate.
- Record the job id, log path, work directory, and exact config overrides.

## Environment Notes

The concrete container wrapper, partition, workspace path, and GPU request
syntax can differ by server. The generator uses portable defaults and accepts
site-specific values only through explicit arguments.
'''
SHARED_GPU_PATTERN = render_default_placeholders(SHARED_GPU_PATTERN)


class MarkdownExtractor:
    """Small markdown extraction helpers for embedded guidance."""

    @staticmethod
    def extract_fenced_block(markdown: str, language: str) -> str:
        """Return the first fenced block for language from markdown.

        Args:
            markdown: Markdown text to scan.
            language: Fence language identifier.

        Returns:
            The block body without the closing fence.

        Raises:
            ValueError: If no matching fenced block exists.
        """
        pattern = re.compile(
            rf"^```{re.escape(language)}\s*\n(.*?)^```\s*$",
            re.MULTILINE | re.DOTALL,
        )
        match = pattern.search(markdown)
        if match is None:
            raise ValueError("fenced block not found")
        return match.group(1).rstrip("\n")

    @staticmethod
    def heading_level(line: str) -> int | None:
        """Return markdown heading level for a line, if any."""
        match = re.match(r"^(#+)\s+", line)
        if match is None:
            return None
        return len(match.group(1))

    @classmethod
    def extract_section(cls, markdown: str, heading: str) -> str:
        """Extract a markdown section by exact heading text.

        Args:
            markdown: Markdown text to scan.
            heading: Heading text without leading hashes.

        Returns:
            The matching section including its heading.

        Raises:
            ValueError: If the section is missing or empty.
        """
        lines = markdown.splitlines()
        start = None
        level = None
        for index, line in enumerate(lines):
            parsed_level = cls.heading_level(line)
            if parsed_level is None:
                continue
            title = line[parsed_level:].strip()
            if title == heading:
                start = index
                level = parsed_level
                break
        if start is None or level is None:
            raise ValueError("section not found")

        end = len(lines)
        for index in range(start + 1, len(lines)):
            parsed_level = cls.heading_level(lines[index])
            if parsed_level is not None and parsed_level <= level:
                end = index
                break
        section = "\n".join(lines[start:end]).strip()
        if not section:
            raise ValueError("section empty")
        return section

    @classmethod
    def extract_first_table(cls, markdown: str, section_heading: str) -> str:
        """Extract the first markdown table from a section."""
        section = cls.extract_section(markdown, section_heading)
        rows: list[str] = []
        collecting = False
        for line in section.splitlines():
            if line.lstrip().startswith("|") and line.rstrip().endswith("|"):
                rows.append(line)
                collecting = True
            elif collecting:
                break
        if not rows:
            raise ValueError("table not found")
        return "\n".join(rows)

    @classmethod
    def safe_section(cls, markdown: str, heading: str) -> str:
        """Extract a section or return the standard missing-info response."""
        try:
            return cls.extract_section(markdown, heading)
        except Exception:
            return NOT_FOUND

    @classmethod
    def safe_table(cls, markdown: str, heading: str) -> str:
        """Extract a table or return the standard missing-info response."""
        try:
            return cls.extract_first_table(markdown, heading)
        except Exception:
            return NOT_FOUND


class SbatchGenerator:
    """Generate portable SBATCH scripts from explicit inputs."""

    GPU_GUARD_SKIP_IF_MISSING = "skip_if_missing"
    GPU_GUARD_ERROR_IF_MISSING = "error_if_missing"
    GPU_GUARD_DISABLED = "disabled"

    @staticmethod
    def is_safe_sbatch_value(value: str | int) -> bool:
        """Return whether value can be interpolated into one SBATCH line."""
        value_text = str(value)
        return bool(value_text) and re.search(r"[\r\n\x00]", value_text) is None

    @staticmethod
    def is_safe_sbatch_option(option: str) -> bool:
        """Return whether option is a safe long SBATCH option name."""
        return re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", option) is not None

    @staticmethod
    def is_safe_shell_line(value: str) -> bool:
        """Return whether a command-like value can stay on one script line."""
        return bool(value) and re.search(r"[\r\n\x00]", value) is None

    @staticmethod
    def is_safe_env_name(name: str) -> bool:
        """Return whether name is a valid shell variable identifier."""
        return re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) is not None

    @classmethod
    def append_sbatch_line(
        cls,
        lines: list[str],
        option: str,
        value: str | int | bool,
    ) -> None:
        """Append a validated SBATCH directive to lines."""
        if not cls.is_safe_sbatch_option(option):
            raise ValueError("unsafe SBATCH option name")
        if isinstance(value, bool):
            if value:
                lines.append(f"#SBATCH --{option}")
            return
        if not cls.is_safe_sbatch_value(value):
            raise ValueError("unsafe SBATCH directive value")
        lines.append(f"#SBATCH --{option}={value}")

    @staticmethod
    def contains_rejected_train_cmd(train_cmd: str) -> bool:
        """Return whether train_cmd contains known shared-server anti-patterns."""
        lowered = train_cmd.lower()
        return (
            "cuda_visible_devices=" in lowered
            or re.search(r"(^|[;&|\s])pkill($|[;&|\s])", lowered) is not None
            or "dist_train.sh" in lowered
        )

    @classmethod
    def append_gpu_guard(cls, lines: list[str], gpu_guard: str) -> None:
        """Append a generic CUDA/nvidia-smi guard."""
        if gpu_guard == cls.GPU_GUARD_DISABLED:
            return
        if gpu_guard not in (
            cls.GPU_GUARD_SKIP_IF_MISSING,
            cls.GPU_GUARD_ERROR_IF_MISSING,
        ):
            raise ValueError("unsupported gpu_guard")

        lines.extend(
            [
                "",
                'if [ -z "${CUDA_VISIBLE_DEVICES:-}" ]; then',
                '    echo "[ERROR] SLURM did not assign a GPU." >&2',
                "    exit 1",
                "fi",
                'echo "[INFO] SLURM assigned GPU: $CUDA_VISIBLE_DEVICES"',
                "",
                "if ! command -v nvidia-smi >/dev/null 2>&1; then",
            ],
        )
        if gpu_guard == cls.GPU_GUARD_ERROR_IF_MISSING:
            lines.extend(
                [
                    '    echo "[ERROR] nvidia-smi is unavailable." >&2',
                    "    exit 1",
                ],
            )
        else:
            lines.append(
                '    echo "[WARN] nvidia-smi unavailable; skipping GPU guard." >&2',
            )
        lines.extend(
            [
                "else",
                '    for gpu_idx in $(echo "$CUDA_VISIBLE_DEVICES" | tr "," " "); do',
                "        USED_MB=$(nvidia-smi "
                "--query-gpu=memory.used "
                "--format=csv,noheader,nounits "
                "--id=$gpu_idx 2>/dev/null | tr -d ' ')",
                '        if [ -z "$USED_MB" ]; then',
                '            echo "[ERROR] Failed to query GPU $gpu_idx." >&2',
                "            exit 1",
                "        fi",
                "        if [ \"$USED_MB\" -gt "
                f"{DEFAULT_GPU_MEMORY_USED_MB_THRESHOLD} ]; then",
                '            echo "[ERROR] GPU $gpu_idx is already using '
                '${USED_MB} MB." >&2',
                "            exit 1",
                "        fi",
                "    done",
                "fi",
            ],
        )

    @classmethod
    def append_env_exports(cls, lines: list[str], env: dict[str, str]) -> None:
        """Append validated environment exports."""
        if not env:
            return
        lines.append("")
        for name, value in env.items():
            value_text = str(value)
            if (
                not cls.is_safe_env_name(name)
                or not cls.is_safe_shell_line(value_text)
            ):
                raise ValueError("unsafe environment assignment")
            lines.append(f"export {name}={shlex.quote(value_text)}")

    @classmethod
    def append_execution(
        cls,
        lines: list[str],
        train_cmd: str,
        workdir: str | None,
        wrapper_cmd: str | None,
    ) -> None:
        """Append the training command execution block."""
        if not cls.is_safe_shell_line(train_cmd):
            raise ValueError("unsafe train_cmd")
        if workdir is not None and not cls.is_safe_shell_line(workdir):
            raise ValueError("unsafe workdir")
        if wrapper_cmd is not None and not cls.is_safe_shell_line(wrapper_cmd):
            raise ValueError("unsafe wrapper_cmd")

        lines.extend(["", f"TRAIN_CMD={shlex.quote(train_cmd)}"])
        if workdir is None:
            lines.append('RUN_CMD="$TRAIN_CMD"')
        else:
            prefix = f"cd {shlex.quote(workdir)} && "
            lines.append(f"RUN_CMD={shlex.quote(prefix)}\"$TRAIN_CMD\"")

        if wrapper_cmd is None:
            lines.append('bash -lc "$RUN_CMD"')
        else:
            lines.append(f"{wrapper_cmd} bash -lc \"$RUN_CMD\"")

    @classmethod
    def generate(
        cls,
        train_cmd: str,
        job_name: str,
        gpus: int,
        time: str,
        mem: str,
        cpus: int,
        partition: str | None,
        chdir: str | None,
        output: str,
        extra_sbatch_options: dict[str, str | int | bool] | None,
        env: dict[str, str] | None,
        workdir: str | None,
        wrapper_cmd: str | None,
        gpu_guard: str,
    ) -> str:
        """Generate a generic SBATCH script from explicit parameters."""
        lines = ["#!/bin/bash"]
        required_options: tuple[tuple[str, str | int], ...] = (
            ("job-name", job_name),
            ("gpus", gpus),
            ("cpus-per-task", cpus),
            ("mem", mem),
            ("time", time),
            ("output", output),
        )
        for option, value in required_options:
            cls.append_sbatch_line(lines, option, value)
        if partition is not None:
            cls.append_sbatch_line(lines, "partition", partition)
        if chdir is not None:
            cls.append_sbatch_line(lines, "chdir", chdir)
        for option, value in (extra_sbatch_options or {}).items():
            cls.append_sbatch_line(lines, option, value)
        lines.append("set -euo pipefail")

        if gpus > 0:
            cls.append_gpu_guard(lines, gpu_guard)
        cls.append_env_exports(lines, env or {})
        cls.append_execution(lines, train_cmd, workdir, wrapper_cmd)
        return "\n".join(lines) + "\n"


class Diagnostics:
    """Keyword-based troubleshooting lookup over embedded guidance."""

    @staticmethod
    def keyword_diagnostics(symptom: str) -> str | None:
        """Return targeted guidance sections for a symptom string."""
        text = symptom.lower()
        sections: list[str] = []
        if "invalid account" in text or "account" in text:
            sections.append(
                MarkdownExtractor.safe_section(
                    QUEUE_GUIDE,
                    "Job Rejected With `Invalid account`",
                ),
            )
        if (
            "exitcode" in text
            or "exit code" in text
            or "fail" in text
            or "failed" in text
        ):
            sections.append(
                MarkdownExtractor.safe_section(
                    QUEUE_GUIDE,
                    "Job Fails Immediately (ExitCode 1:0)",
                ),
            )
        if "output" in text or "log" in text or "stdout" in text:
            sections.append(
                MarkdownExtractor.safe_section(
                    QUEUE_GUIDE,
                    "Job Output Is Not Visible",
                ),
            )
        if "gpu" in text or "cuda" in text or "visible" in text or "memory" in text:
            sections.append(
                MarkdownExtractor.safe_section(
                    SHARED_GPU_PATTERN,
                    "Scheduler/Physical GPU Mismatch",
                ),
            )
            sections.append(
                MarkdownExtractor.safe_section(SHARED_GPU_PATTERN, "Anti-Patterns"),
            )
        if "wrap" in text or "/bin/sh" in text or "bash" in text:
            sections.append(
                MarkdownExtractor.safe_section(
                    SHARED_GPU_PATTERN,
                    "`sbatch --wrap` Runs Under `/bin/sh`",
                ),
            )
        if (
            "directory" in text
            or "chdir" in text
            or "workspace" in text
            or "path" in text
        ):
            sections.append(
                MarkdownExtractor.safe_section(
                    SHARED_GPU_PATTERN,
                    "Host vs Container Working Directory",
                ),
            )
        if "munge" in text or "outage" in text or "slurmctld" in text:
            sections.append(
                MarkdownExtractor.safe_section(
                    SHARED_GPU_PATTERN,
                    "Munge / SLURM Outage",
                ),
            )

        cleaned = [section for section in sections if section != NOT_FOUND]
        if not cleaned:
            return None
        return "\n\n".join(cleaned)


class SlurmGuidanceTools:
    """FastMCP tool surface for read-only SLURM guidance."""

    @staticmethod
    @APP.tool()
    def get_queue_guide() -> str:
        """Return the embedded shared GPU SLURM server queue guide."""
        return QUEUE_GUIDE

    @staticmethod
    @APP.tool()
    def get_sample_job_script() -> str:
        """Return the embedded GPU server sample SBATCH job record."""
        return SAMPLE_JOB_SCRIPT

    @staticmethod
    @APP.tool()
    def get_gpu_server_context() -> str:
        """Return embedded GPU server context without enabling live actions."""
        return get_gpu_server_context_text()

    @staticmethod
    @APP.tool()
    def get_server_info() -> str:
        """Return GPU server context as a backward-compatible alias."""
        return get_gpu_server_context_text()

    @staticmethod
    @APP.tool()
    def generate_sbatch_script(
        train_cmd: str = GENERIC_DEFAULT_TRAIN_CMD,
        job_name: str = GENERIC_DEFAULT_JOB_NAME,
        gpus: int = 1,
        time: str = "24:00:00",
        mem: str = "32G",
        cpus: int = 8,
        partition: str | None = None,
        chdir: str | None = None,
        output: str = GENERIC_DEFAULT_OUTPUT,
        extra_sbatch_options: dict[str, str | int | bool] | None = None,
        env: dict[str, str] | None = None,
        workdir: str | None = None,
        wrapper_cmd: str | None = None,
        gpu_guard: str = SbatchGenerator.GPU_GUARD_SKIP_IF_MISSING,
    ) -> str:
        """Generate a portable SBATCH script from explicit parameters."""
        if SbatchGenerator.contains_rejected_train_cmd(train_cmd):
            return REJECTED_TRAIN_CMD
        if gpus < 1 or cpus < 1:
            return "Rejected request: gpus and cpus must be positive integers."
        if not all(
            SbatchGenerator.is_safe_sbatch_value(value)
            for value in (job_name, gpus, time, mem, cpus, output)
        ):
            return REJECTED_SBATCH_VALUE
        if partition is not None and not SbatchGenerator.is_safe_sbatch_value(
            partition,
        ):
            return REJECTED_SBATCH_VALUE
        if chdir is not None and not SbatchGenerator.is_safe_sbatch_value(chdir):
            return REJECTED_SBATCH_VALUE
        if gpu_guard not in (
            SbatchGenerator.GPU_GUARD_SKIP_IF_MISSING,
            SbatchGenerator.GPU_GUARD_ERROR_IF_MISSING,
            SbatchGenerator.GPU_GUARD_DISABLED,
        ):
            return REJECTED_GPU_GUARD

        try:
            return SbatchGenerator.generate(
                train_cmd,
                job_name,
                gpus,
                time,
                mem,
                cpus,
                partition,
                chdir,
                output,
                extra_sbatch_options,
                env,
                workdir,
                wrapper_cmd,
                gpu_guard,
            )
        except ValueError as error:
            if "environment" in str(error):
                return REJECTED_ENV_VALUE
            if "gpu_guard" in str(error):
                return REJECTED_GPU_GUARD
            return REJECTED_SBATCH_VALUE
        except Exception:
            return NOT_FOUND

    @staticmethod
    @APP.tool()
    def diagnose(symptom: str) -> str:
        """Return targeted troubleshooting guidance from embedded records."""
        try:
            targeted = Diagnostics.keyword_diagnostics(symptom)
            if targeted is not None:
                return targeted
            return "\n\n".join(
                [
                    MarkdownExtractor.safe_section(QUEUE_GUIDE, "Troubleshooting"),
                    MarkdownExtractor.safe_section(
                        SHARED_GPU_PATTERN,
                        "Recurring Gotchas",
                    ),
                ],
            )
        except Exception:
            return NOT_FOUND

    @staticmethod
    @APP.tool()
    def get_checklist() -> str:
        """Return reusable SLURM preparation checklists."""
        try:
            return MarkdownExtractor.safe_section(
                SHARED_GPU_PATTERN,
                "Reuse Checklist",
            )
        except Exception:
            return NOT_FOUND

    @staticmethod
    @APP.tool()
    def list_commands() -> str:
        """Return command tables and command snippets from embedded guidance."""
        try:
            return "\n\n".join(
                [
                    MarkdownExtractor.safe_table(QUEUE_GUIDE, "Common Commands"),
                    MarkdownExtractor.safe_section(
                        SHARED_GPU_PATTERN,
                        "Submission & Monitoring Commands",
                    ),
                ],
            )
        except Exception:
            return NOT_FOUND


if __name__ == "__main__":
    APP.run()
