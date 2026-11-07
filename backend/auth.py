"""Auth0 login for saved progress.

Configured (AUTH0_DOMAIN + AUTH0_AUDIENCE set): routes under /api/me require
`Authorization: Bearer <Auth0 access token>`, verified against the tenant's JWKS (RS256,
audience, issuer, expiry). The user id is the token's `sub`.

Not configured: demo mode. The frontend sends `X-Demo-User: <any id>` so saving works locally
before Auth0 exists. Set AUTH_DEMO_MODE=off to forbid that in a deployment.
"""
from __future__ import annotations

import os
import re
from functools import lru_cache

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "").strip().removeprefix("https://").rstrip("/")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "").strip()
DEMO_MODE = os.getenv("AUTH_DEMO_MODE", "on").strip().lower() != "off"
_DEMO_ID = re.compile(r"^[A-Za-z0-9_.-]{3,64}$")


class AuthError(Exception):
    def __init__(self, status: int, error: str, message: str):
        super().__init__(message)
        self.status, self.error, self.message = status, error, message


def configured() -> bool:
    return bool(AUTH0_DOMAIN and AUTH0_AUDIENCE)


def info() -> dict:
    return {"provider": "auth0" if configured() else ("demo" if DEMO_MODE else "none"),
            "domain": AUTH0_DOMAIN or None, "audience": AUTH0_AUDIENCE or None}


@lru_cache(maxsize=1)
def _jwks():
    import jwt
    return jwt.PyJWKClient(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json", cache_keys=True, lifespan=3600)


def user_from_request(headers) -> dict:
    """Return {"id", "provider"} or raise AuthError."""
    auth = headers.get("Authorization", "")
    if configured():
        if not auth.lower().startswith("bearer "):
            raise AuthError(401, "auth_required", "Log in first: send Authorization: Bearer <Auth0 access token>.")
        token = auth.split(" ", 1)[1].strip()
        import jwt
        try:
            key = _jwks().get_signing_key_from_jwt(token).key
            claims = jwt.decode(token, key, algorithms=["RS256"], audience=AUTH0_AUDIENCE,
                                issuer=f"https://{AUTH0_DOMAIN}/", options={"require": ["exp", "sub"]})
        except jwt.ExpiredSignatureError:
            raise AuthError(401, "token_expired", "Your session expired. Log in again.")
        except Exception as e:
            raise AuthError(401, "invalid_token", f"Invalid access token ({type(e).__name__}).")
        return {"id": "auth0|" + str(claims["sub"])[:120], "provider": "auth0"}
    if DEMO_MODE:
        demo = headers.get("X-Demo-User", "").strip()
        if not _DEMO_ID.match(demo):
            raise AuthError(401, "auth_required",
                            "Auth0 is not configured yet. For local testing send X-Demo-User: <3-64 letters, digits, _ . ->.")
        return {"id": "demo|" + demo, "provider": "demo"}
    raise AuthError(503, "auth_not_configured", "Login is not configured on this server.")
