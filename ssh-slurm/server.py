"""Read-only FastMCP server for embedded SLURM guidance."""

from __future__ import annotations

import re
import shlex

from mcp.server.fastmcp import FastMCP


APP = FastMCP("ssh-slurm")

DEFAULT_CONTAINER_WRAPPER = "/usr/local/bin/pipe-mcp-s10"
DEFAULT_CONTAINER_WORKDIR = "/workspace"
DEFAULT_HOST_LOG_PATH = "/srv/workspace/pipe/slurm-%j.out"
DEFAULT_JOB_NAME = "pipe-train"
DEFAULT_HOST_CHDIR = "/tmp"
DEFAULT_GPU_MEMORY_USED_MB_THRESHOLD = 1000
DEFAULT_PARTITION_EXAMPLE = "gpu_h200"
DEFAULT_SAMPLE_TRAIN_CMD = (
    "cd /workspace && python3 -c "
    "'import torch; print(torch.cuda.is_available(), torch.cuda.device_count())'"
)

NOT_FOUND = "The requested information could not be found in the embedded knowledge base."
REJECTED_TRAIN_CMD = (
    "Rejected train_cmd: do not set CUDA_VISIBLE_DEVICES, call pkill, or use "
    "dist_train.sh from generated SLURM scripts. Start from the embedded sample "
    "job and let SLURM assign CUDA_VISIBLE_DEVICES."
)


