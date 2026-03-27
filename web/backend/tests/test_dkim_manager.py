"""Tests for DKIM key management and email signing."""
import base64
from unittest.mock import patch, MagicMock

import pytest

from web.backend.core.mail.dkim_manager import (
    generate_dkim_keypair,
    get_dkim_dns_record,
    get_public_key_base64,
    sign_message,
)


# ── generate_dkim_keypair ────────────────────────────────────


class TestGenerateDkimKeypair:

    def test_returns_tuple_of_two_strings(self):
        private_pem, public_pem = generate_dkim_keypair()
        assert isinstance(private_pem, str)
        assert isinstance(public_pem, str)

    def test_private_key_pem_format(self):
        private_pem, _ = generate_dkim_keypair()
        assert private_pem.startswith("-----BEGIN PRIVATE KEY-----")
        assert private_pem.strip().endswith("-----END PRIVATE KEY-----")

    def test_public_key_pem_format(self):
        _, public_pem = generate_dkim_keypair()
        assert public_pem.startswith("-----BEGIN PUBLIC KEY-----")
        assert public_pem.strip().endswith("-----END PUBLIC KEY-----")

    def test_keys_are_unique_per_call(self):
        pair_a = generate_dkim_keypair()
        pair_b = generate_dkim_keypair()
        assert pair_a[0] != pair_b[0]
        assert pair_a[1] != pair_b[1]

    def test_private_key_is_valid_base64_body(self):
        private_pem, _ = generate_dkim_keypair()
        lines = private_pem.strip().split("\n")
        body = "".join(line for line in lines if not line.startswith("-----"))
        decoded = base64.b64decode(body)
        assert len(decoded) > 0

    def test_public_key_is_valid_base64_body(self):
        _, public_pem = generate_dkim_keypair()
        lines = public_pem.strip().split("\n")
        body = "".join(line for line in lines if not line.startswith("-----"))
        decoded = base64.b64decode(body)
        assert len(decoded) > 0


# ── sign_message ─────────────────────────────────────────────


class TestSignMessage:

    def test_sign_prepends_signature(self):
        fake_signature = b"DKIM-Signature: v=1; a=rsa-sha256; d=example.com\r\n"
        raw = b"From: sender@example.com\r\nSubject: Hi\r\n\r\nBody"

        mock_dkim = MagicMock()
        mock_dkim.sign.return_value = fake_signature

        with patch.dict("sys.modules", {"dkim": mock_dkim}):
            result = sign_message(raw, "example.com", "default", "fake-key")

        assert result == fake_signature + raw
        mock_dkim.sign.assert_called_once()

    def test_sign_passes_correct_arguments(self):
        mock_dkim = MagicMock()
        mock_dkim.sign.return_value = b""

        raw = b"From: a@b.com\r\n\r\nHello"
        private_pem = "-----BEGIN PRIVATE KEY-----\nfake\n-----END PRIVATE KEY-----"

        with patch.dict("sys.modules", {"dkim": mock_dkim}):
            sign_message(raw, "mydomain.org", "sel2024", private_pem)

        call_kwargs = mock_dkim.sign.call_args
        assert call_kwargs.kwargs["domain"] == b"mydomain.org"
        assert call_kwargs.kwargs["selector"] == b"sel2024"
        assert call_kwargs.kwargs["privkey"] == private_pem.encode()

    def test_fallback_on_signing_exception(self):
        raw = b"From: sender@example.com\r\n\r\nBody"
        mock_dkim = MagicMock()
        mock_dkim.sign.side_effect = RuntimeError("signing failed")

        with patch.dict("sys.modules", {"dkim": mock_dkim}):
            result = sign_message(raw, "example.com", "default", "fake-key")

        assert result == raw

    def test_fallback_logs_error(self):
        raw = b"From: a@b.com\r\n\r\nHi"
        mock_dkim = MagicMock()
        mock_dkim.sign.side_effect = ValueError("bad key")

        with patch.dict("sys.modules", {"dkim": mock_dkim}), \
             patch("web.backend.core.mail.dkim_manager.logger") as mock_logger:
            sign_message(raw, "test.com", "sel", "key")

        mock_logger.error.assert_called_once()


# ── get_dkim_dns_record ──────────────────────────────────────


class TestGetDkimDnsRecord:

    def test_format_with_real_key(self):
        _, public_pem = generate_dkim_keypair()
        record = get_dkim_dns_record("default", public_pem)
        assert record.startswith("v=DKIM1; k=rsa; p=")
        assert "-----" not in record

    def test_key_data_is_valid_base64(self):
        _, public_pem = generate_dkim_keypair()
        record = get_dkim_dns_record("default", public_pem)
        key_b64 = record.split("p=")[1]
        decoded = base64.b64decode(key_b64)
        assert len(decoded) > 0

    def test_with_minimal_pem(self):
        pem = "-----BEGIN PUBLIC KEY-----\nABCD1234\n-----END PUBLIC KEY-----"
        record = get_dkim_dns_record("sel", pem)
        assert record == "v=DKIM1; k=rsa; p=ABCD1234"

    def test_multiline_pem_body(self):
        pem = (
            "-----BEGIN PUBLIC KEY-----\n"
            "AAAA\n"
            "BBBB\n"
            "CCCC\n"
            "-----END PUBLIC KEY-----"
        )
        record = get_dkim_dns_record("sel", pem)
        assert record == "v=DKIM1; k=rsa; p=AAAABBBBCCCC"


# ── get_public_key_base64 ────────────────────────────────────


class TestGetPublicKeyBase64:

    def test_strips_pem_headers(self):
        pem = "-----BEGIN PUBLIC KEY-----\nSOMEDATA\n-----END PUBLIC KEY-----"
        result = get_public_key_base64(pem)
        assert result == "SOMEDATA"

    def test_multiline_body(self):
        pem = (
            "-----BEGIN PUBLIC KEY-----\n"
            "LINE1\n"
            "LINE2\n"
            "LINE3\n"
            "-----END PUBLIC KEY-----"
        )
        result = get_public_key_base64(pem)
        assert result == "LINE1LINE2LINE3"

    def test_no_headers_in_result(self):
        _, public_pem = generate_dkim_keypair()
        result = get_public_key_base64(public_pem)
        assert "-----" not in result

    def test_consistent_with_dns_record(self):
        _, public_pem = generate_dkim_keypair()
        b64 = get_public_key_base64(public_pem)
        dns_record = get_dkim_dns_record("sel", public_pem)
        assert dns_record == f"v=DKIM1; k=rsa; p={b64}"
