"""Auth service — business logic for authentication and authorization."""

import uuid
from datetime import datetime, timezone

from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy import select

from app.extensions import db
from app.models.user import User
from app.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse, UserResponse


class AuthService:
    """Handles registration, login, token management, and password operations."""

    def register(self, data: RegisterRequest) -> UserResponse:
        """Register a new user.

        Args:
            data: Validated registration data.

        Returns:
            UserResponse with the created user's public data.

        Raises:
            ValueError: If email is already registered.
        """
        stmt = select(User).where(User.email == data.email)
        existing = db.session.execute(stmt).scalar_one_or_none()
        if existing:
            raise ValueError("Email already registered")

        user = User(
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            role=data.role,
            phone=data.phone,
        )
        user.set_password(data.password)

        db.session.add(user)
        db.session.commit()

        return UserResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
        )

    def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate user and return JWT tokens.

        Args:
            data: Validated login credentials.

        Returns:
            TokenResponse with access and refresh tokens.

        Raises:
            ValueError: If credentials are invalid or account is deactivated.
        """
        stmt = select(User).where(User.email == data.email)
        user = db.session.execute(stmt).scalar_one_or_none()

        if not user or not user.check_password(data.password):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("Account is deactivated")

        # Update last login timestamp
        user.last_login_at = datetime.now(timezone.utc)
        db.session.commit()

        # Create JWT tokens with role in claims
        additional_claims = {"role": user.role}
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims,
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims=additional_claims,
        )

        user_response = UserResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_response,
        )

    def refresh_tokens(self, user_id: str) -> dict[str, str]:
        """Generate new access token from a valid refresh token.

        Args:
            user_id: UUID string from the refresh token identity.

        Returns:
            Dict with new access_token.

        Raises:
            ValueError: If user not found or inactive.
        """
        stmt = select(User).where(User.id == uuid.UUID(user_id))
        user = db.session.execute(stmt).scalar_one_or_none()

        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        additional_claims = {"role": user.role}
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims,
        )

        return {"access_token": access_token, "token_type": "bearer"}

    def get_current_user(self, user_id: str) -> UserResponse:
        """Get the current authenticated user's profile.

        Args:
            user_id: UUID string from JWT identity.

        Returns:
            UserResponse with user data.

        Raises:
            ValueError: If user not found.
        """
        stmt = select(User).where(User.id == uuid.UUID(user_id))
        user = db.session.execute(stmt).scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        return UserResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
        )

    def change_password(self, user_id: str, current_password: str, new_password: str) -> None:
        """Change a user's password.

        Args:
            user_id: UUID string of the user.
            current_password: The user's current password for verification.
            new_password: The new password to set.

        Raises:
            ValueError: If current password is wrong or user not found.
        """
        stmt = select(User).where(User.id == uuid.UUID(user_id))
        user = db.session.execute(stmt).scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        if not user.check_password(current_password):
            raise ValueError("Current password is incorrect")

        user.set_password(new_password)
        db.session.commit()


# Module-level instance for use by routes
auth_service = AuthService()
