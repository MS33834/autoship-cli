"""Tests for hardware profiling."""

from __future__ import annotations

import sys
from unittest.mock import patch

from autoship.core.hardware_profiler import HardwareProfile, detect_hardware


def test_detect_hardware_recommends_tier_3() -> None:
    with (
        patch("autoship.core.hardware_profiler._cpu_count", return_value=16),
        patch("autoship.core.hardware_profiler._memory_gb", return_value=32.0),
        patch("autoship.core.hardware_profiler._has_gpu", return_value=True),
    ):
        profile = detect_hardware()
    assert profile.recommended_tier == 3


def test_detect_hardware_recommends_tier_2() -> None:
    with (
        patch("autoship.core.hardware_profiler._cpu_count", return_value=4),
        patch("autoship.core.hardware_profiler._memory_gb", return_value=8.0),
        patch("autoship.core.hardware_profiler._has_gpu", return_value=False),
    ):
        profile = detect_hardware()
    assert profile.recommended_tier == 2


def test_detect_hardware_recommends_tier_1() -> None:
    with (
        patch("autoship.core.hardware_profiler._cpu_count", return_value=2),
        patch("autoship.core.hardware_profiler._memory_gb", return_value=4.0),
        patch("autoship.core.hardware_profiler._has_gpu", return_value=False),
    ):
        profile = detect_hardware()
    assert profile.recommended_tier == 1


def test_hardware_profile_fields() -> None:
    profile = HardwareProfile(cpu_cores=4, memory_gb=16.0, has_gpu=False, recommended_tier=2)
    assert profile.cpu_cores == 4
    assert profile.memory_gb == 16.0
    assert profile.has_gpu is False


def test_memory_gb_fallback_from_proc(tmp_path, monkeypatch) -> None:
    from autoship.core.hardware_profiler import _memory_gb

    monkeypatch.setitem(sys.modules, "psutil", None)
    meminfo = tmp_path / "meminfo"
    meminfo.write_text("MemTotal:       16384000 kB\n")

    def _open(*args, **kwargs):
        return meminfo.open()

    with patch("builtins.open", _open):
        assert abs(_memory_gb() - 15.625) < 0.01


def test_memory_gb_assumes_default_on_failure(monkeypatch) -> None:
    from autoship.core.hardware_profiler import _memory_gb

    monkeypatch.setitem(sys.modules, "psutil", None)
    with patch("builtins.open", side_effect=OSError("no /proc")):
        assert _memory_gb() == 8.0


def test_has_gpu_detects_nvidia_smi() -> None:
    from autoship.core.hardware_profiler import _has_gpu

    with patch("shutil.which", return_value="/usr/bin/nvidia-smi"):
        assert _has_gpu() is True


def test_has_gpu_no_torch() -> None:
    from autoship.core.hardware_profiler import _has_gpu

    with patch("shutil.which", return_value=None), patch.dict("sys.modules", {"torch": None}):
        assert _has_gpu() is False
