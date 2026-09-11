import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

import models
from database import get_db


# ---------------------------------------------------------------------------
# Authentication configuration
# ---------------------------------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable is not configured."
    )

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120")
)

security = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Password hashing
#
# PBKDF2-SHA256 is used so we do not store plain-text passwords.
# Stored format:
#
# pbkdf2_sha256$iterations$salt$hash
# ---------------------------------------------------------------------------

PBKDF2_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password cannot be empty.")

    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )

    encoded_salt = base64.b64encode(salt).decode("utf-8")
    encoded_hash = base64.b64encode(password_hash).decode("utf-8")

    return (
        f"pbkdf2_sha256$"
        f"{PBKDF2_ITERATIONS}$"
        f"{encoded_salt}$"
        f"{encoded_hash}"
    )


def verify_password(
    plain_password: str,
    stored_password_hash: str,
) -> bool:

    if not plain_password or not stored_password_hash:
        return False

    try:
        algorithm, iterations, encoded_salt, encoded_hash = (
            stored_password_hash.split("$", 3)
        )

        if algorithm != "pbkdf2_sha256":
            return False

        salt = base64.b64decode(encoded_salt)
        expected_hash = base64.b64decode(encoded_hash)

        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            int(iterations),
        )

        return hmac.compare_digest(
            calculated_hash,
            expected_hash,
        )

    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT access tokens
# ---------------------------------------------------------------------------

def create_access_token(
    user: models.User,
    expires_minutes: int | None = None,
) -> str:

    expiry_minutes = (
        expires_minutes
        if expires_minutes is not None
        else ACCESS_TOKEN_EXPIRE_MINUTES
    )

    now = datetime.now(timezone.utc)

    payload = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(minutes=expiry_minutes),
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )


# ---------------------------------------------------------------------------
# Current authenticated user
# ---------------------------------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> models.User:

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme.",
        )

    payload = decode_access_token(
        credentials.credentials
    )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )

    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    return user


# ---------------------------------------------------------------------------
# Role-based authorization
# ---------------------------------------------------------------------------

def require_roles(*allowed_roles: str):
    """
    Dependency used to protect endpoints by role.

    Example:

        @router.post("/approve")
        def approve(
            current_user = Depends(
                require_roles(
                    models.Role.COMMANDER.value,
                    models.Role.ADMIN.value,
                )
            )
        ):
            ...
    """

    def role_checker(
        current_user: models.User = Depends(get_current_user),
    ) -> models.User:

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You do not have permission "
                    "to perform this action."
                ),
            )

        return current_user

    return role_checker


# ---------------------------------------------------------------------------
# Convenience role groups
# ---------------------------------------------------------------------------

COMMAND_CENTER_ROLES = (
    models.Role.OPERATOR.value,
    models.Role.COMMANDER.value,
    models.Role.ADMIN.value,
)

COMMANDER_ROLES = (
    models.Role.COMMANDER.value,
    models.Role.ADMIN.value,
)

ADMIN_ROLES = (
    models.Role.ADMIN.value,
)