def render_default_placeholders(text: str) -> str:
    """Render embedded guidance placeholders from deployment defaults."""
    replacements = {
        "{{CONTAINER_WRAPPER}}": DEFAULT_CONTAINER_WRAPPER,
        "{{CONTAINER_WORKDIR}}": DEFAULT_CONTAINER_WORKDIR,
        "{{HOST_LOG_PATH}}": DEFAULT_HOST_LOG_PATH,
        "{{JOB_NAME}}": DEFAULT_JOB_NAME,
        "{{HOST_CHDIR}}": DEFAULT_HOST_CHDIR,
        "{{GPU_MEMORY_THRESHOLD_MB}}": str(DEFAULT_GPU_MEMORY_USED_MB_THRESHOLD),
        "{{PARTITION_EXAMPLE}}": DEFAULT_PARTITION_EXAMPLE,
        "{{SAMPLE_TRAIN_CMD}}": DEFAULT_SAMPLE_TRAIN_CMD,
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

## 자주 쓰는 명령

| 명령 | 설명 |
|---|---|
| `sbatch s.sh` | s.sh 잡을 큐에 제출 |
| `squeue -u "$USER"` | 내 pending/running 잡 |
| `squeue` | 전체 큐 |
| `scancel <id>` | 내 잡 취소 |
| `scancel -u "$USER"` | 내 모든 잡 취소 |
| `sacct -X` | 본인 잡 이력 |
| `sacct -X --starttime=now-7days` | 최근 7일 이력 |
| `sinfo` | 노드/파티션 상태 |
| `scontrol show job <id>` | 잡 상세 정보 |

## 잡 스크립트 패턴

핵심 골격:

```bash
#!/bin/bash
#SBATCH --gpus=1
#SBATCH --time=24:00:00
#SBATCH --chdir={{HOST_CHDIR}}
#SBATCH --output={{HOST_LOG_PATH}}

sudo -n {{CONTAINER_WRAPPER}} bash -c "cd {{CONTAINER_WORKDIR}} && python train.py"
```

## SBATCH 옵션 자주 쓰는 것

| 옵션 | 예시 | 의미 |
|---|---|---|
| `--gpus=N` | `--gpus=2` | GPU N개 요청 |
| `--gpus-per-node=N` | `--gpus-per-node=4` | 노드당 N개 |
| `--time=HH:MM:SS` | `--time=12:00:00` | 최대 wall time |
| `--mem=NG` | `--mem=64G` | 메모리 N GB 요청 |
| `--cpus-per-task=N` | `--cpus-per-task=8` | 잡당 CPU N core |
| `--job-name=NAME` | `--job-name=baseline` | 잡 이름 |
| `--partition=PART` | `--partition={{PARTITION_EXAMPLE}}` | 특정 파티션 |
| `--output=FILE` | `--output=run-%j.log` | stdout 경로 |

## 인터랙티브 잡

```bash
srun --gpus=1 -t 1:00:00 --pty bash
```

## 트러블슈팅

### 잡이 `Invalid account` 로 거부
- 본인 OS 계정이 SLURM 에 등록 안 됐을 가능성. 운영자에게 계정 등록을
  요청한다.

### 잡이 즉시 fail (ExitCode 1:0)
- `--chdir` 빠뜨렸을 가능성. SLURM 잡은 호스트에서 시작되므로 컨테이너
  전용 경로를 작업 디렉터리로 쓰면 실패할 수 있다.
  -> `#SBATCH --chdir={{HOST_CHDIR}}` 사용.

### 잡 출력이 안 보임
- `--output=` 으로 stdout 경로를 명시한다.
  -> `#SBATCH --output={{HOST_LOG_PATH}}` 권장.

### 학습 도중 패키지 설치 필요
컨테이너 안에서 옵션 3가지:
1. `pip install --user xxx`
2. `pip install xxx`
3. `conda create -n myenv python=3.10 && conda activate myenv`

SBATCH 잡에서는 필요한 환경 활성화나 `PYTHONPATH` 설정을 training command에
포함한다.

### 잡이 GPU 못 찾음
- 컨테이너에 GPU가 노출되어 있는지 확인한다.
'''
QUEUE_GUIDE = render_default_placeholders(QUEUE_GUIDE)

SAMPLE_JOB_SCRIPT = r'''---
summary: GPU server sample SBATCH template with a GPU memory guard and
  container-wrapper invocation.
---

# GPU Server sample-job.sh

## sample-job.sh

```bash
#!/bin/bash
# SLURM 잡 샘플
#
# 사용법:
#   sbatch sample-job.sh
#
# 본인 학습 명령에 맞춰 TRAIN_CMD 만 바꾸세요.

#SBATCH --job-name={{JOB_NAME}}
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --chdir={{HOST_CHDIR}}
#SBATCH --output={{HOST_LOG_PATH}}

if [ -z "${CUDA_VISIBLE_DEVICES:-}" ]; then
    echo "[ERROR] SLURM did not assign a GPU. Check #SBATCH --gpus." >&2
    exit 1
fi
echo "[INFO] SLURM assigned GPU: $CUDA_VISIBLE_DEVICES"

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
echo "[INFO] Hardware check passed. Starting training."

TRAIN_CMD="{{SAMPLE_TRAIN_CMD}}"

sudo -n {{CONTAINER_WRAPPER}} bash -c "export CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES && $TRAIN_CMD"
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
  -> pass CUDA_VISIBLE_DEVICES through the container wrapper
  -> inspect assigned GPU memory before training
  -> run training only if the assigned GPU is free enough
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
sinfo -p <partition>
tail -f {{HOST_LOG_PATH}}
command -v sbatch && command -v squeue && command -v srun
```

## Recurring Gotchas

### Scheduler/Physical GPU Mismatch

SLURM can assign a GPU that is already heavily used by a process it does not
account for. The job-local guard should inspect `nvidia-smi` memory for the
assigned physical GPU and abort if usage exceeds the accepted threshold.

### `sbatch --wrap` Runs Under `/bin/sh`

Using `sbatch --wrap '...'` can make the job run under `/bin/sh`, which does
not support `set -o pipefail`. Write an explicit bash script instead:

```bash
#!/bin/bash
set -euo pipefail
```

### Host vs Container Working Directory

SLURM jobs start on the host filesystem, not inside the container. Use
`#SBATCH --chdir={{HOST_CHDIR}}`, write logs to a host-visible path, and
re-enter the container through the wrapper.

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
- Use `#SBATCH --chdir={{HOST_CHDIR}}` and a host-visible `--output` path.
- Pass `CUDA_VISIBLE_DEVICES` through the container wrapper.
- Add an early `nvidia-smi` memory guard.
- Chain long training jobs after a short smoke job when appropriate.
- Record the job id, log path, work directory, and exact config overrides.

## Environment Notes

The concrete container wrapper, partition, workspace path, and GPU request
syntax can differ by server. This plugin's generated scripts use deployment
defaults for its target shared GPU server; adapt them before reusing the
guidance for a different SLURM environment.
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
    """Generate safe SBATCH scripts from the embedded sample."""

    @staticmethod
    def replace_sbatch_value(script: str, option: str, value: str | int) -> str:
        """Replace or insert a single SBATCH directive."""
        pattern = re.compile(
            rf"^#SBATCH\s+--{re.escape(option)}=.*$",
            re.MULTILINE,
        )
        replacement = f"#SBATCH --{option}={value}"
        if pattern.search(script):
            return pattern.sub(replacement, script, count=1)
        lines = script.splitlines()
        insert_at = 0
        for index, line in enumerate(lines):
            if line.startswith("#SBATCH"):
                insert_at = index + 1
        lines.insert(insert_at, replacement)
        return "\n".join(lines)

    @staticmethod
    def replace_train_cmd(script: str, train_cmd: str) -> str:
        """Replace the TRAIN_CMD assignment using shell-safe quoting."""
        quoted = shlex.quote(train_cmd)
        pattern = re.compile(r"^TRAIN_CMD=.*$", re.MULTILINE)
        replacement = f"TRAIN_CMD={quoted}"
        if pattern.search(script) is None:
            raise ValueError("TRAIN_CMD assignment not found")
        return pattern.sub(replacement, script, count=1)

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
    def generate(
        cls,
        train_cmd: str,
        job_name: str,
        gpus: int,
        time: str,
        mem: str,
        cpus: int,
    ) -> str:
        """Generate an SBATCH script from the embedded template."""
        script = MarkdownExtractor.extract_fenced_block(SAMPLE_JOB_SCRIPT, "bash")
        replacements: tuple[tuple[str, str | int], ...] = (
            ("job-name", job_name),
            ("gpus", gpus),
            ("cpus-per-task", cpus),
            ("mem", mem),
            ("time", time),
            ("chdir", DEFAULT_HOST_CHDIR),
            ("output", DEFAULT_HOST_LOG_PATH),
        )
        for option, value in replacements:
            script = cls.replace_sbatch_value(script, option, value)
        return cls.replace_train_cmd(script, train_cmd)


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
                    "잡이 `Invalid account` 로 거부",
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
                    "잡이 즉시 fail (ExitCode 1:0)",
                ),
            )
        if "output" in text or "log" in text or "stdout" in text:
            sections.append(
                MarkdownExtractor.safe_section(QUEUE_GUIDE, "잡 출력이 안 보임"),
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
        train_cmd: str,
        job_name: str = DEFAULT_JOB_NAME,
        gpus: int = 1,
        time: str = "24:00:00",
        mem: str = "32G",
        cpus: int = 8,
    ) -> str:
        """Generate a safe GPU server SBATCH script by changing template slots."""
        if SbatchGenerator.contains_rejected_train_cmd(train_cmd):
            return REJECTED_TRAIN_CMD
        if gpus < 1 or cpus < 1:
            return "Rejected request: gpus and cpus must be positive integers."

        try:
            return SbatchGenerator.generate(
                train_cmd,
                job_name,
                gpus,
                time,
                mem,
                cpus,
            )
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
                    MarkdownExtractor.safe_section(QUEUE_GUIDE, "트러블슈팅"),
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
                    MarkdownExtractor.safe_table(QUEUE_GUIDE, "자주 쓰는 명령"),
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
