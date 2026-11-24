"""Minimal BaseTool shim for the vendored OpenMontage tools.

This is a trimmed copy of OpenMontage's tools/base_tool.py, keeping only
what the three vendored tools in this repo need: the ToolResult dataclass,
the enums used in tool class attributes, and BaseTool.run_command.
The full OpenMontage base tool also handles Backlot event emission, cost
tracking, and retries — none of which this render pipeline uses.
Upstream: https://github.com/openmontage/openmontage (AGPL-3.0).
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class ToolTier(str, Enum):
    CORE = "core"
    VOICE = "voice"
    ENHANCE = "enhance"
    GENERATE = "generate"
    SOURCE = "source"
    ANALYZE = "analyze"
    PUBLISH = "publish"


class ToolStability(str, Enum):
    EXPERIMENTAL = "experimental"
    BETA = "beta"
    PRODUCTION = "production"


class ToolStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"


class ToolRuntime(str, Enum):
    LOCAL = "local"
    LOCAL_GPU = "local_gpu"
    API = "api"
    HYBRID = "hybrid"


class ExecutionMode(str, Enum):
    SYNC = "sync"
    ASYNC = "async"


class Determinism(str, Enum):
    DETERMINISTIC = "deterministic"
    SEEDED = "seeded"
    STOCHASTIC = "stochastic"


class ResumeSupport(str, Enum):
    NONE = "none"
    FROM_START = "from_start"
    FROM_CHECKPOINT = "from_checkpoint"


@dataclass
class ResourceProfile:
    cpu_cores: int = 1
    ram_mb: int = 512
    vram_mb: int = 0
    disk_mb: int = 100
    network_required: bool = False


@dataclass
class RetryPolicy:
    max_retries: int = 0
    backoff_seconds: float = 1.0
    retryable_errors: list[str] = field(default_factory=list)


@dataclass
class ToolResult:
    """Standard result returned by tool execution."""

    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    error: Optional[str] = None
    cost_usd: Optional[float] = 0.0
    duration_seconds: float = 0.0
    seed: Optional[int] = None
    model: Optional[str] = None
    from_cache: bool = False


class BaseTool(ABC):
    """Minimal base class: uniform interface + subprocess helper."""

    name = "base"
    version = "0.1.0"

    @abstractmethod
    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        raise NotImplementedError

    def run_command(
        self,
        cmd: list[str],
        *,
        timeout: Optional[int] = None,
        cwd: Optional[Path] = None,
    ) -> subprocess.CompletedProcess:
        """Run a subprocess command with standard error handling."""
        resolved_cmd = list(cmd)
        if platform.system() == "Windows" and resolved_cmd:
            exe = shutil.which(resolved_cmd[0])
            if exe:
                resolved_cmd[0] = exe
        try:
            return subprocess.run(
                resolved_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                cwd=cwd,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            stdout = (exc.stdout or "").strip()
            detail = stderr or stdout or str(exc)
            raise ToolCommandError(
                exc.returncode,
                exc.cmd,
                output=exc.output,
                stderr=exc.stderr,
                detail=detail,
            ) from exc


class ToolCommandError(subprocess.CalledProcessError):
    """Subprocess failure with a human-readable detail string."""

    def __init__(self, returncode, cmd, output=None, stderr=None, detail=None):
        super().__init__(returncode, cmd, output=output, stderr=stderr)
        self.detail = detail or str(self)

    def __str__(self):
        return self.detail or super().__str__()


class DependencyError(Exception):
    pass
