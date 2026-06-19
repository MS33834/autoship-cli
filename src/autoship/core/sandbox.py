"""Sandbox execution helpers for untrusted/community plugins.

This module provides a ``SandboxRunner`` that executes a command inside a
restricted subprocess environment. It is a first-phase implementation: it
limits the environment and working directory, and optionally blocks network
access when ``unshare`` or ``firejail`` is available.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autoship.exceptions import SandboxError

logger = logging.getLogger("autoship")


def _decode_stream(value: str | bytes | None) -> str | None:
    """Normalize subprocess output to a string."""
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


@dataclass
class SandboxResult:
    """Result of a sandboxed execution."""

    returncode: int
    stdout: str
    stderr: str


class SandboxRunner:
    """Run a command in a restricted subprocess environment.

    Restrictions applied:

    - A fresh temporary working directory is used by default.
    - Only whitelisted environment variables are inherited.
    - If ``network`` is ``False`` and a supported network namespace tool is
      available, the command is wrapped to block network access.

    The runner degrades gracefully when sandbox tooling is unavailable unless
    ``required`` is ``True``: it still applies the environment and directory
    restrictions and logs a warning that network isolation could not be
    enforced. When ``required`` is ``True`` and no isolation tool is available,
    a ``SandboxError`` is raised instead of degrading.
    """

    def __init__(
        self,
        *,
        network: bool = False,
        env_whitelist: list[str] | None = None,
        working_dir: Path | None = None,
        required: bool = False,
    ) -> None:
        self.network = network
        self.env_whitelist = env_whitelist or ["PATH", "HOME", "USER", "LANG", "LC_ALL"]
        self.working_dir = working_dir
        self.required = required

    def run(
        self,
        command: list[str],
        *,
        input_text: str | None = None,
        timeout: float | None = None,
    ) -> SandboxResult:
        """Run ``command`` inside the sandbox constraints."""
        cwd = self.working_dir or Path(tempfile.mkdtemp(prefix="autoship-sandbox-"))
        cwd.mkdir(parents=True, exist_ok=True)

        env = self._build_env()
        wrapped = self._wrap_network(command)

        logger.debug("Sandbox run: %s in %s (network=%s)", wrapped, cwd, self.network)
        try:
            proc = subprocess.run(
                wrapped,
                cwd=cwd,
                env=env,
                input=input_text,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            return SandboxResult(
                returncode=-1,
                stdout=_decode_stream(exc.stdout) or "",
                stderr=_decode_stream(exc.stderr) or "Sandbox execution timed out",
            )
        except (OSError, FileNotFoundError) as exc:
            return SandboxResult(returncode=-1, stdout="", stderr=str(exc))

        if wrapped != command and proc.returncode != 0 and self._is_tool_failure(proc.stderr):
            logger.warning(
                "Network sandbox tool failed (%s); retrying without network isolation",
                proc.stderr.strip(),
            )
            try:
                proc = subprocess.run(
                    command,
                    cwd=cwd,
                    env=env,
                    input=input_text,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired as exc:
                return SandboxResult(
                    returncode=-1,
                    stdout=_decode_stream(exc.stdout) or "",
                    stderr=_decode_stream(exc.stderr) or "Sandbox execution timed out",
                )
            except (OSError, FileNotFoundError) as exc:
                return SandboxResult(returncode=-1, stdout="", stderr=str(exc))

        return SandboxResult(returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)

    @staticmethod
    def _is_tool_failure(stderr: str) -> bool:
        """Return True when stderr indicates the sandbox tool itself failed."""
        indicators = [
            "Operation not permitted",
            "unshare failed",
            "firejail failed",
            "permission denied",
            "No such file or directory",
        ]
        text = stderr.lower()
        return any(indicator.lower() in text for indicator in indicators)

    def _build_env(self) -> dict[str, str]:
        """Return a minimal environment containing only whitelisted variables."""
        return {key: value for key, value in os.environ.items() if key in self.env_whitelist}

    def _wrap_network(self, command: list[str]) -> list[str]:
        """Wrap ``command`` with a network namespace tool when appropriate."""
        if self.network:
            return command

        if shutil.which("unshare"):
            return ["unshare", "--net", "--", *command]
        if shutil.which("firejail"):
            return ["firejail", "--net=none", "--quiet", "--", *command]

        if self.required:
            raise SandboxError(
                "Sandbox is required but no network isolation tool is available (unshare/firejail)"
            )

        logger.warning("No network sandbox tool available (unshare/firejail); network not blocked")
        return command

    def available(self) -> dict[str, Any]:
        """Report sandbox capability availability."""
        return {
            "network_unshare": shutil.which("unshare") is not None,
            "network_firejail": shutil.which("firejail") is not None,
            "directory_isolation": True,
            "env_isolation": True,
        }
