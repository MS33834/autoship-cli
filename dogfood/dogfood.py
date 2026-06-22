"""AutoShip-CLI 冒烟测试套件。

该脚本在多种典型项目结构上运行 AutoShip 核心命令，验证 CLI 在真实项目上的
基本可用性。可直接用于 CI：

    uv run python dogfood/dogfood.py

返回非零退出码表示存在非预期的命令失败。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
AUTOSHIP = [sys.executable, "-m", "autoship"]

CI = os.environ.get("CI", "false").lower() == "true"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    # 避免 CI 环境中模型后端相关命令因超时而失败
    env["AUTOSHIP_LOG_LEVEL"] = "WARNING"
    return env


def run(
    cmd: list[str],
    cwd: Path,
    check: bool = False,
    timeout: int = 60,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            env=_env(),
            check=check,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + "\n[dogfood timeout]"
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=124,
            stdout=stdout,
            stderr=stderr,
        )


def setup_git(project_root: Path) -> None:
    run(["git", "init", "-q"], project_root, check=True)
    run(["git", "config", "user.email", "dogfood@example.com"], project_root, check=True)
    run(["git", "config", "user.name", "Dogfood"], project_root, check=True)


def write_config(project_root: Path, project_type: str = "generic") -> None:
    """写入一个轻量配置，避免依赖真实模型后端。"""
    config = f"""schema_version = 1
project_type = "{project_type}"
log_level = "WARNING"

[model]
default_tier = 1
fallback = false

[clean]
enabled = true
tools = ["black"]

