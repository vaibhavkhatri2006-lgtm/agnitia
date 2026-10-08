from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse, RoleVerificationResponse
from app.schemas.errors import HTTPErrorResponse
from app.services.auth_service import auth_service
from app.dependencies.auth import (
    get_current_user,
    require_active_user,
    require_role,
    require_permission,
)

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue JWT access token",
    responses={
        401: {"model": HTTPErrorResponse, "description": "Invalid credentials"},
        403: {"model": HTTPErrorResponse, "description": "Inactive account"},
    },
)
def login(
    login_req: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticates a user via email/username and password.
    Returns a signed JWT bearer token and user profile including server-validated role and permissions.
    """
    return auth_service.login(db, login_req)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated user profile and permissions",
    responses={
        401: {"model": HTTPErrorResponse, "description": "Unauthenticated or invalid token"},
        403: {"model": HTTPErrorResponse, "description": "Account disabled"},
    },
)
def get_me(
    current_user: User = Depends(require_active_user),
):
    """
    Retrieves the identity, role, and permission claims of the authenticated user.
    Server-side identity is verified from the decoded JWT.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        display_name=current_user.display_name,
        role=current_user.role_name,
        permissions=current_user.permission_codes,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.get(
    "/verify-role/authority",
    response_model=RoleVerificationResponse,
    summary="Protected endpoint requiring 'authority' or 'admin' role",
    responses={
        401: {"model": HTTPErrorResponse, "description": "Unauthenticated"},
        403: {"model": HTTPErrorResponse, "description": "Forbidden - Role not authorized"},
    },
)
def verify_authority_role(
    current_user: User = Depends(require_role("authority", "admin")),
):
    """
    Verifies that the caller has planner or official authority privileges.
    Citizens and community members are rejected with 403 Forbidden.
    """
    return RoleVerificationResponse(
        status="authorized",
        message=f"Access granted for official authority operation to user '{current_user.email}'",
        role=current_user.role_name,
        user_id=current_user.id,
        user_email=current_user.email,
        granted_permissions=current_user.permission_codes,
    )


@router.get(
    "/verify-role/admin",
    response_model=RoleVerificationResponse,
    summary="Protected endpoint requiring 'admin' role",
    responses={
        401: {"model": HTTPErrorResponse, "description": "Unauthenticated"},
        403: {"model": HTTPErrorResponse, "description": "Forbidden - Role not authorized"},
    },
)
def verify_admin_role(
    current_user: User = Depends(require_role("admin")),
):
    """
    Verifies that the caller has system administration privileges.
    Non-admin roles are rejected with 403 Forbidden.
    """
    return RoleVerificationResponse(
        status="authorized",
        message=f"Access granted for system administrative operation to user '{current_user.email}'",
        role=current_user.role_name,
        user_id=current_user.id,
        user_email=current_user.email,
        granted_permissions=current_user.permission_codes,
    )


@router.get(
    "/verify-role/community",
    response_model=RoleVerificationResponse,
    summary="Protected endpoint requiring 'community', 'authority', or 'admin' role",
    responses={
        401: {"model": HTTPErrorResponse, "description": "Unauthenticated"},
        403: {"model": HTTPErrorResponse, "description": "Forbidden - Role not authorized"},
    },
)
def verify_community_role(
    current_user: User = Depends(require_role("community", "authority", "admin")),
):
    """
    Verifies that the caller has community verifier privileges.
    Standard citizens are rejected with 403 Forbidden.
    """
    return RoleVerificationResponse(
        status="authorized",
        message=f"Access granted for community verification operation to user '{current_user.email}'",
        role=current_user.role_name,
        user_id=current_user.id,
        user_email=current_user.email,
        granted_permissions=current_user.permission_codes,
    )
