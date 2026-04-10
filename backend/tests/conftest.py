"""Shared test fixtures for backend tests."""

import pytest

from app import create_app
from app.extensions import db as _db
from app.models.user import User


@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    app = create_app("testing")
    return app


@pytest.fixture(scope="function")
def db(app):
    """Create fresh database tables for each test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture
def client(app, db):
    """Flask test client with database."""
    return app.test_client()


@pytest.fixture
def sample_user(db):
    """Create a sample patient user."""
    user = User(
        email="patient@test.com",
        first_name="Test",
        last_name="Patient",
        role="patient",
    )
    user.set_password("securepass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_doctor(db):
    """Create a sample doctor user."""
    user = User(
        email="doctor@test.com",
        first_name="Dr. Test",
        last_name="Doctor",
        role="doctor",
    )
    user.set_password("securepass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def auth_headers(client, db):
    """JWT auth headers keyed by role.

    Creates one user per role (patient, doctor, nurse, admin), logs each in,
    and returns a mapping::

        {
            "patient": {"Authorization": "Bearer ..."},
            "doctor":  {"Authorization": "Bearer ..."},
            "nurse":   {"Authorization": "Bearer ..."},
            "admin":   {"Authorization": "Bearer ..."},
        }

    Tests that want a single header can do ``auth_headers["patient"]``.
    """
    roles = [
        ("patient", "patient@test.com", "Test", "Patient"),
        ("doctor", "doctor@test.com", "Dr. Test", "Doctor"),
        ("nurse", "nurse@test.com", "Test", "Nurse"),
        ("admin", "admin@test.com", "Test", "Admin"),
    ]

    headers: dict[str, dict[str, str]] = {}
    for role, email, first, last in roles:
        user = User(email=email, first_name=first, last_name=last, role=role)
        user.set_password("securepass123")
        db.session.add(user)
        db.session.commit()

        resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "securepass123"},
        )
        token = resp.get_json()["access_token"]
        headers[role] = {"Authorization": f"Bearer {token}"}

    return headers
