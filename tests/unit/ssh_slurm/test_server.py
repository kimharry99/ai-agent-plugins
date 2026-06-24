from __future__ import annotations

import importlib.util
import shlex
import sys
import types
import unittest
from pathlib import Path
from typing import Any


SERVER_PATH = Path(__file__).parents[3] / "ssh-slurm" / "server.py"


class FakeFastMCP:
    """Minimal FastMCP test double for decorator registration."""

    def __init__(self, name: str) -> None:
        self.name = name

    def tool(self) -> Any:
        """Return a decorator that leaves tool functions unchanged."""
        return ToolDecorator()

    def run(self) -> None:
        """Match the real FastMCP surface used by server.py."""


class ToolDecorator:
    """Callable decorator object that returns functions unchanged."""

    def __call__(self, function: Any) -> Any:
        """Return the decorated function unchanged."""
        return function


class ServerModuleLoader:
    """Load ssh-slurm/server.py with a fake MCP dependency."""

    @classmethod
    def load(cls) -> types.ModuleType:
        """Return a freshly loaded server module."""
        mcp_module = types.ModuleType("mcp")
        server_module = types.ModuleType("mcp.server")
        fastmcp_module = types.ModuleType("mcp.server.fastmcp")
        fastmcp_module.FastMCP = FakeFastMCP
        sys.modules["mcp"] = mcp_module
        sys.modules["mcp.server"] = server_module
        sys.modules["mcp.server.fastmcp"] = fastmcp_module

        spec = importlib.util.spec_from_file_location(
            "ssh_slurm_server_under_test",
            SERVER_PATH,
        )
        if spec is None or spec.loader is None:
            raise AssertionError("failed to load server module spec")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


class TestGenerateSbatchScript(unittest.TestCase):
    """Tests for the public generate_sbatch_script MCP tool."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ServerModuleLoader.load()
        cls.generate = staticmethod(
            cls.server.SlurmGuidanceTools.generate_sbatch_script,
        )

    def test_default_script_is_generic(self) -> None:
        script = self.generate()

        assert script.startswith("#!/bin/bash\n")
        assert "#SBATCH --job-name=slurm-job\n" in script
        assert "#SBATCH --gpus=1\n" in script
        assert "#SBATCH --cpus-per-task=8\n" in script
        assert "#SBATCH --mem=32G\n" in script
        assert "#SBATCH --time=24:00:00\n" in script
        assert "#SBATCH --output=slurm-%j.out\n" in script
        assert "set -euo pipefail\n" in script
        assert "TRAIN_CMD='python train.py'\n" in script
        assert "#SBATCH --partition=" not in script
        assert "#SBATCH --chdir=" not in script

        site_specific_strings = (
            "/workspace",
            "/srv/workspace/pipe",
            "pipe-mcp-s10",
            "gpu_h200",
            "pipe-train",
        )
        for site_value in site_specific_strings:
            assert site_value not in script

    def test_wrapper_branching(self) -> None:
        direct_script = self.generate(
            train_cmd="python train.py",
            gpu_guard="disabled",
        )
        wrapped_script = self.generate(
            train_cmd="python train.py",
            wrapper_cmd="sudo -n /opt/slurm-wrapper",
            gpu_guard="disabled",
        )

        assert 'bash -lc "$RUN_CMD"' in direct_script
        assert "sudo -n /opt/slurm-wrapper" not in direct_script
        assert 'sudo -n /opt/slurm-wrapper bash -lc "$RUN_CMD"' in wrapped_script

    def test_optional_sbatch_workdir_and_env_options(self) -> None:
        script = self.generate(
            train_cmd="python train.py",
            partition="debug-gpu",
            chdir="/scratch/jobs",
            output="logs/train-%j.out",
            extra_sbatch_options={
                "constraint": "a100",
                "exclusive": True,
            },
            env={
                "PYTHONPATH": "src",
                "WANDB_MODE": "offline",
            },
            workdir="/project/train",
            gpu_guard="disabled",
        )

        assert "#SBATCH --partition=debug-gpu\n" in script
        assert "#SBATCH --chdir=/scratch/jobs\n" in script
        assert "#SBATCH --output=logs/train-%j.out\n" in script
        assert "#SBATCH --constraint=a100\n" in script
        assert "#SBATCH --exclusive\n" in script
        assert "export PYTHONPATH=src\n" in script
        assert "export WANDB_MODE=offline\n" in script
        assert "cd /project/train && " in script

    def test_gpu_guard_modes(self) -> None:
        skip_script = self.generate()
        error_script = self.generate(gpu_guard="error_if_missing")
        disabled_script = self.generate(gpu_guard="disabled")

        assert "command -v nvidia-smi" in skip_script
        assert "skipping GPU guard" in skip_script
        assert "[ERROR] nvidia-smi is unavailable." in error_script
        assert "command -v nvidia-smi" not in disabled_script

    def test_train_cmd_quoting_is_preserved(self) -> None:
        train_cmd = 'python -c "print(\'quoted value\')" --name "two words"'
        script = self.generate(train_cmd=train_cmd, gpu_guard="disabled")

        assert f"TRAIN_CMD={shlex.quote(train_cmd)}\n" in script
        assert 'RUN_CMD="$TRAIN_CMD"\n' in script
        assert 'bash -lc "$RUN_CMD"\n' in script
