from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, Request, status

from app.auth.models import OpsUser, Role

# TODO: Replace hardcoded JWT verification with Auth0/Cognito JWKS endpoint.
# Integration point:
#   jwks_client = PyJWKClient(AUTH0_JWKS_URL)
#   signing_key = jwks_client.get_signing_key_from_jwt(token)
#   payload = jwt.decode(token, signing_key, algorithms=["RS256"])
#   return OpsUser(id=payload["sub"], username=payload.get("name"), ...)

OPS_USERS: dict[str, OpsUser] = {
    "viewer-token": OpsUser(
        id="u-viewer", username="ops-viewer", role=Role.VIEWER, token="viewer-token"
    ),
    "commander-token": OpsUser(
        id="u-cmdr", username="ops-commander", role=Role.COMMANDER, token="commander-token"
    ),
    "admin-token": OpsUser(
        id="u-admin", username="ops-admin", role=Role.ADMIN, token="admin-token"
    ),
}


def verify_token(token: str) -> OpsUser:
    if token in OPS_USERS:
        return OPS_USERS[token]
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return OpsUser(
            id=payload.get("sub", "unknown"),
            username=payload.get("name", "unknown"),
            role=Role.VIEWER,
            token=token,
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_ops_user(request: Request) -> OpsUser:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
        )
    token = auth_header.removeprefix("Bearer ")
    return verify_token(token)


def require_role(required: Role) -> Callable:
    async def dependency(current_user: OpsUser = Depends(get_current_ops_user)) -> OpsUser:
        if current_user.role.value < required.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' lacks permission; "
                f"'{required}' required",
            )
        return current_user

    return dependency
