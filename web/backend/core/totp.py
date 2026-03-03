"""TOTP two-factor authentication utilities."""
import hmac
import io
import json
import base64
import secrets
import string
import threading
import time
from typing import List, Tuple, Optional

import pyotp
import qrcode

from web.backend.core.crypto import encrypt_field, decrypt_field


ISSUER = "Remnawave Admin"

# ── TOTP replay protection ──────────────────────────────────────
# Track last-used TOTP timestamp per account to prevent code reuse.
# Key: account_id (int), Value: last pyotp counter (int).
_used_counters: dict[int, int] = {}
_used_lock = threading.Lock()
_COUNTER_TTL = 120  # Keep entries for 2 minutes max


def _current_counter() -> int:
    """Current TOTP 30-second time step."""
    return int(time.time()) // 30


def generate_totp_secret() -> str:
    """Generate a new TOTP secret key (base32, plaintext)."""
    return pyotp.random_base32()


def encrypt_totp_secret(secret: str) -> str:
    """Encrypt a TOTP secret for database storage."""
    return encrypt_field(secret)


def decrypt_totp_secret(ciphertext: str) -> str:
    """Decrypt a TOTP secret from database storage."""
    return decrypt_field(ciphertext)


def encrypt_backup_codes(codes: List[str]) -> str:
    """Encrypt backup codes JSON for database storage."""
    return encrypt_field(json.dumps(codes))


def decrypt_backup_codes(ciphertext: str) -> Optional[List[str]]:
    """Decrypt backup codes from database storage. Returns None on failure."""
    try:
        result = json.loads(decrypt_field(ciphertext))
        if not isinstance(result, list):
            return None
        return result
    except (ValueError, json.JSONDecodeError):
        return None


def get_provisioning_uri(secret: str, username: str) -> str:
    """Build an otpauth:// URI for authenticator apps."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=ISSUER)


def generate_qr_base64(uri: str) -> str:
    """Render a provisioning URI as a base64-encoded PNG image."""
    img = qrcode.make(uri, box_size=6, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def verify_totp_code(secret: str, code: str, account_id: Optional[int] = None) -> bool:
    """Verify a 6-digit TOTP code (allows +/-1 time window).

    If account_id is provided, also checks for replay (same code reused).
    """
    totp = pyotp.TOTP(secret)
    stripped = code.strip()

    # First: check if the code is valid at all
    if not totp.verify(stripped, valid_window=1):
        return False

    # No replay protection requested
    if account_id is None:
        return True

    # Determine which counter step this code belongs to
    now_counter = int(time.time()) // 30
    for offset in range(-1, 2):
        candidate = now_counter + offset
        if hmac.compare_digest(totp.at(candidate), stripped):
            with _used_lock:
                last = _used_counters.get(account_id)
                if last is not None and last >= candidate:
                    return False  # Replay detected
                _used_counters[account_id] = candidate
                # Cleanup stale entries
                cutoff = _current_counter() - (_COUNTER_TTL // 30)
                stale = [k for k, v in _used_counters.items() if v < cutoff]
                for k in stale:
                    del _used_counters[k]
            return True

    # Code was valid per pyotp but we couldn't identify the counter step
    # (should not happen in practice). Accept it but skip replay tracking.
    return True


def generate_backup_codes(count: int = 8) -> List[str]:
    """Generate a set of one-time backup codes (8 alphanumeric chars each)."""
    alphabet = string.digits + string.ascii_lowercase
    return ["".join(secrets.choice(alphabet) for _ in range(8)) for _ in range(count)]


def verify_backup_code(
    stored_codes_encrypted: Optional[str], code: str
) -> Tuple[bool, Optional[str]]:
    """Check a backup code and remove it if valid.

    Uses constant-time comparison to prevent timing attacks.

    Args:
        stored_codes_encrypted: Fernet-encrypted JSON array of codes, or None.
        code: User-provided backup code.

    Returns:
        (is_valid, updated_encrypted_codes).
        updated_encrypted_codes is None when no codes remain.
    """
    if not stored_codes_encrypted:
        return False, stored_codes_encrypted

    codes = decrypt_backup_codes(stored_codes_encrypted)
    if codes is None:
        return False, stored_codes_encrypted

    normalized = code.strip().lower()

    # Constant-time scan: always check all codes to avoid timing leak
    match_idx = -1
    for i, stored in enumerate(codes):
        if hmac.compare_digest(normalized.encode(), stored.encode()):
            match_idx = i

    if match_idx < 0:
        return False, stored_codes_encrypted

    codes.pop(match_idx)
    updated = encrypt_backup_codes(codes) if codes else None
    return True, updated
