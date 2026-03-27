"""Auth service — business logic for authentication and authorization."""

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import requests
from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy import select

from app.extensions import db
from app.models.user import User
from app.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse, UserResponse


@dataclass
class GoogleUser:
    """Verified Google user data from ID token."""
    email: str
    first_name: str
    last_name: str
    picture: str | None = None
    google_id: str | None = None


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

    def verify_google_token(self, id_token: str) -> GoogleUser:
        """Verify a Google ID token and extract user info.

        Uses Google's tokeninfo endpoint for verification.

        Args:
            id_token: The Google ID token from frontend Sign-In.

        Returns:
            GoogleUser with verified email and name.

        Raises:
            ValueError: If the token is invalid or verification fails.
        """
        try:
            # Verify with Google's tokeninfo endpoint
            resp = requests.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}",
                timeout=10,
            )
            if resp.status_code != 200:
                raise ValueError("Invalid Google token")

            data = resp.json()

            # Verify the token is for our app (if client ID is configured)
            google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
            if google_client_id and data.get("aud") != google_client_id:
                raise ValueError("Token was not issued for this application")

            if not data.get("email_verified", "false") == "true":
                raise ValueError("Google email is not verified")

            return GoogleUser(
                email=data["email"],
                first_name=data.get("given_name", data.get("email", "").split("@")[0]),
                last_name=data.get("family_name", ""),
                picture=data.get("picture"),
                google_id=data.get("sub"),
            )

        except requests.RequestException as e:
            raise ValueError(f"Failed to verify Google token: {str(e)}")

    def login_or_register_google(self, google_user: GoogleUser) -> TokenResponse:
        """Login an existing user or create a new one from Google OAuth.

        Args:
            google_user: Verified Google user data.

        Returns:
            TokenResponse with JWT tokens and user profile.
        """
        stmt = select(User).where(User.email == google_user.email)
        user = db.session.execute(stmt).scalar_one_or_none()

        if not user:
            # Auto-register as patient
            user = User(
                email=google_user.email,
                first_name=google_user.first_name,
                last_name=google_user.last_name,
                role="patient",
                is_active=True,
                is_verified=True,  # Google email is already verified
                avatar_url=google_user.picture,
            )
            # Set a random password (user logs in via Google, not password)
            user.set_password(uuid.uuid4().hex)
            db.session.add(user)
            db.session.commit()

        if not user.is_active:
            raise ValueError("Account is deactivated")

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        if google_user.picture and not user.avatar_url:
            user.avatar_url = google_user.picture
        db.session.commit()

        additional_claims = {"role": user.role}
        access_token = create_access_token(
            identity=str(user.id), additional_claims=additional_claims,
        )
        refresh_token = create_refresh_token(
            identity=str(user.id), additional_claims=additional_claims,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(
                id=str(user.id), email=user.email,
                first_name=user.first_name, last_name=user.last_name,
                role=user.role, is_active=user.is_active, is_verified=user.is_verified,
            ),
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
