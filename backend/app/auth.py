"""Verify Clerk session tokens. Routes stay free of Clerk SDK details."""

from __future__ import annotations

from typing import Annotated

from clerk_backend_api import AuthenticateRequestOptions, authenticate_request
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings

http_bearer = HTTPBearer(auto_error=False)


def require_auth(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    _creds: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)] = None,
) -> str | None:
    """Return the Clerk user id, or None when auth is not configured.

    Tests and key-less local runs skip verification. A set ``CLERK_SECRET_KEY``
    requires a valid Bearer session token on protected routes.
    """
    del _creds
    secret = settings.clerk_secret_key.strip()
    if not secret:
        return None

    state = authenticate_request(
        request,
        AuthenticateRequestOptions(
            secret_key=secret,
            jwt_key=settings.clerk_jwt_key or None,
            authorized_parties=list(settings.clerk_authorized_parties),
            accepts_token=["session_token"],
        ),
    )
    if not state.is_signed_in or not state.payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in to evaluate answers.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = state.payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in to evaluate answers.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
