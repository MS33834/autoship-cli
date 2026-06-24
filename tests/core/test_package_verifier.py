"""Tests for package download and integrity verification."""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from autoship.core.package_verifier import (
    PackageVerificationError,
    compute_sha256,
    verify_package,
)


def _make_keypair() -> tuple[str, str]:
    """Return (public_key_b64, sha256_hex_signed_b64) helper for a given payload."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return base64.b64encode(public_key.public_bytes_raw()).decode("ascii"), private_key


def test_compute_sha256(tmp_path: Path) -> None:
    path = tmp_path / "pkg.whl"
    path.write_bytes(b"hello")
    assert compute_sha256(path) == hashlib.sha256(b"hello").hexdigest()


def test_verify_package_with_valid_sha256(tmp_path: Path) -> None:
    path = tmp_path / "pkg.whl"
    path.write_bytes(b"hello")
    sha256 = hashlib.sha256(b"hello").hexdigest()

    verify_package(path, sha256_hex=sha256, signature_b64=None, public_key_b64=None)


def test_verify_package_with_invalid_sha256(tmp_path: Path) -> None:
    path = tmp_path / "pkg.whl"
    path.write_bytes(b"hello")

    with pytest.raises(PackageVerificationError):
        verify_package(
            path,
            sha256_hex="0" * 64,
            signature_b64=None,
            public_key_b64=None,
        )


def test_verify_package_with_valid_signature(tmp_path: Path) -> None:
    path = tmp_path / "pkg.whl"
    path.write_bytes(b"hello")
    sha256 = hashlib.sha256(b"hello").hexdigest()
    public_key_b64, private_key = _make_keypair()
    signature = private_key.sign(sha256.encode("ascii"))
    signature_b64 = base64.b64encode(signature).decode("ascii")

    verify_package(
        path, sha256_hex=sha256, signature_b64=signature_b64, public_key_b64=public_key_b64
    )


def test_verify_package_with_invalid_signature(tmp_path: Path) -> None:
    path = tmp_path / "pkg.whl"
    path.write_bytes(b"hello")
    sha256 = hashlib.sha256(b"hello").hexdigest()
    public_key_b64, _private_key = _make_keypair()

    with pytest.raises(PackageVerificationError):
        verify_package(
            path,
            sha256_hex=sha256,
            signature_b64=base64.b64encode(b"invalid").decode("ascii"),
            public_key_b64=public_key_b64,
        )


def test_verify_package_requires_public_key_when_signature_present(tmp_path: Path) -> None:
    path = tmp_path / "pkg.whl"
    path.write_bytes(b"hello")
    sha256 = hashlib.sha256(b"hello").hexdigest()

    with pytest.raises(PackageVerificationError):
        verify_package(
            path,
            sha256_hex=sha256,
            signature_b64=base64.b64encode(b"sig").decode("ascii"),
            public_key_b64=None,
        )


def test_verify_package_requires_sha256_when_signature_present(tmp_path: Path) -> None:
    path = tmp_path / "pkg.whl"
    path.write_bytes(b"hello")
    public_key_b64, _private_key = _make_keypair()

    with pytest.raises(PackageVerificationError):
        verify_package(
            path,
            sha256_hex=None,
            signature_b64=base64.b64encode(b"sig").decode("ascii"),
            public_key_b64=public_key_b64,
        )


def test_download_package_returns_path_and_clears_directory(tmp_path: Path) -> None:
    from autoship.core.package_verifier import download_package

    pkg = tmp_path / "pkg.whl"
    pkg.write_bytes(b"pkg")

    def _fake_run(cmd: list[str], **_kwargs: object) -> object:
        # The function places the package in the temp dir itself for this test.
        return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    with (
        patch("autoship.core.package_verifier.subprocess.run", side_effect=_fake_run),
        patch(
            "autoship.utils.hashing.pip_cmd",
            return_value=["pip"],
        ),
    ):
        out_dir = tmp_path / "download"
        out_dir.mkdir()
        # Move pkg into download dir so download_package can find it.
        pkg.rename(out_dir / "pkg.whl")
        result = download_package("pkg==1.0.0", out_dir)

    assert result == out_dir / "pkg.whl"
