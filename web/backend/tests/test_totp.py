"""Tests for web.backend.core.totp module."""
import base64
import json
import time
from unittest.mock import patch

import pyotp
import pytest

from web.backend.core.totp import (
    ISSUER,
    _used_counters,
    decrypt_backup_codes,
    decrypt_totp_secret,
    encrypt_backup_codes,
    encrypt_totp_secret,
    generate_backup_codes,
    generate_qr_base64,
    generate_totp_secret,
    get_provisioning_uri,
    verify_backup_code,
    verify_totp_code,
)


@pytest.fixture(autouse=True)
def _clear_used_counters():
    _used_counters.clear()
    yield
    _used_counters.clear()


# ── generate_totp_secret ─────────────────────────────────────


def test_generate_totp_secret_returns_base32():
    secret = generate_totp_secret()
    assert isinstance(secret, str)
    assert len(secret) >= 16
    base64.b32decode(secret + "=" * (-len(secret) % 8))


def test_generate_totp_secret_unique():
    secrets = {generate_totp_secret() for _ in range(10)}
    assert len(secrets) == 10


# ── encrypt / decrypt TOTP secret ────────────────────────────


@patch("web.backend.core.totp.encrypt_field")
def test_encrypt_totp_secret_delegates(mock_enc):
    mock_enc.return_value = "cipher"
    result = encrypt_totp_secret("ABCDEFGH")
    mock_enc.assert_called_once_with("ABCDEFGH")
    assert result == "cipher"


@patch("web.backend.core.totp.decrypt_field")
def test_decrypt_totp_secret_delegates(mock_dec):
    mock_dec.return_value = "ABCDEFGH"
    result = decrypt_totp_secret("cipher")
    mock_dec.assert_called_once_with("cipher")
    assert result == "ABCDEFGH"


# ── encrypt / decrypt backup codes ───────────────────────────


@patch("web.backend.core.totp.encrypt_field")
def test_encrypt_backup_codes(mock_enc):
    codes = ["abc123", "def456"]
    mock_enc.return_value = "encrypted"
    result = encrypt_backup_codes(codes)
    mock_enc.assert_called_once_with(json.dumps(codes))
    assert result == "encrypted"


@patch("web.backend.core.totp.decrypt_field")
def test_decrypt_backup_codes_success(mock_dec):
    codes = ["abc123", "def456"]
    mock_dec.return_value = json.dumps(codes)
    result = decrypt_backup_codes("cipher")
    assert result == codes


@patch("web.backend.core.totp.decrypt_field")
def test_decrypt_backup_codes_not_a_list(mock_dec):
    mock_dec.return_value = json.dumps({"key": "value"})
    assert decrypt_backup_codes("cipher") is None


@patch("web.backend.core.totp.decrypt_field")
def test_decrypt_backup_codes_invalid_json(mock_dec):
    mock_dec.return_value = "not-json-at-all"
    assert decrypt_backup_codes("cipher") is None


@patch("web.backend.core.totp.decrypt_field", side_effect=ValueError("bad"))
def test_decrypt_backup_codes_decrypt_failure(mock_dec):
    assert decrypt_backup_codes("cipher") is None


# ── get_provisioning_uri ─────────────────────────────────────


def test_get_provisioning_uri_format():
    secret = pyotp.random_base32()
    uri = get_provisioning_uri(secret, "alice")
    assert uri.startswith("otpauth://totp/")
    assert "alice" in uri
    assert secret in uri


def test_get_provisioning_uri_different_users():
    secret = pyotp.random_base32()
    uri1 = get_provisioning_uri(secret, "bob")
    uri2 = get_provisioning_uri(secret, "charlie")
    assert uri1 != uri2


# ── generate_qr_base64 ──────────────────────────────────────


def test_generate_qr_base64_valid_png():
    uri = "otpauth://totp/Test:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Test"
    b64 = generate_qr_base64(uri)
    raw = base64.b64decode(b64)
    assert raw[:4] == b"\x89PNG"


def test_generate_qr_base64_non_empty():
    b64 = generate_qr_base64("https://example.com")
    assert len(b64) > 100


# ── verify_totp_code ─────────────────────────────────────────


def test_verify_totp_code_valid():
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    code = totp.now()
    assert verify_totp_code(secret, code) is True


def test_verify_totp_code_wrong_code():
    secret = pyotp.random_base32()
    assert verify_totp_code(secret, "000000") is False


def test_verify_totp_code_strips_whitespace():
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    code = totp.now()
    assert verify_totp_code(secret, f"  {code}  ") is True


