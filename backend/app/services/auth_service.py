from datetime import timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.core.security import verify_password, create_access_token
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.config import settings


class AuthService:
    @staticmethod
    def authenticate_user(db: Session, identifier: str, password: str) -> Optional[User]:
        """
        Validates user credentials against the database.
        Accepts either email or username as the identifier.
        """
        user = db.query(User).filter(
            (User.email == identifier.strip().lower()) | (User.username == identifier.strip())
        ).first()

        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    @staticmethod
    def create_token_for_user(user: User, expires_delta: Optional[timedelta] = None) -> TokenResponse:
        """
        Builds a signed JWT access token and returns TokenResponse schema with user details.
        """
        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role_name,
            permissions=user.permission_codes,
            expires_delta=expires_delta,
        )

        lifespan_seconds = int(
            expires_delta.total_seconds()
            if expires_delta
            else settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

        user_response = UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            display_name=user.display_name,
            role=user.role_name,
            permissions=user.permission_codes,
            is_active=user.is_active,
            created_at=user.created_at,
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=lifespan_seconds,
            user=user_response,
        )

    @classmethod
    def login(cls, db: Session, login_req: LoginRequest) -> TokenResponse:
        """
        Handles user login, verifying active status and issuing a signed JWT token.
        """
        user = cls.authenticate_user(db, login_req.email, login_req.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive. Please contact your administrator.",
            )

        return cls.create_token_for_user(user)


auth_service = AuthService()
