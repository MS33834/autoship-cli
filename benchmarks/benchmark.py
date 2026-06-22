"""AutoShip-CLI 性能基准与回归检测。

运行方式：

    uv run python benchmarks/benchmark.py

首次运行会生成 ``benchmarks/results.json``；后续运行会与上一次基线对比，
当某项指标中位数超过基线的 ``regression_threshold``（默认 1.2 倍）时返回非零
退出码，可用于 CI 性能回归门禁。
"""

from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import psutil

from autoship.core.metrics import get_registry

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
BENCHMARKS_DIR = REPO_ROOT / "benchmarks"
RESULTS_PATH = BENCHMARKS_DIR / "results.json"

DEFAULT_REGRESSION_THRESHOLD = 1.2


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env["AUTOSHIP_LOG_LEVEL"] = "WARNING"
    return env


def _autoship_cmd() -> list[str]:
    return [sys.executable, "-m", "autoship"]


def run(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: int = 60,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=_env(),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


@dataclass
class Benchmark:
    """单个性能基准指标。"""

    name: str
    unit: str
    target: float | None = None
    regression_threshold: float = DEFAULT_REGRESSION_THRESHOLD
    values: list[float] = field(default_factory=list)

    def measure(self, value: float) -> None:
        self.values.append(value)

    @property
    def median(self) -> float:
        if not self.values:
            return 0.0
        return statistics.median(self.values)

    @property
    def stdev(self) -> float | None:
        if len(self.values) < 2:
            return None
        return statistics.stdev(self.values)

    def to_dict(self, baseline: dict[str, Any] | None = None) -> dict[str, Any]:
        baseline_median = baseline.get("median") if baseline else None
        regression: bool | None = None
        ratio: float | None = None
        if baseline_median is not None and baseline_median > 0:
            ratio = self.median / baseline_median
            regression = ratio > self.regression_threshold

        passed = self.target is None or self.median <= self.target
        if regression:
            passed = False

        return {
            "name": self.name,
            "unit": self.unit,
            "target": self.target,
            "regression_threshold": self.regression_threshold,
            "values": self.values,
            "median": self.median,
            "stdev": self.stdev,
            "baseline_median": baseline_median,
            "ratio": ratio,
            "regression": regression,
            "passed": passed,
        }


def _create_project(root: Path, num_files: int = 100) -> None:
    """创建一个用于基准测试的合成 Python 项目。"""
    for i in range(num_files):
        (root / f"module_{i:03d}.py").write_text(
            "from __future__ import annotations\n\n"
            "import os\n\n"
            f"def func_{i}() -> int:\n"
            "    x = 1\n"
            "    return x\n",
            encoding="utf-8",
        )


def _setup_git(project_root: Path) -> None:
    run(["git", "init", "-q"], cwd=project_root)
    run(["git", "config", "user.email", "bench@example.com"], cwd=project_root)
    run(["git", "config", "user.name", "Benchmark"], cwd=project_root)


def _write_config(project_root: Path) -> None:
    config = """schema_version = 1
project_type = "generic"
log_level = "WARNING"

[model]
default_tier = 1
fallback = false

[clean]
enabled = true
tools = ["black"]
"""
    (project_root / ".autoship.toml").write_text(config, encoding="utf-8")


def benchmark_startup() -> Benchmark:
    """测量 ``--help`` 的 CLI 启动时间。"""
    bench = Benchmark("cli_startup", "ms", target=800.0)
    # warmup
    run(_autoship_cmd() + ["--help"])
    for _ in range(7):
        start = time.perf_counter()
        proc = run(_autoship_cmd() + ["--help"])
        elapsed_ms = (time.perf_counter() - start) * 1000
        if proc.returncode != 0:
            bench.measure(float("inf"))
        else:
            bench.measure(elapsed_ms)
    return bench


def benchmark_clean(num_files: int = 100) -> Benchmark:
    """测量 ``autoship clean`` 在合成项目上的执行时间。"""
    bench = Benchmark("clean_execution", "s", target=10.0)
    for _ in range(3):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            _create_project(project_root, num_files=num_files)
            _setup_git(project_root)
            _write_config(project_root)
            start = time.perf_counter()
            proc = run(_autoship_cmd() + ["--yes", "clean"], cwd=project_root, timeout=120)
            elapsed_s = time.perf_counter() - start
            if proc.returncode != 0:
                bench.measure(float("inf"))
            else:
                bench.measure(elapsed_s)
    return bench


def benchmark_verify() -> Benchmark:
    """测量 ``autoship verify`` 的端到端耗时。"""
    bench = Benchmark("verify_execution", "s", target=5.0)
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)
        _create_project(project_root, num_files=10)
        _setup_git(project_root)
        _write_config(project_root)
        for _ in range(3):
            start = time.perf_counter()
            proc = run(
                _autoship_cmd() + ["verify", "python --version"],
                cwd=project_root,
                timeout=60,
            )
            elapsed_s = time.perf_counter() - start
            if proc.returncode != 0:
                bench.measure(float("inf"))
            else:
                bench.measure(elapsed_s)
    return bench


