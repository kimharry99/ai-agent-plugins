"""Read-only FastMCP server for embedded SLURM guidance."""

from __future__ import annotations

import re
import shlex

from mcp.server.fastmcp import FastMCP

app = FastMCP("ssh-slurm")

NOT_FOUND = "The requested information could not be found in the embedded knowledge base."
REJECTED_TRAIN_CMD = (
    "Rejected train_cmd: do not set CUDA_VISIBLE_DEVICES, call pkill, or use "
    "dist_train.sh from generated SLURM scripts. Start from the embedded sample "
    "job and let SLURM assign CUDA_VISIBLE_DEVICES."
)

QUEUE_GUIDE = r'''---
type: reference
date: 2026-06-23
project: pipe-dino
summary: Canonical QUEUE_GUIDE.md from the s10 (H200) shared GPU server — SLURM command table, SBATCH option reference, troubleshooting, and Grafana monitoring URLs. Verbatim copy of the server's official guide.
---

# s10 (H200) SLURM Queue Guide — canonical copy

Verbatim copy of `/workspace/QUEUE_GUIDE.md` (host path `/srv/workspace/pipe/QUEUE_GUIDE.md`)
on the s10 server, captured 2026-06-23.

- Server: `pipe-dongmin-s10` (H200), SSH `dongmin@163.152.163.218 -p 23119`
- Container wrapper: `/usr/local/bin/pipe-mcp-s10`
- Host `~/workspace` is a symlink to `/srv/workspace/pipe`, which equals the
  container's `/workspace`.

This file fills the gap noted in `../20_syntheses/syn_slurm-shared-gpu-queue-batching-pattern.md`:
the synthesis abstracted the rules, but the literal guide text lived only on the server.

---

## QUEUE_GUIDE.md (verbatim)

```markdown
# SLURM 큐 사용 가이드 — pipe 팀 (s10)

> 이 컨테이너 (pipe-dongmin-s10) 안에서 학습 잡을 큐에 던지는 방법.

## TL;DR

```bash
sbatch sample-job.sh    # 잡 제출
squeue                  # 내 잡 보기
scancel <JOBID>         # 취소
sacct                   # 본인 잡 이력
```

`train.py` 자체는 수정할 필요 없음. `sample-job.sh` 만 본인 학습 명령에 맞게 편집.

## 자주 쓰는 명령

| 명령 | 설명 |
|---|---|
| `sbatch s.sh` | s.sh 잡을 큐에 제출 → 자원 빌 때 자동 실행 |
| `squeue -u $USER` | 내 pending/running 잡 |
| `squeue` | 전체 큐 (다른 팀 포함) |
| `scancel <id>` | 내 잡 취소 |
| `scancel -u $USER` | 내 모든 잡 취소 |
| `sacct -X` | 본인 잡 이력 (오늘) |
| `sacct -X --starttime=now-7days` | 최근 7일 이력 |
| `sinfo` | 노드/파티션 상태 |
| `scontrol show job <id>` | 잡 상세 정보 |

## 잡 스크립트 패턴

`/workspace/sample-job.sh` 참고. 핵심 골격:

```bash
#!/bin/bash
#SBATCH --gpus=1                                        # GPU 갯수
#SBATCH --time=24:00:00                                 # 최대 실행 시간 (HH:MM:SS)
#SBATCH --chdir=/tmp                                    # 호스트 cwd (호스트엔 /workspace 없음)
#SBATCH --output=/srv/workspace/pipe/slurm-%j.out              # 잡 출력 파일

# slurmd 는 host 사용자 권한 (docker 그룹 미가입) → docker exec 직접 불가.
# 대신 sudoers 무비번 wrapper 로 컨테이너 진입 → conda env 그대로 사용.
sudo -n /usr/local/bin/pipe-mcp-s10 bash -c "cd /workspace && python train.py"
```

## SBATCH 옵션 자주 쓰는 것

| 옵션 | 예시 | 의미 |
|---|---|---|
| `--gpus=N` | `--gpus=2` | GPU N개 요청 |
| `--gpus-per-node=N` | `--gpus-per-node=4` | 노드당 N개 (다중 노드 시) |
| `--time=HH:MM:SS` | `--time=12:00:00` | 최대 wall time |
| `--mem=NG` | `--mem=64G` | 메모리 N GB 요청 |
| `--cpus-per-task=N` | `--cpus-per-task=8` | 잡당 CPU N core |
| `--job-name=NAME` | `--job-name=baseline` | 잡 이름 (squeue 에 표시) |
| `--partition=PART` | `--partition=gpu_h200` | 특정 파티션 (10번이면 gpu_h200) |
| `--output=FILE` | `--output=run-%j.log` | stdout 경로 (%j = 잡 ID) |

## 인터랙티브 잡 (디버깅)

큐 안 거치고 GPU 한 장 즉시 잡고 셸:

```bash
srun --gpus=1 -t 1:00:00 --pty bash
# 잡 끝나고 컨테이너로 돌아옴
```

## 트러블슈팅

### 잡이 `Invalid account` 로 거부
- 본인 OS 계정이 SLURM 에 등록 안 됐을 가능성. 운영자에게 `sacctmgr add user` 요청.

### 잡이 즉시 fail (ExitCode 1:0)
- `--chdir` 빠뜨렸을 가능성. SLURM 잡은 호스트에서 시작되므로 `/workspace` 같은 컨테이너 경로는 못 씀.
  → `#SBATCH --chdir=/tmp` 또는 `/srv/workspace/pipe` (이건 컨테이너의 /workspace 와 동일).

### 잡 출력이 안 보임
- `--output=` 으로 명시 (default 는 cwd 의 slurm-N.out).
  → `#SBATCH --output=/srv/workspace/pipe/slurm-%j.out` 권장 (컨테이너에서도 /workspace 로 보임).

### 학습 도중 패키지 설치 필요
컨테이너 안에서 옵션 3가지:
1. `pip install --user xxx` — `~/.local` 에 설치. 권한 문제 없음. 가장 단순.
2. `pip install xxx` — `/opt/conda` 에 설치 (팀 그룹 write 권한 있어 가능). 같은 팀 멤버 공유.
3. 새 conda env: `conda create -n myenv python=3.10 && conda activate myenv && pip install xxx`.

후 sbatch 잡에서 `PYTHONPATH=~/.local/lib/python3.X/site-packages python train.py` 또는 conda env activate 한 번 하면 됨.

### 잡이 GPU 못 찾음
- 컨테이너에 GPU 노출됐는지 `docker exec pipe-dongmin-s10 nvidia-smi` 로 확인.

## 모니터링

- Grafana 큐/사용 현황: http://163.152.163.211:3000/d/slurm-queue/
- GPU 사용자별 추적: http://163.152.163.211:3000/d/gpu-by-user/

## 운영자 연락

큐/account 관련 문의: 본인 팀 운영자 또는 #gpu-ops 채널.
```
'''

