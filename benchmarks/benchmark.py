"""Performance benchmark script for AutoShip-CLI.

Run with:
    uv run python benchmarks/benchmark.py

Outputs a JSON report to ``benchmarks/results.json``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import psutil

from autoship.core.metrics import get_registry

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
BENCHMARKS_DIR = REPO_ROOT / "benchmarks"


class Benchmark:
    """A single benchmark measurement."""

    def __init__(self, name: str, unit: str, target: float | None = None) -> None:
        self.name = name
        self.unit = unit
        self.target = target
        self.values: list[float] = []

    def measure(self, value: float) -> None:
        self.values.append(value)

    @property
    def median(self) -> float:
        if not self.values:
            return 0.0
        sorted_values = sorted(self.values)
        n = len(sorted_values)
        if n % 2 == 1:
            return sorted_values[n // 2]
        return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "unit": self.unit,
            "target": self.target,
            "values": self.values,
            "median": self.median,
            "passed": self.target is None or self.median <= self.target,
        }


def _autoship_cmd() -> list[str]:
    """Return the command to invoke autoship via the installed package."""
    return [sys.executable, "-m", "autoship"]


def _env() -> dict[str, str]:
    """Return an environment with the project on PYTHONPATH."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _create_project(root: Path, num_files: int = 100) -> None:
    """Create a sample Python project for benchmarking."""
    for i in range(num_files):
        (root / f"module_{i:03d}.py").write_text(
            "from __future__ import annotations\n\n"
            "import os\n\n"
            f"def func_{i}() -> int:\n"
            "    x = 1\n"
            "    return x\n",
            encoding="utf-8",
        )


def benchmark_startup() -> Benchmark:
    """Measure CLI startup time for ``--help``."""
    bench = Benchmark("cli_startup", "ms", target=500.0)
    for _ in range(5):
        start = time.perf_counter()
        subprocess.run(_autoship_cmd() + ["--help"], env=_env(), check=True, capture_output=True)
        elapsed_ms = (time.perf_counter() - start) * 1000
        bench.measure(elapsed_ms)
    return bench


def benchmark_clean(num_files: int = 100) -> Benchmark:
    """Measure ``autoship clean`` execution time on a synthetic project."""
    bench = Benchmark("clean_execution", "s", target=5.0)
    for _ in range(3):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            _create_project(project_root, num_files=num_files)
            subprocess.run(["git", "init"], cwd=project_root, check=True, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "bench@example.com"],
                cwd=project_root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Benchmark"],
                cwd=project_root,
                check=True,
                capture_output=True,
            )
            start = time.perf_counter()
            subprocess.run(
                _autoship_cmd() + ["--yes", "clean"],
                cwd=project_root,
                env=_env(),
                check=True,
                capture_output=True,
            )
            elapsed_s = time.perf_counter() - start
            bench.measure(elapsed_s)
    return bench


def benchmark_idle_memory() -> Benchmark:
    """Measure idle memory after importing the CLI."""
    bench = Benchmark("idle_memory", "MB", target=80.0)
    process = psutil.Process(os.getpid())
    # Warm import to get a stable reading.
    subprocess.run(
        [sys.executable, "-c", "from autoship.cli.main import cli_entrypoint"],
        cwd=REPO_ROOT,
        env=_env(),
        check=True,
        capture_output=True,
    )
    mem_mb = process.memory_info().rss / (1024 * 1024)
    bench.measure(mem_mb)
    return bench


def run_benchmarks() -> dict:
    """Run all benchmarks and return a report."""
    get_registry().reset()
    benchmarks = [
        benchmark_startup(),
        benchmark_clean(),
        benchmark_idle_memory(),
    ]
    return {
        "benchmarks": [b.to_dict() for b in benchmarks],
        "metrics": get_registry().snapshot(),
        "all_passed": all(b.to_dict()["passed"] for b in benchmarks),
    }


def main() -> int:
    report = run_benchmarks()
    BENCHMARKS_DIR.mkdir(exist_ok=True)
    results_path = BENCHMARKS_DIR / "results.json"
    results_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
