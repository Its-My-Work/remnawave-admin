"""Dependencies for public API v3 — API key authentication and rate limiting."""
import logging
from dataclasses import dataclass, field
from typing import List

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)


@dataclass
class ApiKeyUser:
    """Authenticated API key context."""
    key_id: int
    key_name: str
    scopes: List[str] = field(default_factory=list)

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes


async def require_api_key(request: Request) -> ApiKeyUser:
    """Dependency: extract and validate X-API-Key header."""
    raw_key = request.headers.get("X-API-Key")
    if not raw_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )

    from web.backend.core.api_key_auth import validate_api_key
    key_data = await validate_api_key(raw_key)
    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
        )

    user = ApiKeyUser(
        key_id=key_data["id"],
        key_name=key_data["name"],
        scopes=key_data["scopes"],
    )
    # Stash on request.state so rate-limit keyfunc can read it without re-auth.
    request.state.api_key_user = user
    return user


def require_scope(scope: str):
    """Dependency factory: check that the API key has a specific scope AND
    enforces a per-key rate limit (read/write/bulk) based on method+path.
    """
    async def _check(request: Request) -> ApiKeyUser:
        api_key = await require_api_key(request)
        if not api_key.has_scope(scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing scope: {scope}",
            )
        # Apply rate limit per request method/path.
        from web.backend.api.v3.rate_limit import read_limit, write_limit, bulk_limit
        path = request.url.path or ""
        method = request.method.upper()
        if "/bulk/" in path:
            await bulk_limit(request)
        elif method == "GET":
            await read_limit(request)
        else:
            await write_limit(request)
        return api_key
    return _check


def api_key_identifier(request: Request) -> str:
    """key_func for slowapi — bucket by API key id, fall back to IP."""
    user = getattr(request.state, "api_key_user", None)
    if user is not None:
        return f"apikey:{user.key_id}"
    # Before dependency runs (shouldn't really happen if decorator comes after Depends)
    from slowapi.util import get_remote_address
    return f"ip:{get_remote_address(request)}"
