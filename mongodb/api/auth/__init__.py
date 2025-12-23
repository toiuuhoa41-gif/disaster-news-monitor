"""
Authentication Module
"""

from mongodb.api.auth.jwt_auth import (
    Token,
    TokenData,
    UserCreate,
    UserResponse,
    LoginRequest,
    create_access_token,
    create_refresh_token,
    decode_token,
    authenticate_user,
    create_user,
    get_current_user,
    get_current_active_user,
    get_optional_user,
    require_role,
    require_admin,
    require_crawler,
    verify_password,
    get_password_hash,
)

__all__ = [
    "Token",
    "TokenData",
    "UserCreate",
    "UserResponse",
    "LoginRequest",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "authenticate_user",
    "create_user",
    "get_current_user",
    "get_current_active_user",
    "get_optional_user",
    "require_role",
    "require_admin",
    "require_crawler",
    "verify_password",
    "get_password_hash",
]
