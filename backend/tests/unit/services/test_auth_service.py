"""Unit tests for the auth service — registration, login, token refresh."""

import pytest

from app.schemas.auth_schema import RegisterRequest, LoginRequest
from app.services.auth_service import AuthService


class TestAuthServiceRegister:
    """Tests for user registration."""

    def test_register_new_patient(self, db):
        """Registering a new patient creates user and returns profile."""
        service = AuthService()
        data = RegisterRequest(
            email="newpatient@test.com",
            password="securepass123",
            first_name="New",
            last_name="Patient",
            role="patient",
        )
        result = service.register(data)

        assert result.email == "newpatient@test.com"
        assert result.first_name == "New"
        assert result.role == "patient"
        assert result.is_active is True
        assert result.is_verified is False

    def test_register_new_doctor_rejected(self, db):
        """Public self-registration MUST NOT allow elevated roles.

        The public /register endpoint is restricted to ``role='patient'`` to
        prevent privilege escalation via unauthenticated signup. Doctor and
        admin accounts must be provisioned through the admin panel.
        """
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            RegisterRequest(
                email="newdoctor@test.com",
                password="securepass123",
                first_name="New",
                last_name="Doctor",
                role="doctor",
            )

    def test_register_duplicate_email_raises(self, db, sample_user):
        """Registering with an existing email raises ValueError."""
        service = AuthService()
        data = RegisterRequest(
            email="patient@test.com",  # same as sample_user
            password="securepass123",
            first_name="Duplicate",
            last_name="User",
            role="patient",
        )

        with pytest.raises(ValueError, match="Email already registered"):
            service.register(data)


class TestAuthServiceLogin:
    """Tests for user login."""

    def test_login_valid_credentials(self, db, sample_user):
        """Login with correct credentials returns tokens."""
        service = AuthService()
        data = LoginRequest(email="patient@test.com", password="securepass123")
        result = service.login(data)

        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"
        assert result.user.email == "patient@test.com"

    def test_login_wrong_password(self, db, sample_user):
        """Login with wrong password raises ValueError."""
        service = AuthService()
        data = LoginRequest(email="patient@test.com", password="wrongpassword")

        with pytest.raises(ValueError, match="Invalid email or password"):
            service.login(data)

    def test_login_nonexistent_email(self, db):
        """Login with unregistered email raises ValueError."""
        service = AuthService()
        data = LoginRequest(email="nobody@test.com", password="securepass123")

        with pytest.raises(ValueError, match="Invalid email or password"):
            service.login(data)

    def test_login_inactive_user(self, db, sample_user):
        """Login with deactivated account raises ValueError."""
        sample_user.is_active = False
        db.session.commit()

        service = AuthService()
        data = LoginRequest(email="patient@test.com", password="securepass123")

        with pytest.raises(ValueError, match="Account is deactivated"):
            service.login(data)


class TestAuthServiceGetUser:
    """Tests for get current user."""

    def test_get_current_user(self, db, sample_user):
        """Getting current user returns correct profile."""
        service = AuthService()
        result = service.get_current_user(str(sample_user.id))

        assert result.email == "patient@test.com"
        assert result.role == "patient"

    def test_get_nonexistent_user(self, db):
        """Getting non-existent user raises ValueError."""
        service = AuthService()

        with pytest.raises(ValueError, match="User not found"):
            service.get_current_user("00000000-0000-0000-0000-000000000000")
