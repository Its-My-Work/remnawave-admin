"""Symmetric encryption for sensitive fields (TOTP secrets, backup codes).

Uses Fernet (AES-128-CBC + HMAC-SHA256) with a key derived from WEB_SECRET_KEY.
"""
import hashlib
import base64

from cryptography.fernet import Fernet, InvalidToken

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is not None:
        return _fernet
    from web.backend.core.config import get_web_settings
    raw_key = get_web_settings().secret_key.encode()
    # Domain separation: derive a Fernet key independent from the JWT signing key
    # so that rotating WEB_SECRET_KEY for JWT invalidation won't break encrypted data.
    derived = hashlib.sha256(b"totp-field-encryption:" + raw_key).digest()
    _fernet = Fernet(base64.urlsafe_b64encode(derived))
    return _fernet


def encrypt_field(plaintext: str) -> str:
    """Encrypt a string field for database storage."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_field(ciphertext: str) -> str:
    """Decrypt a database-stored encrypted field."""
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        raise ValueError("Failed to decrypt field — key mismatch or corrupted data")