SAMPLE_JOB_SCRIPT = r'''---
type: reference
date: 2026-06-23
project: pipe-dino
summary: Canonical sample-job.sh from the s10 (H200) shared GPU server — the official SBATCH template with the complete header block, the nvidia-smi GPU guard (>1000 MB threshold), and the container-wrapper invocation. Verbatim copy.
---

# s10 (H200) SLURM sample-job.sh — canonical copy

Verbatim copy of `/workspace/sample-job.sh` (host path `/srv/workspace/pipe/sample-job.sh`)
on the s10 server, captured 2026-06-23.

- Server: `pipe-dongmin-s10` (H200), SSH `dongmin@163.152.163.218 -p 23119`
- Container wrapper: `/usr/local/bin/pipe-mcp-s10`

This is the literal template referenced throughout the records ("copy the sample
script, change only `TRAIN_CMD`") and in
`../20_syntheses/syn_slurm-shared-gpu-queue-batching-pattern.md`. It confirms two
details the synthesis could only approximate:

- The GPU guard aborts when assigned-GPU memory use is `> 1000` MB (exact threshold).
- The container is re-entered via
  `sudo -n /usr/local/bin/pipe-mcp-s10 bash -c "export CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES && $TRAIN_CMD"`.

---

## sample-job.sh (verbatim)

```bash
#!/bin/bash
# SLURM 잡 샘플 — pipe 팀 (pipe-dongmin-s10, s10)
#
# 사용법: 컨테이너 안에서
#   sbatch sample-job.sh
#
# 본인 학습 명령에 맞춰 CMD 만 바꾸세요. train.py 코드는 수정 불필요.
#
# 동작 원리:
#   - sbatch → 호스트 slurmd 가 ${USER} 권한으로 본 스크립트 실행
#   - slurmd 는 docker group 미가입이라 docker exec 직접 호출 불가
#   - 대신 sudoers 에 무비번 등록된 wrapper(${TEAM}-mcp-${SERVER}) 통해 컨테이너 진입
#   - 컨테이너 안에서 conda env ($/workspace 코드, 의존성) 그대로 사용

#SBATCH --job-name=pipe-train
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --chdir=/tmp
#SBATCH --output=/srv/workspace/pipe/slurm-%j.out

# ───────── SLURM 자동 할당 GPU 사용 ─────────
# SLURM scheduler 가 free GPU 를 골라 $CUDA_VISIBLE_DEVICES 에 박아줌.
# 우리는 그 값 그대로 컨테이너에 전달 — SLURM accounting 일치.
if [ -z "${CUDA_VISIBLE_DEVICES:-}" ]; then
    echo "[ERROR] SLURM 이 GPU 할당 안 함 — #SBATCH --gpus 옵션 확인" >&2
    exit 1
fi
echo "[INFO] SLURM 할당 GPU: $CUDA_VISIBLE_DEVICES"

# ───────── hardware 실측 검증 (방어용 — SLURM 우회 사용자 충돌 방지) ─────────
# SLURM 이 카운트만 보고 점유 GPU 를 alloc 할 수 있음. 실측 사전 검사.
for gpu_idx in $(echo "$CUDA_VISIBLE_DEVICES" | tr ',' ' '); do
    USED_MB=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits --id=$gpu_idx 2>/dev/null | tr -d ' ')
    if [ -z "$USED_MB" ]; then
        echo "[ERROR] GPU $gpu_idx 정보 조회 실패" >&2
        exit 1
    fi
    if [ "$USED_MB" -gt 1000 ]; then
        echo "[ERROR] SLURM 이 GPU $gpu_idx 할당했으나 실측 ${USED_MB} MB 사용 중 (SLURM 우회 점유자 있음). 잡 종료." >&2
        exit 1
    fi
done
echo "[INFO] hardware 실측 검증 통과 — 학습 시작"

# ───────── 본인 학습 명령으로 변경 ─────────
# 예) TRAIN_CMD="cd /workspace/myrepo && python3 train.py --config configs/foo.yaml"
TRAIN_CMD="cd /workspace && python3 -c 'import torch; print(torch.cuda.is_available(), torch.cuda.device_count())'"

# wrapper 통해 컨테이너 진입 — $CUDA_VISIBLE_DEVICES 가 SLURM 이 정한 값
sudo -n /usr/local/bin/pipe-mcp-s10 bash -c "export CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES && $TRAIN_CMD"
```
'''

