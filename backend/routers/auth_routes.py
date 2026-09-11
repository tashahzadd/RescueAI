import os

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import models
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from database import get_db


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str


class BootstrapRequest(BaseModel):
    setup_token: str
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    is_active: bool


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    email = payload.email.strip().lower()

    user = (
        db.query(models.User)
        .filter(models.User.email == email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive.",
        )

    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account does not have login credentials configured.",
        )

    if not verify_password(
        payload.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    access_token = create_access_token(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
        },
    }


# ---------------------------------------------------------------------------
# Current User
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_my_account(
    current_user: models.User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
    }


# ---------------------------------------------------------------------------
# One-Time Commander Bootstrap
# ---------------------------------------------------------------------------

@router.post(
    "/bootstrap-commander",
    response_model=UserResponse,
)
def bootstrap_commander(
    payload: BootstrapRequest,
    db: Session = Depends(get_db),
):
    """
    Create the first RescueAI Commander account.

    This endpoint is protected by BOOTSTRAP_TOKEN.

    Once a Commander/Admin exists, this endpoint refuses to create
    another privileged account.
    """

    expected_token = os.getenv("BOOTSTRAP_TOKEN")

    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Commander bootstrap is disabled.",
        )

    if payload.setup_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid setup token.",
        )

    privileged_user = (
        db.query(models.User)
        .filter(
            models.User.role.in_(
                [
                    models.Role.COMMANDER.value,
                    models.Role.ADMIN.value,
                ]
            )
        )
        .first()
    )

    if privileged_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A Commander or Administrator account already exists. "
                "Bootstrap is no longer permitted."
            ),
        )

    email = payload.email.strip().lower()

    existing_user = (
        db.query(models.User)
        .filter(models.User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    commander = models.User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=models.Role.COMMANDER.value,
        is_active=True,
    )

    db.add(commander)
    db.commit()
    db.refresh(commander)

    return {
        "id": commander.id,
        "name": commander.name,
        "email": commander.email,
        "role": commander.role,
        "is_active": commander.is_active,
    }
