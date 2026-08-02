"""Lightweight API-key / JWT auth seam.

Starter ships with a development API key check. Swap for full OIDC/RBAC later
without rewriting routers — depend on `require_auth` only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt

from app.config.settings import Settings, get_settings


@dataclass(frozen=True, slots=True)
class AuthPrincipal:
    subject: str
    roles: tuple[str, ...] = ("operator",)


async def require_auth(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> AuthPrincipal:
    # Development convenience: open access when no auth headers are configured usage.
    open_envs = {"development", "test", "simulation"}
    if settings.app_env in open_envs and not authorization and not x_api_key:
        return AuthPrincipal(subject="dev-operator", roles=("operator", "admin"))

    if x_api_key:
        expected = settings.jwt_secret.get_secret_value()
        if x_api_key != expected:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
        return AuthPrincipal(subject="api-key", roles=("operator",))

    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret.get_secret_value(),
                algorithms=[settings.jwt_algorithm],
            )
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            ) from exc
        subject = str(payload.get("sub", "unknown"))
        roles = tuple(payload.get("roles", ["operator"]))
        return AuthPrincipal(subject=subject, roles=roles)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