SHARED_GPU_PATTERN = r'''---
type: synthesis
date: 2026-06-20
project:
summary: On shared GPU servers, run all CUDA training/inference through the SLURM queue with job-local safety guards — request GPU count (never pin a physical id), verify the assigned GPU is free, use an explicit bash sbatch script, and write output to host-visible paths via the container wrapper.
---

# Shared-GPU SLURM Queueing & Batching Pattern

## Context

Server work across two projects (`vggt-det`, May–Jun 2026; `pipe-dino`, Jun 2026)
on two shared GPU servers (H200 via `pipe-mcp-s10`, RTX A6000 via `pipe-mcp-s8`)
surfaced the same core problem repeatedly: the queue system is the official way to
reserve GPUs, but the physical machine can hold state that the queue does not fully
account for. The SLURM accounting may report a node as idle while a physical GPU is
already heavily occupied by work outside SLURM's visibility.

Beyond the accounting mismatch, each new server session uncovered an additional
failure mode — `sbatch --wrap` running under `/bin/sh` instead of `bash`,
host-vs-container working directory mismatches, headless environment gaps, and
SLURM/Munge availability risks. None of these is unique to a project; all of them
recur whenever shared GPU infrastructure is used.

The existing `syn_vggt-det-shared-server-slurm-smoke-pattern.md` captures the
original VGGT-Det pattern. This synthesis generalizes the pattern across projects
and adds the failure modes that surfaced in later `pipe-dino` sessions.

## Core Pattern

The submission flow is the same regardless of project:

```text
read the server's QUEUE_GUIDE.md
  -> copy the sample job script for this project
  -> request GPU count through SLURM (not a physical GPU id)
  -> let SLURM set CUDA_VISIBLE_DEVICES; pass it through the container wrapper
  -> inside the job, inspect the assigned physical GPU's free memory
  -> run training only if the GPU is actually free enough
  -> preserve the job id, log path, work_dir, and exact config overrides
```

The key rule is that SLURM owns reservation, the job script owns a fast physical-state
sanity check, and the training command owns only the project-specific run. Keeping
these three responsibilities separate is what lets a job exit safely when the
accounting state diverges from physical reality.

## Submission & Monitoring Commands

Standard job submit and queue inspection:

```bash
sbatch <script>.sbatch
squeue -u "$USER"
squeue -j <ids> -o '%i %t %M %R %j'
```

Full accounting record after a job finishes:

```bash
sacct -j <id> --format=JobID,JobName%32,State,ExitCode,Elapsed,Start,End -P
```

Diagnose a pending job:

```bash
scontrol show job <id>
sinfo -p <partition>
```

Stream logs in real time:

```bash
tail -f /srv/workspace/pipe/slurm-<name>-<jobid>.out
```

Check whether the scheduler is available before submitting (useful at session start):

```bash
command -v sbatch && command -v squeue && command -v srun
```

## Batching & Dependencies

The standard batching pattern is a short smoke job followed by a full training job
chained through a SLURM dependency. The smoke job runs one epoch with batch size 1;
the full job becomes eligible only after the smoke job completes successfully.

When the smoke job fails for any reason — including a job-local GPU guard or a
configuration error — the downstream full job enters `DependencyNeverSatisfied` and
must be cancelled manually with `scancel`. This is the correct behavior: the chain
prevents a known-broken configuration from consuming long GPU hours unattended.

During `pipe-dino` server work the standard chain was a 1-epoch smoke job followed by
a 36-epoch full training job submitted together at handoff time. Monitoring focused on
the smoke job first; the full job took care of itself if the smoke completed.

## Recurring Gotchas

### Scheduler/Physical GPU Mismatch

SLURM can assign a GPU that is already heavily used by a process it does not account
for. The job-local guard catches this before training starts:

```
[ERROR] SLURM assigned GPU 0, but it is already using 125739 MB. Exiting.
```

The guard inspects `nvidia-smi` memory for the assigned physical GPU and aborts if
usage exceeds a threshold (around 1000 MB was used in practice). This is not a
workaround to be cleaned up — it is a permanent part of any job script for these
servers until the accounting mismatch is resolved by the server administrator.

### `sbatch --wrap` Runs Under `/bin/sh`

Using `sbatch --wrap '...'` instead of a dedicated script file causes the job to run
under `/bin/sh`, which does not support `set -o pipefail`. The job fails immediately
with:

```
/var/spool/slurmd/job00057/slurm_script: 4: set: Illegal option -o pipefail
```

The training code is never reached. Any downstream job depending on this one becomes
`DependencyNeverSatisfied`. The fix is always to write an explicit bash script:

```bash
#!/bin/bash
set -euo pipefail
```

Never use `sbatch --wrap` for jobs that need `bash` features.

### Host vs Container Working Directory

On these servers, SLURM jobs start on the host filesystem, not inside the container.
A job script that references `/workspace/...` paths directly will fail because those
paths do not exist on the host. The correct pattern from `QUEUE_GUIDE.md` is:

- `#SBATCH --chdir=/tmp` so the job starts in a path that exists on the host
- Output goes to the host-visible path `/srv/workspace/pipe/<name>-<jobid>.out`
- The container is re-entered through the wrapper:
  `sudo -n /usr/local/bin/pipe-mcp-s{8,10} bash -c "export CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES && <train_cmd>"`
- Inside the container, the same log appears at `/workspace/slurm-<jobid>.out`

Reading `QUEUE_GUIDE.md` before writing a new script is not optional. This
host/container boundary is the single most common source of "job starts but does
nothing" failures.

### Headless `libGL.so.1` (open3d via mmdet3d)

When `mmdet3d.visualization` is in scope, the mmdet3d registry loads `open3d`, which
calls `libGL.so.1`. That shared library is absent in headless SLURM environments:

```
OSError: libGL.so.1: cannot open shared object file: No such file or directory
```

The fix for training jobs is to suppress the visualization backend entirely:
`visualizer=None`, `default_scope=mmengine`, and prefix all mmdet3d type strings with
`mmdet3d.` to keep registry lookups working. Do not apply `default_scope=mmengine` to
inference jobs: it breaks the dataset registry lookup and the job will fail trying to
resolve dataset types.

### Missing `tensorboard` Module at Smoke Time

Smoke jobs should not expand the base container environment. If the training config
references a `TensorboardVisBackend`, and `tensorboard` is not installed, the job
fails on import. The smoke fix is `visualizer=None` and a fresh work directory, not
installing packages into the base environment.

### Munge / SLURM Outage

SLURM has historically had Munge authentication failures on these servers. If the
scheduler is unavailable, the rule is to halt and report — never fall back to a
direct `CUDA_VISIBLE_DEVICES=N python ...` invocation outside the queue. A direct
fallback bypasses the reservation model and may collide with another user's job.

## Anti-Patterns

The following patterns have each caused real failures or policy violations across
these server sessions:

- Encoding a physical GPU id inside `TRAIN_CMD`:
  `CUDA_VISIBLE_DEVICES=1 python tools/train.py ...` bypasses SLURM's assignment
  model entirely.
- Using `tools/dist_train.sh` on a shared server. That script contains
  `pkill -9 python` and `pkill -9 -f train.py`, which will kill unrelated processes.
- Submitting via `sbatch --wrap` when the script body needs `bash` features.
- Installing packages into the base container environment during a smoke run. Keep
  all changes user-local or project-local.
- Writing output to `/workspace/...` paths in `#SBATCH` directives without
  `--chdir=/tmp`; those paths do not exist on the host.
- Applying `default_scope=mmengine` to inference jobs.

## Reuse Checklist

Use this checklist when preparing a SLURM job on a new shared GPU server session.

- Read the server's `QUEUE_GUIDE.md` before writing any script.
- Start from the server's sample job script; copy it and change only `TRAIN_CMD`.
- Use `#SBATCH --gpus=1` or `#SBATCH --gres=gpu:1` (check which syntax the server
  accepts); do not encode a physical GPU number.
- Begin the script with `#!/bin/bash` and `set -euo pipefail`; never use `--wrap`.
- Use `#SBATCH --chdir=/tmp` and set `--output` to a host-visible path under
  `/srv/workspace/pipe/`.
- Pass `CUDA_VISIBLE_DEVICES` through the container wrapper; do not set it inside
  `TRAIN_CMD`.
- Add an early `nvidia-smi` memory guard that aborts if the assigned GPU is busy.
- Apply smoke overrides: one epoch, batch size 1, minimal workers, `WANDB_MODE=offline`
  or `WANDB_DISABLED=true`.
- Suppress visualization for headless runs: `visualizer=None`; use `default_scope=mmengine`
  only for training jobs, not inference.
- Chain a full training job as a SLURM dependency on the smoke job succeeding.
- After the job completes, record: job id, log path, output `work_dir`, exact annotation
  files, and all config overrides used.

## Environment Notes

Two container wrappers are in use across recorded sessions:

- `pipe-mcp-s10`: H200 server (SSH port 23119), partition `gpu_h200`
- `pipe-mcp-s8`: RTX A6000 server (hostname `pipe-dongmin-s8`), partition `gpu_a6000`

Both servers have a `QUEUE_GUIDE.md` and a `sample-job.sh` at `/workspace/`. The
wrapper name and SSH target differ; the pattern is identical.

Two GPU-request syntaxes have appeared in recorded scripts: `#SBATCH --gpus=1`
(most sessions) and `#SBATCH --gres=gpu:1` (projection-fix-overfit plan, Jun 2026).
Check the server's queue guide for the accepted form; both mean "request one GPU" and
both let SLURM set `CUDA_VISIBLE_DEVICES`.

## Source Records

This synthesis draws from the following records and the earlier project-scoped synthesis:

- `../20_syntheses/syn_vggt-det-shared-server-slurm-smoke-pattern.md`
- `../10_records/2026-05-24_vggt-det_server-training-handoff.md`
- `../10_records/2026-05-25_vggt-det_server-smoke-test-setup.md`
- `../10_records/2026-05-25_vggt-det_slurm-smoke-test-completed.md`
- `../10_records/2026-06-04_vggt-det_pipe3d-server-handoff-local-smoke.md`
- `../10_records/2026-06-05_vggt-det_h200-container-memory-search.md`
- `../10_records/2026-06-05_vggt-det_pipe3d-h200-server-1epoch-smoke-success.md`
- `../10_records/2026-06-05_vggt-det_s8-slurm-smoke-run-handoff.md`
- `../10_records/2026-06-14_pipe-dino_detr3d-h200-smoke-and-36ep.md`
- `../10_records/2026-06-15_pipe-dino_detr3d-h200-retrain.md`
- `../10_records/2026-06-15_pipe-dino_detr3d-h200-retrain-pcfix.md`
- `../10_records/2026-06-15_pipe-dino_detr3d-h200-retrain-100ep.md`
- `../10_records/2026-06-18_pipe-dino_a6000-sunrgbd-training-plan.md`
- `../10_records/2026-06-18_pipe-dino_a6000-sunrgbd-step4-plan.md`
- `../10_records/2026-06-18_pipe-dino_a6000-sunrgbd-step4-step5-closure.md`
- `../10_records/2026-06-18_pipe-dino_a6000-sunrgbd-step5-smoke.md`
- `../10_records/2026-06-18_pipe-dino_sunrgbd-detr3d-training-queued.md`
- `../10_records/2026-06-18_pipe-dino_sunrgbd-detr3d-smoke-success-full-running.md`
- `../10_records/2026-06-18_pipe-dino_sunrgbd-detr3d-36ep-complete.md`
- `../10_records/2026-06-18_pipe-dino_sunrgbd-small-batch-overfit-plan.md`
- `../10_records/2026-06-19_pipe-dino_sunrgbd-projection-fix-overfit-plan.md`
- `../10_records/2026-06-19_pipe-dino_sunrgbd-projection-fix-overfit-result.md`

## Closing

The pattern generalizes cleanly across projects and servers because the boundaries are
stable: SLURM owns reservation, the job script owns a fast physical-state check, and
the training command owns only the project-specific run. Adding the pipe-dino sessions
to the record base confirmed two things the vggt-det synthesis could not yet say: that
`sbatch --wrap` is reliably unsafe on these servers, and that the host/container
working directory split is a structural property of the server setup, not a one-time
accident. Future sessions on any shared GPU server in this environment should start
from this checklist.
'''

