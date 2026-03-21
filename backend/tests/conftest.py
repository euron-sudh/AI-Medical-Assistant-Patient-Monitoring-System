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
def auth_headers(client, sample_user):
    """Get JWT auth headers for the sample patient user."""
    response = client.post("/api/v1/auth/login", json={
        "email": "patient@test.com",
        "password": "securepass123",
    })
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
