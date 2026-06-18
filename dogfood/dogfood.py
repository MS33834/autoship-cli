"""Dogfood AutoShip-CLI against representative project types.

Run with:
    uv run python dogfood/dogfood.py

Produces ``dogfood/report.md``.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
AUTOSHIP = [sys.executable, "-m", "autoship"]


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def run(
    cmd: list[str], cwd: Path, check: bool = False, timeout: int = 60
) -> subprocess.CompletedProcess:
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
        stdout = exc.stdout.decode("utf-8") if isinstance(exc.stdout, bytes) else exc.stdout or ""
        stderr = exc.stderr.decode("utf-8") if isinstance(exc.stderr, bytes) else exc.stderr or ""
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=124,
            stdout=stdout,
            stderr=stderr + "\n[dogfood timeout]",
        )


def setup_git(project_root: Path) -> None:
    run(["git", "init"], project_root, check=True)
    run(["git", "config", "user.email", "dogfood@example.com"], project_root, check=True)
    run(["git", "config", "user.name", "Dogfood"], project_root, check=True)


def write_config(project_root: Path) -> None:
    """Write a minimal config with a fast-failing fake model backend."""
    config = """schema_version = 1
log_level = "WARNING"

[model]
default_tier = 1
fallback = false

[[model.backends]]
provider = "ollama"
base_url = "http://localhost:59999"
model = "fake"
timeout = 2.0
concurrency = 1
priority = 0
"""
    (project_root / ".autoship.toml").write_text(config, encoding="utf-8")


def scenario_simple_script() -> dict:
    """A tiny single-file Python project."""
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)
        (project_root / "hello.py").write_text("import os\n\ndef hello():\n    return 'world'\n")
        setup_git(project_root)
        write_config(project_root)

        init = run(AUTOSHIP + ["--yes", "init"], project_root)
        clean = run(AUTOSHIP + ["--yes", "clean"], project_root)
        plugin_list = run(AUTOSHIP + ["plugin", "list"], project_root)
        commit = run(AUTOSHIP + ["--yes", "commit"], project_root, timeout=30)
        verify = run(AUTOSHIP + ["verify", "echo ok"], project_root, timeout=30)

        return {
            "name": "simple_script",
            "description": "单文件 Python 脚本",
            "results": {
                "init": {"rc": init.returncode, "stderr": init.stderr[:500]},
                "clean": {"rc": clean.returncode, "stderr": clean.stderr[:500]},
                "plugin_list": {"rc": plugin_list.returncode, "stderr": plugin_list.stderr[:500]},
                "commit": {"rc": commit.returncode, "stderr": commit.stderr[:500]},
                "verify": {"rc": verify.returncode, "stderr": verify.stderr[:500]},
            },
        }


def scenario_flask_app() -> dict:
    """A small Flask web project."""
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)
        (project_root / "app.py").write_text(
            "from flask import Flask\n\napp = Flask(__name__)\n\n@app.route('/')\ndef index():\n    return 'ok'\n"
        )
        (project_root / "requirements.txt").write_text("flask\n")
        setup_git(project_root)
        write_config(project_root)

        init = run(AUTOSHIP + ["--yes", "init"], project_root)
        clean = run(AUTOSHIP + ["--yes", "clean"], project_root)
        plugin_list = run(AUTOSHIP + ["plugin", "list"], project_root)

        return {
            "name": "flask_app",
            "description": "Flask Web 项目",
            "results": {
                "init": {"rc": init.returncode, "stderr": init.stderr[:500]},
                "clean": {"rc": clean.returncode, "stderr": clean.stderr[:500]},
                "plugin_list": {"rc": plugin_list.returncode, "stderr": plugin_list.stderr[:500]},
            },
        }


def scenario_data_science() -> dict:
    """A project importing heavier scientific libraries."""
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)
        (project_root / "analysis.py").write_text(
            "import json\n\nimport numpy as np\n\ndef summary(data):\n    return {'mean': float(np.mean(data))}\n"
        )
        (project_root / "requirements.txt").write_text("numpy\n")
        setup_git(project_root)
        write_config(project_root)

        init = run(AUTOSHIP + ["--yes", "init"], project_root)
        clean = run(AUTOSHIP + ["--yes", "clean"], project_root)

        return {
            "name": "data_science",
            "description": "数据科学项目（numpy）",
            "results": {
                "init": {"rc": init.returncode, "stderr": init.stderr[:500]},
                "clean": {"rc": clean.returncode, "stderr": clean.stderr[:500]},
            },
        }


def scenario_monorepo() -> dict:
    """A simple monorepo with two packages."""
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)
        pkg_a = project_root / "packages" / "pkg_a"
        pkg_b = project_root / "packages" / "pkg_b"
        pkg_a.mkdir(parents=True)
        pkg_b.mkdir(parents=True)
        (pkg_a / "__init__.py").write_text("def a():\n    return 1\n")
        (pkg_b / "__init__.py").write_text("from pkg_a import a\n\ndef b():\n    return a() + 1\n")
        setup_git(project_root)
        write_config(project_root)

        init = run(AUTOSHIP + ["--yes", "init"], project_root)
        clean = run(AUTOSHIP + ["--yes", "clean"], project_root)

        return {
            "name": "monorepo",
            "description": "Monorepo 多包项目",
            "results": {
                "init": {"rc": init.returncode, "stderr": init.stderr[:500]},
                "clean": {"rc": clean.returncode, "stderr": clean.stderr[:500]},
            },
        }


def run_all() -> list[dict]:
    return [
        scenario_simple_script(),
        scenario_flask_app(),
        scenario_data_science(),
        scenario_monorepo(),
    ]


def render_report(scenarios: list[dict]) -> str:
    lines = [
        "# AutoShip-CLI Dogfooding Report",
        "",
        f"Python: {sys.version.split()[0]}",
        "",
        "## Scenarios",
        "",
    ]
    issues: list[str] = []
    for scenario in scenarios:
        lines.append(f"### {scenario['name']} ({scenario['description']})")
        lines.append("")
        lines.append("| Command | Exit Code | Notes |")
        lines.append("|---------|-----------|-------|")
        for cmd, result in scenario["results"].items():
            rc = result["rc"]
            note = "OK" if rc == 0 else f"rc={rc}"
            stderr = result["stderr"].strip()
            if stderr:
                note += f"<br><small>{stderr[:120]}</small>"
            if rc != 0 and cmd != "commit" and cmd != "verify":
                issues.append(f"- `{scenario['name']}.{cmd}` failed with rc={rc}: {stderr[:120]}")
            lines.append(f"| `{cmd}` | {rc} | {note} |")
        lines.append("")

    lines.append("## Known Limitations / Issues Found")
    lines.append("")
    if issues:
        lines.extend(issues)
    else:
        lines.append("- No unexpected failures in non-AI commands.")
    lines.append(
        "- `commit` and `verify` require a configured model backend; failures without one are expected."
    )
    lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    lines.append(
        "- Continue dogfooding with a running local model (Ollama/LM Studio) for `commit`/`verify` paths."
    )
    lines.append(
        "- Consider adding `autoship doctor` command to diagnose missing model/toolchain dependencies."
    )
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    scenarios = run_all()
    report = render_report(scenarios)
    report_path = REPO_ROOT / "dogfood" / "report.md"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
