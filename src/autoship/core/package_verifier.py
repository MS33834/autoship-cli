"""Download and verify plugin package integrity before installation."""

from __future__ import annotations

import base64
import hashlib
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from cryptography.exceptions import InvalidSignature  # pyright: ignore[reportMissingImports]
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey,  # pyright: ignore[reportMissingImports]
)

from autoship.exceptions import PluginError

logger = logging.getLogger("autoship")


class PackageVerificationError(PluginError):
    """Raised when a plugin package fails integrity or signature verification."""


class PackageDownloadError(PluginError):
    """Raised when a plugin package cannot be downloaded."""


def _pip_cmd() -> list[str]:
    """Return the preferred package installer command (uv or pip)."""
    if shutil.which("uv"):
        return ["uv", "pip"]
    return ["pip"]


def compute_sha256(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_package(
    package_path: Path,
    *,
    sha256_hex: str | None,
    signature_b64: str | None,
    public_key_b64: str | None,
) -> None:
    """Verify a downloaded package against an expected sha256 and/or signature.

    When ``signature_b64`` is provided, ``sha256_hex`` and ``public_key_b64``
    must also be provided. The signature is validated over the sha256 hex string.

    Raises:
        PackageVerificationError: If any check fails.
    """
    actual_sha256 = compute_sha256(package_path)

    if sha256_hex is not None and actual_sha256 != sha256_hex:
        raise PackageVerificationError(
            "Package sha256 mismatch",
            details={"expected": sha256_hex, "actual": actual_sha256},
        )

    if signature_b64 is not None:
        if sha256_hex is None:
            raise PackageVerificationError(
                "Package signature requires a sha256 hash",
            )
        if public_key_b64 is None:
            raise PackageVerificationError(
                "Package signature present but no public key configured",
            )
        try:
            public_key_bytes = base64.b64decode(public_key_b64, validate=True)
            signature_bytes = base64.b64decode(signature_b64, validate=True)
            public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
            public_key.verify(signature_bytes, sha256_hex.encode("ascii"))
        except (ValueError, InvalidSignature) as exc:
            raise PackageVerificationError(
                "Package signature verification failed",
                details={"reason": str(exc)},
            ) from exc


def download_package(source_for_pip: str, output_dir: Path) -> Path:
    """Download a package to a directory without installing it.

    Returns the path to the downloaded wheel or sdist.

    Raises:
        PackageDownloadError: If the download fails or no file is produced.
    """
    pip_cmd = _pip_cmd()
    args = [*pip_cmd, "download", "--no-deps", "--quiet", "-d", str(output_dir), source_for_pip]
    try:
        result = subprocess.run(
            args,
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        raise PackageDownloadError(
            f"Failed to download package {source_for_pip}",
            details={"reason": str(exc), "stderr": getattr(exc, "stderr", "")},
        ) from exc

    if result.returncode != 0:
        raise PackageDownloadError(
            f"Failed to download package {source_for_pip}",
            details={"stderr": result.stderr},
        )

    files = list(output_dir.iterdir())
    if len(files) != 1:
        raise PackageDownloadError(
            f"Expected exactly one downloaded file for {source_for_pip}, found {len(files)}",
        )
    return files[0]


def download_and_verify(
    source_for_pip: str,
    *,
    sha256_hex: str | None,
    signature_b64: str | None,
    public_key_b64: str | None,
) -> Path:
    """Download a package and verify it before returning the local file path.

    The caller is responsible for deleting the returned file after installation.
    """
    with tempfile.TemporaryDirectory(prefix="autoship-pkg-") as tmp:
        tmp_path = Path(tmp)
        package_path = download_package(source_for_pip, tmp_path)
        verify_package(
            package_path,
            sha256_hex=sha256_hex,
            signature_b64=signature_b64,
            public_key_b64=public_key_b64,
        )
        # Move out of the temporary directory so the caller can keep it.
        final_path = Path(tempfile.mkdtemp(prefix="autoship-pkg-")) / package_path.name
        final_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(package_path), str(final_path))
    return final_path