def test_verify_totp_code_no_replay_without_account_id():
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    code = totp.now()
    assert verify_totp_code(secret, code) is True
    assert verify_totp_code(secret, code) is True


def test_verify_totp_code_with_account_id_valid():
    """Valid code with account_id returns True on first use."""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    code = totp.now()
    assert verify_totp_code(secret, code, account_id=42) is True


def test_verify_totp_code_replay_protection():
    """Same valid code with same account_id is rejected on second use."""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    code = totp.now()
    assert verify_totp_code(secret, code, account_id=42) is True
    assert verify_totp_code(secret, code, account_id=42) is False


def test_verify_totp_code_different_accounts():
    """Different account_ids with same code both succeed (no cross-blocking)."""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    code = totp.now()
    assert verify_totp_code(secret, code, account_id=1) is True
    assert verify_totp_code(secret, code, account_id=2) is True


def test_verify_totp_code_stale_cleanup():
    """Stale entries in _used_counters are cleaned up during verification."""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    _used_counters[999] = 0  # counter from epoch — very stale
    code = totp.now()
    verify_totp_code(secret, code, account_id=77)
    assert 77 in _used_counters
    assert 999 not in _used_counters


# ── generate_backup_codes ────────────────────────────────────


def test_generate_backup_codes_default_count():
    codes = generate_backup_codes()
    assert len(codes) == 8


def test_generate_backup_codes_custom_count():
    codes = generate_backup_codes(count=4)
    assert len(codes) == 4


def test_generate_backup_codes_format():
    codes = generate_backup_codes()
    for code in codes:
        assert len(code) == 8
        assert code.isalnum()
        assert code == code.lower()


def test_generate_backup_codes_unique():
    codes = generate_backup_codes(count=20)
    assert len(set(codes)) == 20


# ── verify_backup_code ───────────────────────────────────────


@patch("web.backend.core.totp.decrypt_backup_codes")
@patch("web.backend.core.totp.encrypt_backup_codes")
def test_verify_backup_code_valid(mock_enc, mock_dec):
    mock_dec.return_value = ["abc12345", "def67890", "ghi11111"]
    mock_enc.return_value = "updated_enc"
    ok, updated = verify_backup_code("encrypted_blob", "abc12345")
    assert ok is True
    assert updated == "updated_enc"
    mock_enc.assert_called_once_with(["def67890", "ghi11111"])


@patch("web.backend.core.totp.decrypt_backup_codes")
def test_verify_backup_code_invalid(mock_dec):
    mock_dec.return_value = ["abc12345", "def67890"]
    ok, updated = verify_backup_code("encrypted_blob", "wrong_code")
    assert ok is False
    assert updated == "encrypted_blob"


def test_verify_backup_code_none_input():
    ok, updated = verify_backup_code(None, "anycode")
    assert ok is False
    assert updated is None


def test_verify_backup_code_empty_string():
    ok, updated = verify_backup_code("", "anycode")
    assert ok is False
    assert updated == ""


@patch("web.backend.core.totp.decrypt_backup_codes")
def test_verify_backup_code_decrypt_fails(mock_dec):
    mock_dec.return_value = None
    ok, updated = verify_backup_code("encrypted_blob", "abc12345")
    assert ok is False
    assert updated == "encrypted_blob"


@patch("web.backend.core.totp.decrypt_backup_codes")
@patch("web.backend.core.totp.encrypt_backup_codes")
def test_verify_backup_code_last_code_returns_none(mock_enc, mock_dec):
    mock_dec.return_value = ["onlycode"]
    ok, updated = verify_backup_code("encrypted_blob", "onlycode")
    assert ok is True
    assert updated is None
    mock_enc.assert_not_called()


@patch("web.backend.core.totp.decrypt_backup_codes")
@patch("web.backend.core.totp.encrypt_backup_codes")
def test_verify_backup_code_case_insensitive(mock_enc, mock_dec):
    mock_dec.return_value = ["abc12345"]
    mock_enc.return_value = "enc"
    ok, _ = verify_backup_code("blob", "ABC12345")
    assert ok is True


@patch("web.backend.core.totp.decrypt_backup_codes")
@patch("web.backend.core.totp.encrypt_backup_codes")
def test_verify_backup_code_strips_whitespace(mock_enc, mock_dec):
    mock_dec.return_value = ["abc12345"]
    mock_enc.return_value = "enc"
    ok, _ = verify_backup_code("blob", "  abc12345  ")
    assert ok is True