[commit]
enabled = false
"""
    (project_root / ".autoship.toml").write_text(config, encoding="utf-8")


@dataclass
class Step:
    name: str
    rc: int
    stdout: str
    stderr: str
    expected: Literal["success", "fail", "skip"]

    @property
    def passed(self) -> bool:
        if self.expected == "success":
            return self.rc == 0
        if self.expected == "fail":
            return self.rc != 0
        return True


@dataclass
class Scenario:
    name: str
    description: str
    steps: list[Step] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(step.passed for step in self.steps)


def _record(result: subprocess.CompletedProcess[str], expected: Literal["success", "fail", "skip"]) -> Step:
    return Step(
        name=" ".join(result.args),
        rc=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        expected=expected,
    )


def _run_common_steps(project_root: Path) -> list[Step]:
    steps: list[Step] = []

    init = run(AUTOSHIP + ["init", "--yes"], project_root, timeout=30)
    steps.append(_record(init, "success"))

    clean = run(AUTOSHIP + ["--yes", "clean"], project_root, timeout=60)
    steps.append(_record(clean, "success"))

    plugin_list = run(AUTOSHIP + ["plugin", "list"], project_root, timeout=30)
    steps.append(_record(plugin_list, "success"))

    doctor = run(AUTOSHIP + ["doctor", "--json"], project_root, timeout=30)
    steps.append(_record(doctor, "success"))

    verify = run(AUTOSHIP + ["verify", "python --version"], project_root, timeout=30)
    steps.append(_record(verify, "success"))

    upload = run(
        AUTOSHIP + ["--dry-run", "--yes", "upload", "--target", "pypi"],
        project_root,
        timeout=30,
    )
    steps.append(_record(upload, "success"))

    return steps


def scenario_simple_script() -> Scenario:
    """单个 Python 脚本项目。"""
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)
        (project_root / "hello.py").write_text(
            "import os\n\ndef hello():\n    return 'world'\n",
            encoding="utf-8",
        )
        setup_git(project_root)

        return Scenario(
            name="simple_script",
            description="单文件 Python 脚本",
            steps=_run_common_steps(project_root),
        )


def scenario_flask_app() -> Scenario:
    """Flask Web 项目。"""
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)
        (project_root / "app.py").write_text(
            "from flask import Flask\n\napp = Flask(__name__)\n\n"
            "@app.route('/')\ndef index():\n    return 'ok'\n",
            encoding="utf-8",
        )
        (project_root / "requirements.txt").write_text("flask\n", encoding="utf-8")
        setup_git(project_root)

        return Scenario(
            name="flask_app",
            description="Flask Web 项目",
            steps=_run_common_steps(project_root),
        )


def scenario_data_science() -> Scenario:
    """数据科学项目。"""
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)
        (project_root / "analysis.py").write_text(
            "import json\n\nimport numpy as np\n\n"
            "def summary(data):\n    return {'mean': float(np.mean(data))}\n",
            encoding="utf-8",
        )
        (project_root / "requirements.txt").write_text("numpy\n", encoding="utf-8")
        setup_git(project_root)

        return Scenario(
            name="data_science",
            description="数据科学项目（numpy）",
            steps=_run_common_steps(project_root),
        )


def scenario_monorepo() -> Scenario:
    """简单多包 Monorepo。"""
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)
        pkg_a = project_root / "packages" / "pkg_a"
        pkg_b = project_root / "packages" / "pkg_b"
        pkg_a.mkdir(parents=True)
        pkg_b.mkdir(parents=True)
        (pkg_a / "__init__.py").write_text("def a():\n    return 1\n", encoding="utf-8")
        (pkg_b / "__init__.py").write_text(
            "from pkg_a import a\n\ndef b():\n    return a() + 1\n",
            encoding="utf-8",
        )
        setup_git(project_root)

        return Scenario(
            name="monorepo",
            description="Monorepo 多包项目",
            steps=_run_common_steps(project_root),
        )


def run_all() -> list[Scenario]:
    return [
        scenario_simple_script(),
        scenario_flask_app(),
        scenario_data_science(),
        scenario_monorepo(),
    ]


def render_report(scenarios: list[Scenario]) -> str:
    lines = [
        "# AutoShip-CLI Dogfooding Report",
        "",
        f"Python: {sys.version.split()[0]}",
        f"CI: {CI}",
        "",
        "## Scenarios",
        "",
    ]

    failed_steps: list[str] = []
    for scenario in scenarios:
        status = "PASS" if scenario.passed else "FAIL"
        lines.append(f"### {scenario.name} ({scenario.description}) — {status}")
        lines.append("")
        lines.append("| Command | Exit Code | Expected | Result |")
        lines.append("|---------|-----------|----------|--------|")
        for step in scenario.steps:
            result = "PASS" if step.passed else "FAIL"
            cmd_display = step.name.replace("|", "\\|")
            lines.append(
                f"| `{cmd_display}` | {step.rc} | {step.expected} | {result} |"
            )
            if not step.passed:
                failed_steps.append(f"- `{scenario.name}` → `{step.name}` (rc={step.rc})")
                if step.stderr:
                    snippet = step.stderr.strip().replace("\n", " ")[:120]
                    failed_steps[-1] += f"\n  <small>{snippet}</small>"
        lines.append("")

    lines.append("## Summary")
    lines.append("")
    total = sum(len(s.steps) for s in scenarios)
    passed = sum(1 for s in scenarios for step in s.steps if step.passed)
    lines.append(f"- Steps passed: {passed} / {total}")
    lines.append(f"- Scenarios passed: {sum(1 for s in scenarios if s.passed)} / {len(scenarios)}")
    lines.append("")

    lines.append("## Failures")
    lines.append("")
    if failed_steps:
        lines.extend(failed_steps)
    else:
        lines.append("No unexpected failures.")
    lines.append("")

    return "\n".join(lines)


def write_json_report(scenarios: list[Scenario], path: Path) -> None:
    payload = {
        "python": sys.version.split()[0],
        "ci": CI,
        "scenarios": [
            {
                "name": s.name,
                "description": s.description,
                "passed": s.passed,
                "steps": [
                    {
                        "command": step.name,
                        "rc": step.rc,
                        "expected": step.expected,
                        "passed": step.passed,
                        "stderr": step.stderr[:500] if step.stderr else "",
                    }
                    for step in s.steps
                ],
            }
            for s in scenarios
        ],
        "all_passed": all(s.passed for s in scenarios),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    scenarios = run_all()
    report = render_report(scenarios)

    report_path = REPO_ROOT / "dogfood" / "report.md"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    json_path = REPO_ROOT / "dogfood" / "report.json"
    write_json_report(scenarios, json_path)

    print(report)
    return 0 if all(s.passed for s in scenarios) else 1


if __name__ == "__main__":
    raise SystemExit(main())