VGGT_DET_PATTERN = r'''---
type: synthesis
date: 2026-05-26
project: VGGT-Det-CVPR2026
summary: Shared GPU servers should run VGGT-Det smoke tests through SLURM with job-local safety guards instead of hard-coding physical GPU ids or modifying the base container environment.
---

# VGGT-Det Shared Server SLURM Smoke Pattern

## Context

VGGT-Det server work exposed a recurring shared-cluster problem: the queue
system may be the official way to reserve GPUs, but the physical machine can
still contain state that the queue does not fully account for.

In the H200 server session, the documented path was to submit jobs through
SLURM and let the wrapper pass `CUDA_VISIBLE_DEVICES` into the container. That
rule mattered because directly pinning a physical GPU inside a training command
would bypass the server's intended reservation model. At the same time, SLURM
reported the node as idle while physical GPU 0 was already heavily occupied by
work outside SLURM accounting. A normal one-GPU smoke job was therefore
assigned GPU 0 and had to exit before training started.

The durable lesson is not "always use GPU 1." The durable lesson is to respect
the scheduler while adding job-local checks that detect scheduler/physical
state mismatches before a training process touches a busy card.

## Pattern

Run smoke tests as queued jobs, keep environment changes local to the user or
project, and make the job script verify the actual GPU state before training.

The practical shape is:

```text
server guide / sample job
  -> copy job script for the project
  -> request GPU count through SLURM
  -> let SLURM provide CUDA_VISIBLE_DEVICES
  -> inside the job, inspect assigned physical GPU memory
  -> run smoke training only if the assigned GPU is actually free enough
  -> preserve logs, work_dir, and exact config overrides
```

For VGGT-Det, this kept the smoke test compatible with the server guide while
preventing accidental interference with an already occupied H200. The first
job exited safely when SLURM assigned the busy physical GPU 0. A later
smoke-specific workaround requested both GPUs, inspected the allocated physical
cards, and ran only on a card below the memory threshold; that completed a
one-sample, one-epoch training smoke test on GPU 1.

This workaround should be treated as collision avoidance for a specific
accounting mismatch, not as the normal reservation procedure. The normal
procedure remains: request resources from SLURM, change the training command,
and avoid hard-coding a physical GPU id inside `TRAIN_CMD`.

## Environment Boundary

The server container environment should be changed as narrowly as possible.

During the smoke setup, no new conda environment was created and the base
Torch/TorchVision stack was not replaced. Missing packages were installed into
the user site-packages, OpenCV was switched to the headless build to avoid the
`libGL.so.1` runtime dependency, and repo-local extensions were built only as
needed for import and smoke training.

This approach is not a universal best practice for all training runs. It was
the right boundary for this server session because the container already had a
working CUDA 12.8 PyTorch stack, other users could be affected by broad base
environment changes, and the immediate goal was a smoke test rather than a
full reproducibility rebuild. For a clean long-term training environment, the
project should still record the exact package set or build a dedicated
environment when server policy allows it.

## Reuse Checklist

Use this checklist when preparing another VGGT-Det or similar shared-server
smoke run.

- Start from the server's sample SLURM script or queue guide.
- Replace the training command; do not encode a physical GPU id in it.
- Request GPU count with SLURM directives such as `#SBATCH --gpus=1`.
- Let the wrapper pass SLURM's `CUDA_VISIBLE_DEVICES` into the container.
- Add an early `nvidia-smi` memory guard for the assigned GPU.
- Use small smoke overrides: one epoch, one sample, batch size 1, minimal
  workers, local/offline logging.
- Keep package changes user-local or project-local unless the server owner
  explicitly approves broader changes.
- Avoid helper scripts that kill unrelated Python processes on a shared
  machine.
- Record the job id, log path, output `work_dir`, exact annotation files, and
  config overrides.

## Failure Signals

Several signals should stop the run before it becomes a real training job.

- SLURM assigns a physical GPU whose current memory use is already high.
- The queue guide says to use the wrapper, but the command bypasses it with a
  direct container or physical-GPU invocation.
- A script contains broad process-kill commands such as `pkill -9 python` on a
  shared server.
- Import fixes require changing the base container package stack instead of a
  user-local or project-local layer.
- Dataset symlinks or smoke annotation files do not match the paths expected
  by the training config.

These are not just operational inconveniences. Each signal means the smoke
test may either disturb another user's job or produce a result that cannot be
replayed from the documented server procedure.

## Source Records

- `../10_records/2026-05-24_vggt-det_server-training-handoff.md`
- `../10_records/vggt-det/2026-05-25_vggt-det_server-smoke-test-setup.md`
- `../10_records/vggt-det/2026-05-25_vggt-det_slurm-smoke-test-completed.md`

## Closing

The reusable pattern is to separate reservation, safety, and training. SLURM
owns reservation; the job script owns a fast physical-state sanity check; the
training command owns only the project-specific smoke run. Keeping those
boundaries clear allowed VGGT-Det to complete a smoke test on the shared H200
server without hard-coding GPU ids, replacing the base container stack, or
touching a GPU that was already occupied outside SLURM accounting.
'''



