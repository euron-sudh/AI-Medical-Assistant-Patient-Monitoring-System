"""WSGI entry point for MedAssist AI backend."""

import os

from app import create_app
from app.extensions import db

app = create_app()

# Auto-create tables on startup (needed for Render free tier — no shell access)
with app.app_context():
    db.create_all()

    # Auto-seed demo data if DB is empty
    from app.models.user import User
    if User.query.count() == 0:
        print("Empty database detected — seeding demo data...")
        try:
            # Create 3 test users (emails must match the login form test credentials)
            for email, fname, lname, role in [
                ("patient@demo.dev", "Demo", "Patient", "patient"),
                ("doctor@demo.dev", "Dr. Demo", "Doctor", "doctor"),
                ("admin@demo.dev", "Demo", "Admin", "admin"),
            ]:
                u = User(
                    email=email,
                    first_name=fname,
                    last_name=lname,
                    role=role,
                    is_active=True,
                    is_verified=True,
                )
                u.set_password("Demo1234!")
                db.session.add(u)
            db.session.commit()
            print(f"Seeded {User.query.count()} test users")
        except Exception as e:
            db.session.rollback()
            print(f"Seed error (non-fatal): {e}")

if __name__ == "__main__":
    app.run()
