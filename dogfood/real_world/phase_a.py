"""Phase A — end-to-end scenario tests with four realistic personas."""

from __future__ import annotations

import tempfile
from pathlib import Path

from dogfood.real_world.runner import (
    Scenario,
    Step,
    ensure_clean_tools,
    install_local_plugin,
    run_autoship,
    setup_git,
    uninstall_plugin,
)


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _scenario_fullstack_junior() -> Scenario:
    """A junior full-stack developer ships a FastAPI + frontend monorepo."""
    scenario = Scenario(
        name="fullstack_junior",
        description="FastAPI backend + vanilla frontend monorepo with formatting issues and a failing test.",
        persona="Junior full-stack developer",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ensure_clean_tools()

        _write_file(
            root / "pyproject.toml",
            """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "myapp"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "fastapi",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
""",
        )
        _write_file(
            root / "src/myapp/__init__.py",
            "",
        )
        _write_file(
            root / "src/myapp/main.py",
            """import os
import sys
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    x=1+2
    return {"msg": "hello", "value": x}

@app.get("/users/{user_id}")
def read_user(user_id: int):
    if user_id < 0:
        return {"error": "bad id"}
    return {"user_id": user_id + 1}
""",
        )
        _write_file(
            root / "tests/__init__.py",
            "",
        )
        _write_file(
            root / "tests/test_main.py",
            """from myapp.main import read_user

def test_read_user_positive():
    assert read_user(1) == {"user_id": 2}

def test_read_user_negative():
    # intentionally failing: the implementation adds 1 to negative ids too
    assert read_user(-5) == {"error": "bad id"}
""",
        )
        _write_file(
            root / "frontend/index.html",
            "<!doctype html><html><body><h1>MyApp</h1></body></html>",
        )
        setup_git(root)

        scenario.steps.extend(
            [
                run_autoship(["init", "--yes"], cwd=root),
                run_autoship(["--yes", "clean"], cwd=root),
                run_autoship(["verify", "pytest"], cwd=root, expected="fail"),
                run_autoship(["--yes", "fix"], cwd=root, expected="fail"),
                run_autoship(["--yes", "commit", "-m", "fix: repair user endpoint"], cwd=root),
                run_autoship(
                    ["--yes", "--dry-run", "upload", "--target", "pypi"],
                    cwd=root,
                ),
            ]
        )
    return scenario


def _scenario_devops_engineer() -> Scenario:
    """A DevOps engineer ships a Python CLI as a Docker image."""
    scenario = Scenario(
        name="devops_engineer",
        description="Python CLI tool with Dockerfile, entrypoint script, and GitHub Actions workflow.",
        persona="DevOps engineer",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_file(
            root / "pyproject.toml",
            """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "deploycli"
version = "0.2.0"
requires-python = ">=3.10"
dependencies = []

[project.scripts]
deploy = "deploycli.cli:main"
""",
        )
        _write_file(
            root / "src/deploycli/__init__.py",
            "__version__ = '0.2.0'\n",
        )
        _write_file(
            root / "src/deploycli/cli.py",
            """import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="store_true")
    args = parser.parse_args()
    if args.version:
        print("0.2.0")

if __name__ == "__main__":
    main()
""",
        )
        _write_file(
            root / "Dockerfile",
            'FROM python:3.12-slim\nWORKDIR /app\nCOPY . .\nRUN pip install .\nENTRYPOINT ["deploy"]\n',
        )
        _write_file(
            root / ".github/workflows/ci.yml",
            """name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python -m pip install .
      - run: deploy --version
""",
        )
        setup_git(root)

        scenario.steps.extend(
            [
                run_autoship(["init", "--yes"], cwd=root),
                run_autoship(["doctor", "--json"], cwd=root),
                run_autoship(["verify", "python --version"], cwd=root),
                run_autoship(
                    [
                        "--yes",
                        "--dry-run",
                        "upload",
                        "--target",
                        "docker",
                        "--image",
                        "deploycli",
                        "--tag",
                        "v0.2.0",
                    ],
                    cwd=root,
                ),
                run_autoship(
                    ["plugin", "info", "security-scan"], cwd=root, expected="success", timeout=60
                ),
            ]
        )
    return scenario


def _scenario_plugin_author() -> Scenario:
    """An open-source plugin author uses autoship-sdk to build a new plugin."""
    scenario = Scenario(
        name="plugin_author",
        description="Create a plugin package with autoship-sdk, test it, install it, and dry-run upload.",
        persona="Open-source plugin author",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plugin_pkg = root / "src" / "autoship_hello_plugin"
        _write_file(
            root / "pyproject.toml",
            """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "autoship-hello-plugin"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "autoship>=1.0.0",
    "autoship-sdk>=1.0.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[project.entry-points."autoship.plugins"]
hello = "autoship_hello_plugin.plugin:register"
""",
        )
        _write_file(
            plugin_pkg / "__init__.py",
            "",
        )
        _write_file(
            plugin_pkg / "plugin.py",
            """from __future__ import annotations

from autoship_sdk import Plugin, hook
from autoship.core.context import CommandContext


class HelloPlugin(Plugin):
    @hook
    def pre_commit(self, context: CommandContext) -> None:
        print("[hello-plugin] pre_commit hook fired")

    @hook
    def post_verify(self, context: CommandContext) -> None:
        print("[hello-plugin] post_verify hook fired")


def register() -> HelloPlugin:
    return HelloPlugin()
""",
        )
        _write_file(
            root / "tests" / "test_plugin.py",
            """from autoship_hello_plugin.plugin import HelloPlugin
from autoship_sdk.testing import PluginTestHarness


def test_plugin_hooks():
    plugin = HelloPlugin()
    harness = PluginTestHarness()
    harness.register(plugin)
    ctx = harness.make_context("commit")
    harness.call("pre_commit", ctx)
    assert ctx.extras.get("ran") is None  # hook prints only
""",
        )
        setup_git(root)

        scenario.steps.extend(
            [
                run_autoship(["init", "--yes"], cwd=root),
                run_autoship(["verify", "pytest"], cwd=root),
                install_local_plugin(root, "autoship-hello-plugin"),
                run_autoship(["plugin", "list"], cwd=root),
                run_autoship(["plugin", "trust", "autoship-hello-plugin", "community"], cwd=root),
                run_autoship(["--yes", "commit", "-m", "feat: add hello plugin"], cwd=root),
                run_autoship(
                    ["--yes", "--dry-run", "upload", "--target", "pypi"],
                    cwd=root,
                ),
                uninstall_plugin("autoship-hello-plugin"),
            ]
        )
    return scenario


def _scenario_security_enterprise() -> Scenario:
    """A security-sensitive enterprise developer audits a repo that contains secrets."""
    scenario = Scenario(
        name="security_enterprise",
        description="Repository with a fake API key in source; verify redaction in config output and audit logs.",
        persona="Security-sensitive enterprise developer",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_file(
            root / "pyproject.toml",
            """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "paymentservice"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = []

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
""",
        )
        _write_file(
            root / "src/paymentservice/__init__.py",
            "",
        )
        _write_file(
            root / "src/paymentservice/client.py",
            """import os

API_KEY = os.getenv("PAYMENT_API_KEY", "fake-default-key")


def charge(amount: float) -> dict[str, str]:
    return {"status": "ok", "amount": str(amount)}
""",
        )
        _write_file(
            root / "tests/test_client.py",
            """from paymentservice.client import charge

def test_charge():
    assert charge(10.0)["status"] == "ok"
""",
        )
        setup_git(root)

        extra_env = {"AUTOSHIP_LLM__API_KEY": "sk-live-abc123-secret"}
        config_step = run_autoship(["config", "list", "--json"], cwd=root, extra_env=extra_env)
        redacted = "sk-live-abc123-secret" not in config_step.stdout + config_step.stderr
        config_step.expected = "success"

        audit_step = run_autoship(["audit", "export"], cwd=root)
        audit_redacted = "sk-live-abc123-secret" not in audit_step.stdout + audit_step.stderr

        scenario.steps.extend(
            [
                run_autoship(["init", "--yes"], cwd=root),
                config_step,
                run_autoship(["verify", "pytest"], cwd=root),
                audit_step,
                Step(
                    name="assert config redaction",
                    rc=0 if redacted else 1,
                    stdout="" if redacted else "sensitive value leaked in config output",
                    stderr="",
                    expected="success",
                ),
                Step(
                    name="assert audit redaction",
                    rc=0 if audit_redacted else 1,
                    stdout="" if audit_redacted else "sensitive value leaked in audit output",
                    stderr="",
                    expected="success",
                ),
            ]
        )
    return scenario


def run_all() -> list[Scenario]:
    """Run all Phase A scenarios."""
    return [
        _scenario_fullstack_junior(),
        _scenario_devops_engineer(),
        _scenario_plugin_author(),
        _scenario_security_enterprise(),
    ]


if __name__ == "__main__":
    scenarios = run_all()
    for scenario in scenarios:
        print(f"{scenario.name}: {'PASS' if scenario.passed else 'FAIL'}")
