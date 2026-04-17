"""Ensure demo doctor users + profiles exist (local Docker / dev).

Full demo seed lives in ``wsgi._seed_all_demo_data`` when the DB is completely empty.
This helper runs when there are **no doctor users** yet so ``GET /doctors`` and booking
still work even if the full seed did not run (e.g. partial DB or skipped wsgi import).
"""

from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy import text

from app.extensions import db
from app.models.doctor import DoctorProfile
from app.models.user import User

logger = logging.getLogger(__name__)

_DEMO_PASSWORD = "Demo1234!"

_DOCTORS_DATA: list[dict] = [
    {
        "email": "doctor@demo.dev",
        "first_name": "Sarah",
        "last_name": "Chen",
        "phone": "+1-555-201-0001",
        "specialization": "Internal Medicine",
        "license_number": "MD-2019-04821",
        "license_state": "CA",
        "years_of_experience": 12,
        "department": "General Medicine",
        "consultation_fee": Decimal("175.00"),
        "bio": "Board-certified internist with expertise in chronic disease management and preventive care.",
    },
    {
        "email": "doctor.cardio@demo.dev",
        "first_name": "James",
        "last_name": "Okonkwo",
        "phone": "+1-555-201-0002",
        "specialization": "Cardiology",
        "license_number": "MD-2015-03194",
        "license_state": "CA",
        "years_of_experience": 18,
        "department": "Cardiology",
        "consultation_fee": Decimal("250.00"),
        "bio": "Fellowship-trained cardiologist specializing in heart failure and electrophysiology.",
    },
    {
        "email": "doctor.neuro@demo.dev",
        "first_name": "Maria",
        "last_name": "Rodriguez",
        "phone": "+1-555-201-0003",
        "specialization": "Neurology",
        "license_number": "MD-2017-05673",
        "license_state": "CA",
        "years_of_experience": 14,
        "department": "Neurology",
        "consultation_fee": Decimal("225.00"),
        "bio": "Neurologist with a focus on headache medicine, epilepsy, and neurodegenerative disorders.",
    },
]

_AVAILABILITY = {
    "monday": ["09:00-12:00", "14:00-17:00"],
    "tuesday": ["09:00-12:00", "14:00-17:00"],
    "wednesday": ["09:00-12:00"],
    "thursday": ["09:00-12:00", "14:00-17:00"],
    "friday": ["09:00-12:00", "14:00-16:00"],
}


def ensure_demo_doctors_exist() -> None:
    """Create the three standard demo doctors if there are no doctor users."""
    pg_lock_acquired = False
    try:
        got_lock = db.session.execute(text("SELECT pg_try_advisory_lock(99123)")).scalar()
        pg_lock_acquired = True
    except Exception:
        # SQLite / non-PostgreSQL test DB — no advisory locks.
        got_lock = True

    if got_lock is not True:
        return

    try:
        count = db.session.query(User).filter(User.role == "doctor").count()
        if count > 0:
            return

        logger.info("No doctor users found — creating demo doctors (doctor@demo.dev, etc.)")
        for dd in _DOCTORS_DATA:
            if User.query.filter_by(email=dd["email"]).first():
                continue
            u = User(
                email=dd["email"],
                first_name=dd["first_name"],
                last_name=dd["last_name"],
                role="doctor",
                phone=dd["phone"],
                is_active=True,
                is_verified=True,
            )
            u.set_password(_DEMO_PASSWORD)
            db.session.add(u)
            db.session.flush()

            dp = DoctorProfile(
                user_id=u.id,
                specialization=dd["specialization"],
                license_number=dd["license_number"],
                license_state=dd["license_state"],
                years_of_experience=dd["years_of_experience"],
                department=dd["department"],
                consultation_fee=dd["consultation_fee"],
                bio=dd["bio"],
                availability=_AVAILABILITY,
            )
            db.session.add(dp)

        db.session.commit()
        logger.info("Demo doctors ensured (password: %s)", _DEMO_PASSWORD)
    finally:
        if pg_lock_acquired:
            try:
                db.session.execute(text("SELECT pg_advisory_unlock(99123)"))
                db.session.commit()
            except Exception:
                db.session.rollback()
