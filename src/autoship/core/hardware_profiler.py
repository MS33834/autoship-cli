"""Hardware profiling to recommend a default model tier."""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from typing import Literal, cast

logger = logging.getLogger("autoship")


@dataclass
class HardwareProfile:
    """Summary of local compute resources relevant to model inference."""

    cpu_cores: int
    memory_gb: float
    has_gpu: bool
    recommended_tier: Literal[1, 2, 3]


def detect_hardware() -> HardwareProfile:
    """Detect CPU, RAM and GPU availability and recommend a model tier."""
    cpu_cores = _cpu_count()
    memory_gb = _memory_gb()
    has_gpu = _has_gpu()

    # Tier 3 (deep thinking) needs significant resources.
    if cpu_cores >= 8 and memory_gb >= 16 and has_gpu:
        recommended_tier: Literal[1, 2, 3] = 3
    elif cpu_cores >= 4 and memory_gb >= 8:
        recommended_tier = 2
    else:
        recommended_tier = 1

    return HardwareProfile(
        cpu_cores=cpu_cores,
        memory_gb=memory_gb,
        has_gpu=has_gpu,
        recommended_tier=recommended_tier,
    )


def _cpu_count() -> int:
    """Return the number of logical CPUs, defaulting to 2 if unknown."""
    try:
        import os

        return os.cpu_count() or 2
    except Exception:  # noqa: BLE001
        return 2


def _memory_gb() -> float:
    """Return total system memory in gigabytes."""
    try:
        import psutil

        return float(psutil.virtual_memory().total) / (1024**3)
    except Exception as exc:  # noqa: BLE001
        logger.debug("psutil unavailable or failed: %s", exc)

    # Fallback for Linux systems without psutil.
    try:
        with open("/proc/meminfo") as f:  # noqa: PTH123
            for line in f:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    return kb / (1024**2)
    except (OSError, ValueError):
        pass

    logger.warning("Could not detect system memory; assuming 8 GB")
    return 8.0


def _has_gpu() -> bool:
    """Return True if a GPU runtime appears to be available."""
    if shutil.which("nvidia-smi"):
        return True
    try:
        import torch  # pyright: ignore[reportMissingImports]

        return cast(bool, torch.cuda.is_available())  # pyright: ignore[reportUnknownMemberType]
    except Exception:  # noqa: BLE001
        return False