def _extract_fenced_block(markdown: str, language: str) -> str:
    """Return the first fenced block for language from markdown."""
    pattern = re.compile(
        rf"^```{re.escape(language)}\s*\n(.*?)^```\s*$",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(markdown)
    if match is None:
        raise ValueError("fenced block not found")
    return match.group(1).rstrip("\n")


def _heading_level(line: str) -> int | None:
    match = re.match(r"^(#+)\s+", line)
    if match is None:
        return None
    return len(match.group(1))


def _extract_section(markdown: str, heading: str) -> str:
    """Extract a markdown section by exact heading text without leading hashes."""
    lines = markdown.splitlines()
    start = None
    level = None
    for index, line in enumerate(lines):
        parsed_level = _heading_level(line)
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
        parsed_level = _heading_level(lines[index])
        if parsed_level is not None and parsed_level <= level:
            end = index
            break
    section = "\n".join(lines[start:end]).strip()
    if not section:
        raise ValueError("section empty")
    return section


def _extract_first_table(markdown: str, section_heading: str) -> str:
    section = _extract_section(markdown, section_heading)
    rows = []
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


def _safe_section(markdown: str, heading: str) -> str:
    try:
        return _extract_section(markdown, heading)
    except Exception:
        return NOT_FOUND


def _safe_table(markdown: str, heading: str) -> str:
    try:
        return _extract_first_table(markdown, heading)
    except Exception:
        return NOT_FOUND


def _replace_sbatch_value(script: str, option: str, value: str | int) -> str:
    pattern = re.compile(rf"^#SBATCH\s+--{re.escape(option)}=.*$", re.MULTILINE)
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


def _force_sbatch_directive(script: str, option: str, value: str) -> str:
    return _replace_sbatch_value(script, option, value)


def _replace_train_cmd(script: str, train_cmd: str) -> str:
    quoted = shlex.quote(train_cmd)
    pattern = re.compile(r'^TRAIN_CMD=.*$', re.MULTILINE)
    replacement = f"TRAIN_CMD={quoted}"
    if pattern.search(script) is None:
        raise ValueError("TRAIN_CMD assignment not found")
    return pattern.sub(replacement, script, count=1)


def _contains_rejected_train_cmd(train_cmd: str) -> bool:
    lowered = train_cmd.lower()
    return (
        "cuda_visible_devices=" in lowered
        or re.search(r"(^|[;&|\s])pkill($|[;&|\s])", lowered) is not None
        or "dist_train.sh" in lowered
    )


def _keyword_diagnostics(symptom: str) -> str | None:
    text = symptom.lower()
    sections: list[str] = []
    if "invalid account" in text or "account" in text:
        sections.append(_safe_section(QUEUE_GUIDE, "잡이 `Invalid account` 로 거부"))
    if "exitcode" in text or "exit code" in text or "fail" in text or "failed" in text:
        sections.append(_safe_section(QUEUE_GUIDE, "잡이 즉시 fail (ExitCode 1:0)"))
    if "output" in text or "log" in text or "stdout" in text:
        sections.append(_safe_section(QUEUE_GUIDE, "잡 출력이 안 보임"))
    if "gpu" in text or "cuda" in text or "visible" in text or "memory" in text:
        sections.append(_safe_section(SHARED_GPU_PATTERN, "Scheduler/Physical GPU Mismatch"))
        sections.append(_safe_section(VGGT_DET_PATTERN, "Failure Signals"))
    if "wrap" in text or "/bin/sh" in text or "bash" in text:
        sections.append(_safe_section(SHARED_GPU_PATTERN, "`sbatch --wrap` Runs Under `/bin/sh`"))
    if "directory" in text or "chdir" in text or "workspace" in text or "path" in text:
        sections.append(_safe_section(SHARED_GPU_PATTERN, "Host vs Container Working Directory"))
    if "libgl" in text or "open3d" in text or "mmdet3d" in text:
        sections.append(_safe_section(SHARED_GPU_PATTERN, "Headless `libGL.so.1` (open3d via mmdet3d)"))
    if "tensorboard" in text:
        sections.append(_safe_section(SHARED_GPU_PATTERN, "Missing `tensorboard` Module at Smoke Time"))
    if "munge" in text or "outage" in text or "slurmctld" in text:
        sections.append(_safe_section(SHARED_GPU_PATTERN, "Munge / SLURM Outage"))

    cleaned = [section for section in sections if section != NOT_FOUND]
    if not cleaned:
        return None
    return "\n\n".join(cleaned)


@app.tool()
def get_queue_guide() -> str:
    """Return the embedded canonical s10 SLURM queue guide."""
    return QUEUE_GUIDE


@app.tool()
def get_sample_job_script() -> str:
    """Return the embedded canonical s10 sample SBATCH job record."""
    return SAMPLE_JOB_SCRIPT


@app.tool()
def get_server_info() -> str:
    """Return embedded server facts without enabling SSH or SLURM actions."""
    try:
        queue_intro = QUEUE_GUIDE.split("## QUEUE_GUIDE.md (verbatim)", 1)[0].strip()
        env_notes = _safe_section(SHARED_GPU_PATTERN, "Environment Notes")
        return "\n\n".join([queue_intro, env_notes]).strip()
    except Exception:
        return NOT_FOUND


@app.tool()
def generate_sbatch_script(
    train_cmd: str,
    job_name: str = "pipe-train",
    gpus: int = 1,
    time: str = "24:00:00",
    mem: str = "32G",
    cpus: int = 8,
    server: str = "s10",
) -> str:
    """Generate a safe s10 SBATCH script by changing only template slots."""
    del server
    if _contains_rejected_train_cmd(train_cmd):
        return REJECTED_TRAIN_CMD
    if gpus < 1 or cpus < 1:
        return "Rejected request: gpus and cpus must be positive integers."

    try:
        script = _extract_fenced_block(SAMPLE_JOB_SCRIPT, "bash")
        replacements = (
            ("job-name", job_name),
            ("gpus", gpus),
            ("cpus-per-task", cpus),
            ("mem", mem),
            ("time", time),
        )
        for option, value in replacements:
            script = _replace_sbatch_value(script, option, value)
        script = _force_sbatch_directive(script, "chdir", "/tmp")
        script = _force_sbatch_directive(script, "output", "/srv/workspace/pipe/slurm-%j.out")
        script = _replace_train_cmd(script, train_cmd)
        return script
    except Exception:
        return NOT_FOUND


@app.tool()
def diagnose(symptom: str) -> str:
    """Return targeted troubleshooting guidance from embedded records."""
    try:
        targeted = _keyword_diagnostics(symptom)
        if targeted is not None:
            return targeted
        return "\n\n".join([
            _safe_section(QUEUE_GUIDE, "트러블슈팅"),
            _safe_section(SHARED_GPU_PATTERN, "Recurring Gotchas"),
        ])
    except Exception:
        return NOT_FOUND


@app.tool()
def get_checklist() -> str:
    """Return reusable SLURM preparation checklists."""
    try:
        return "\n\n".join([
            _safe_section(SHARED_GPU_PATTERN, "Reuse Checklist"),
            _safe_section(VGGT_DET_PATTERN, "Reuse Checklist"),
        ])
    except Exception:
        return NOT_FOUND


@app.tool()
def list_commands() -> str:
    """Return command tables and command snippets from embedded guidance."""
    try:
        return "\n\n".join([
            _safe_table(QUEUE_GUIDE, "자주 쓰는 명령"),
            _safe_section(SHARED_GPU_PATTERN, "Submission & Monitoring Commands"),
        ])
    except Exception:
        return NOT_FOUND


@app.resource("slurm://queue-guide")
def queue_guide_resource() -> str:
    """Embedded canonical queue guide."""
    return QUEUE_GUIDE


@app.resource("slurm://sample-job")
def sample_job_resource() -> str:
    """Embedded canonical sample job."""
    return SAMPLE_JOB_SCRIPT


@app.resource("slurm://synthesis/shared-gpu")
def shared_gpu_resource() -> str:
    """Embedded shared-GPU batching synthesis."""
    return SHARED_GPU_PATTERN


@app.resource("slurm://synthesis/vggt-det")
def vggt_det_resource() -> str:
    """Embedded VGGT-Det smoke-test synthesis."""
    return VGGT_DET_PATTERN


if __name__ == "__main__":
    app.run()
