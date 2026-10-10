from datetime import timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.role import Role
from app.core.security import verify_password, hash_password, create_access_token
from app.schemas.auth import LoginRequest, RegisterRequest, ResetPasswordRequest, TokenResponse, UserResponse
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

    @classmethod
    def register(cls, db: Session, register_req: RegisterRequest) -> TokenResponse:
        """
        Registers a new user in the SQL database, hashes the password with bcrypt,
        assigns the role, and returns an access token with user details.
        """
        import time

        email = register_req.email.strip().lower()
        if not email or "@" not in email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A valid email address is required.",
            )

        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An account with email '{email}' already exists in SQL database. Please log in.",
            )

        # Resolve role (citizen, community, authority, admin)
        role_name = (register_req.role or "citizen").strip().lower()
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = db.query(Role).filter(Role.name == "citizen").first()
            if not role:
                role = Role(name="citizen", description="Standard citizen user")
                db.add(role)
                db.flush()

        username = register_req.username or email.split("@")[0]
        # Ensure username uniqueness
        existing_u = db.query(User).filter(User.username == username).first()
        if existing_u:
            username = f"{username}_{int(time.time())}"

        pwd_hash = hash_password(register_req.password)
        new_user = User(
            email=email,
            username=username,
            password_hash=pwd_hash,
            display_name=register_req.display_name or (email.split("@")[0].title()),
            role_id=role.id,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return cls.create_token_for_user(new_user)

    @classmethod
    def reset_or_sync_password(cls, db: Session, req: ResetPasswordRequest) -> TokenResponse:
        """
        Updates the password for an existing account or creates a new one in the SQL database.
        Securely hashes password with bcrypt, updates role if specified, and issues a JWT token.
        """
        import time

        email = req.email.strip().lower()
        if not email or "@" not in email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A valid email address is required.",
            )

        pwd_hash = hash_password(req.password)
        user = db.query(User).filter(User.email == email).first()

        # Resolve role if specified
        target_role = None
        if req.role:
            role_name = req.role.strip().lower()
            target_role = db.query(Role).filter(Role.name == role_name).first()

        if user:
            user.password_hash = pwd_hash
            user.is_active = True
            if target_role:
                user.role_id = target_role.id
            db.commit()
            db.refresh(user)
            return cls.create_token_for_user(user)

        # User does not exist, create new user
        if not target_role:
            target_role = db.query(Role).filter(Role.name == "citizen").first()
            if not target_role:
                target_role = Role(name="citizen", description="Standard citizen user")
                db.add(target_role)
                db.flush()

        username = email.split("@")[0]
        existing_u = db.query(User).filter(User.username == username).first()
        if existing_u:
            username = f"{username}_{int(time.time())}"

        new_user = User(
            email=email,
            username=username,
            password_hash=pwd_hash,
            display_name=email.split("@")[0].title(),
            role_id=target_role.id,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return cls.create_token_for_user(new_user)


auth_service = AuthService()
