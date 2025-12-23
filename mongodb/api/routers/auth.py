"""
Authentication Router
Handles user registration, login, and token refresh
"""

from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta
from mongodb.api.auth.jwt_auth import (
    Token,
    UserCreate,
    UserResponse,
    LoginRequest,
    authenticate_user,
    create_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_active_user,
    require_admin,
)
from mongodb.api.config.settings import settings
from pydantic import BaseModel
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user.
    
    - **username**: Unique username
    - **email**: Optional email address
    - **password**: Password (will be hashed)
    - **full_name**: Optional full name
    """
    try:
        user = await create_user(user_data)
        return UserResponse(
            id=str(user["_id"]),
            username=user["username"],
            email=user.get("email"),
            full_name=user.get("full_name"),
            role=user["role"],
            is_active=user["is_active"],
            created_at=user["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """
    Login with username and password.
    
    Returns access token and refresh token.
    """
    user = await authenticate_user(login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user["username"]}
    )
    
    logger.info(f"User logged in: {user['username']}")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    """
    try:
        payload = decode_token(request.refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        username = payload.get("sub")
        
        # Create new tokens
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": username},
            expires_delta=access_token_expires
        )
        new_refresh_token = create_refresh_token(
            data={"sub": username}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Get current authenticated user information.
    """
    return UserResponse(
        id=str(current_user["_id"]),
        username=current_user["username"],
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        role=current_user["role"],
        is_active=current_user["is_active"],
        created_at=current_user["created_at"]
    )


@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Logout current user.
    
    Note: In a stateless JWT system, the client should discard the token.
    For true logout, implement token blacklisting with Redis.
    """
    logger.info(f"User logged out: {current_user['username']}")
    return {"message": "Successfully logged out"}
