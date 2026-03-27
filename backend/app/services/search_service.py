"""Search service — business logic for cross-entity search using PostgreSQL ILIKE."""

import uuid

from sqlalchemy import select, or_

from app.extensions import db
from app.models.medication import Medication
from app.models.patient import MedicalHistory, PatientProfile
from app.models.user import User


class SearchService:
    """Handles search across patients, medications, and conditions."""

    def search(
        self, query: str, search_type: str = "all", limit: int = 20, offset: int = 0
    ) -> dict:
        """Execute a search across the specified entity types.

        Args:
            query: Search term to match against.
            search_type: One of 'patients', 'medications', 'conditions', or 'all'.
            limit: Maximum results per category.
            offset: Number of results to skip per category.

        Returns:
            Dict with results keyed by entity type.
        """
        results = {}
        pattern = f"%{query}%"

        if search_type in ("patients", "all"):
            results["patients"] = self._search_patients(pattern, limit, offset)

        if search_type in ("medications", "all"):
            results["medications"] = self._search_medications(pattern, limit, offset)

        if search_type in ("conditions", "all"):
            results["conditions"] = self._search_conditions(pattern, limit, offset)

        return results

    def _search_patients(self, pattern: str, limit: int, offset: int) -> list[dict]:
        """Search patients by name or email using ILIKE.

        Args:
            pattern: ILIKE pattern string.
            limit: Maximum results.
            offset: Results to skip.

        Returns:
            List of matching patient dicts.
        """
        stmt = (
            select(User, PatientProfile)
            .outerjoin(PatientProfile, PatientProfile.user_id == User.id)
            .where(
                User.role == "patient",
                or_(
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                    User.email.ilike(pattern),
                    (User.first_name + " " + User.last_name).ilike(pattern),
                ),
            )
            .order_by(User.last_name, User.first_name)
            .limit(limit)
            .offset(offset)
        )

        rows = db.session.execute(stmt).all()
        results = []
        for user, profile in rows:
            results.append({
                "id": str(user.id),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "date_of_birth": profile.date_of_birth.isoformat() if profile and profile.date_of_birth else None,
                "gender": profile.gender if profile else None,
                "blood_type": profile.blood_type if profile else None,
            })
        return results

    def _search_medications(self, pattern: str, limit: int, offset: int) -> list[dict]:
        """Search medications by drug name using ILIKE.

        Args:
            pattern: ILIKE pattern string.
            limit: Maximum results.
            offset: Results to skip.

        Returns:
            List of matching medication dicts.
        """
        stmt = (
            select(Medication)
            .where(Medication.name.ilike(pattern))
            .order_by(Medication.name)
            .limit(limit)
            .offset(offset)
        )

        medications = db.session.execute(stmt).scalars().all()
        results = []
        for m in medications:
            results.append({
                "id": str(m.id),
                "name": m.name,
                "dosage": m.dosage,
                "frequency": m.frequency,
                "status": m.status,
                "patient_id": str(m.patient_id),
                "start_date": m.start_date.isoformat() if m.start_date else None,
            })
        return results

    def _search_conditions(self, pattern: str, limit: int, offset: int) -> list[dict]:
        """Search medical history condition names using ILIKE.

        Args:
            pattern: ILIKE pattern string.
            limit: Maximum results.
            offset: Results to skip.

        Returns:
            List of matching condition dicts.
        """
        stmt = (
            select(MedicalHistory)
            .where(MedicalHistory.condition_name.ilike(pattern))
            .order_by(MedicalHistory.condition_name)
            .limit(limit)
            .offset(offset)
        )

        entries = db.session.execute(stmt).scalars().all()
        results = []
        for e in entries:
            results.append({
                "id": str(e.id),
                "condition_name": e.condition_name,
                "status": e.status,
                "icd_10_code": e.icd_10_code,
                "diagnosis_date": e.diagnosis_date.isoformat() if e.diagnosis_date else None,
                "patient_id": str(e.patient_id),
            })
        return results


# Module-level instance for use by routes
search_service = SearchService()
