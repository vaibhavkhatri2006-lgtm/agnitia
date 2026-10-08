from typing import List, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt

from app.database import get_db
from app.models.user import User
from app.core.security import decode_access_token

# OAuth2 scheme configured to use /auth/login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extracts and validates the JWT bearer token, fetching the authenticated user from the database.
    Raises 401 UNAUTHORIZED if token is missing, expired, or malformed.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload is missing subject claim",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = int(user_id_str)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Ensures that the authenticated user account is active.
    Raises 403 FORBIDDEN if the user account is disabled.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive or disabled",
        )
    return current_user


def require_role(*allowed_roles: str) -> Callable:
    """
    Enforces server-side Role-Based Access Control (RBAC).
    Verifies that the authenticated user possesses at least one of the specified roles.
    Raises 403 FORBIDDEN if the user's role is not authorized.
    """
    def role_checker(current_user: User = Depends(require_active_user)) -> User:
        user_role = current_user.role_name
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Operation requires one of the following roles: {', '.join(allowed_roles)}. Current role: '{user_role}'",
            )
        return current_user

    return role_checker


def require_permission(*required_permissions: str) -> Callable:
    """
    Enforces server-side Permission-Based Access Control.
    Verifies that the authenticated user possesses all specified permissions.
    Raises 403 FORBIDDEN if any required permission is missing.
    """
    def permission_checker(current_user: User = Depends(require_active_user)) -> User:
        user_permissions = set(current_user.permission_codes)
        missing_permissions = [p for p in required_permissions if p not in user_permissions]
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Missing required permission(s): {', '.join(missing_permissions)}",
            )
        return current_user

    return permission_checker