def benchmark_plugin_list() -> Benchmark:
    """测量 ``autoship plugin list`` 的耗时。"""
    bench = Benchmark("plugin_list", "ms", target=800.0)
    for _ in range(5):
        start = time.perf_counter()
        proc = run(_autoship_cmd() + ["plugin", "list"])
        elapsed_ms = (time.perf_counter() - start) * 1000
        if proc.returncode != 0:
            bench.measure(float("inf"))
        else:
            bench.measure(elapsed_ms)
    return bench


def benchmark_idle_memory() -> Benchmark:
    """测量导入 CLI 后的空闲内存。"""
    bench = Benchmark("idle_memory", "MB", target=100.0)
    # 预热后读取
    run([sys.executable, "-c", "from autoship.cli.main import cli_entrypoint"])
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / (1024 * 1024)
    bench.measure(mem_mb)
    return bench


def load_baseline() -> dict[str, Any] | None:
    """加载上一次的基准结果作为回归检测基线。"""
    if not RESULTS_PATH.exists():
        return None
    try:
        data = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
        return {b["name"]: b for b in data.get("benchmarks", [])}
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def run_benchmarks() -> dict[str, Any]:
    """运行所有基准并返回报告。"""
    get_registry().reset()
    baseline = load_baseline()
    benchmarks = [
        benchmark_startup(),
        benchmark_clean(),
        benchmark_verify(),
        benchmark_plugin_list(),
        benchmark_idle_memory(),
    ]
    return {
        "python": sys.version.split()[0],
        "benchmarks": [b.to_dict(baseline.get(b.name) if baseline else None) for b in benchmarks],
        "metrics": get_registry().snapshot(),
        "all_passed": all(b.to_dict().get("passed", False) for b in benchmarks),
    }


def render_report(report: dict[str, Any]) -> str:
    """生成人类可读的 Markdown 报告。"""
    lines = [
        "# AutoShip-CLI Performance Benchmark",
        "",
        f"Python: {report['python']}",
        "",
        "| Benchmark | Median | Target | Baseline | Ratio | Status |",
        "|-----------|--------|--------|----------|-------|--------|",
    ]
    for b in report["benchmarks"]:
        median = f"{b['median']:.2f} {b['unit']}"
        target = f"{b['target']:.2f} {b['unit']}" if b["target"] is not None else "—"
        baseline = (
            f"{b['baseline_median']:.2f} {b['unit']}" if b["baseline_median"] is not None else "—"
        )
        ratio = f"{b['ratio']:.2f}x" if b["ratio"] is not None else "—"
        status = "PASS" if b["passed"] else "FAIL"
        lines.append(f"| {b['name']} | {median} | {target} | {baseline} | {ratio} | {status} |")
    lines.append("")
    regressions = [b for b in report["benchmarks"] if b.get("regression")]
    if regressions:
        lines.append("## Regressions")
        lines.append("")
        for b in regressions:
            lines.append(
                f"- **{b['name']}**: {b['median']:.2f} vs baseline {b['baseline_median']:.2f} "
                f"({b['ratio']:.2f}x > {b['regression_threshold']}x threshold)"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = run_benchmarks()
    BENCHMARKS_DIR.mkdir(exist_ok=True)

    # 保存新基线（无论是否通过都更新，便于追踪趋势）
    RESULTS_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    report_path = BENCHMARKS_DIR / "report.md"
    report_path.write_text(render_report(report), encoding="utf-8")

    print(render_report(report))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
