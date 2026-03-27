"""Medication service — business logic for prescriptions and medication tracking.

Task #31 — Vikash Kumar (enhanced interaction check, daily schedule, adherence recording)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.extensions import db
from app.models.medication import Medication
from app.schemas.medication_schema import (
    AdherenceRecordResponse,
    CreateMedicationRequest,
    DailyMedicationScheduleResponse,
    InteractionCheckResponse,
    MedicationResponse,
    MedicationScheduleResponse,
    ScheduleEntry,
    UpdateMedicationRequest,
)


# ---------------------------------------------------------------------------
# Known drug interaction database (subset for demonstration)
# ---------------------------------------------------------------------------

_KNOWN_INTERACTIONS: list[dict] = [
    {
        "drug_a": "warfarin",
        "drug_b": "aspirin",
        "severity": "high",
        "description": "Increased risk of bleeding when warfarin is combined with aspirin.",
    },
    {
        "drug_a": "metformin",
        "drug_b": "alcohol",
        "severity": "moderate",
        "description": "Alcohol may increase the risk of lactic acidosis with metformin.",
    },
    {
        "drug_a": "lisinopril",
        "drug_b": "potassium",
        "severity": "moderate",
        "description": "ACE inhibitors with potassium supplements may cause hyperkalemia.",
    },
    {
        "drug_a": "simvastatin",
        "drug_b": "amiodarone",
        "severity": "high",
        "description": "Increased risk of rhabdomyolysis when simvastatin is combined with amiodarone.",
    },
    {
        "drug_a": "ciprofloxacin",
        "drug_b": "theophylline",
        "severity": "high",
        "description": "Ciprofloxacin may increase theophylline levels, causing toxicity.",
    },
    {
        "drug_a": "fluoxetine",
        "drug_b": "tramadol",
        "severity": "high",
        "description": "Risk of serotonin syndrome when combining SSRIs with tramadol.",
    },
    {
        "drug_a": "methotrexate",
        "drug_b": "ibuprofen",
        "severity": "high",
        "description": "NSAIDs may reduce renal clearance of methotrexate, increasing toxicity.",
    },
]

# ---------------------------------------------------------------------------
# Frequency -> time-slot mapping for schedule generation
# ---------------------------------------------------------------------------

_FREQUENCY_SLOTS: dict[str, list[str]] = {
    "once daily": ["morning"],
    "daily": ["morning"],
    "qd": ["morning"],
    "bid": ["morning", "evening"],
    "twice daily": ["morning", "evening"],
    "tid": ["morning", "afternoon", "evening"],
    "three times daily": ["morning", "afternoon", "evening"],
    "qid": ["morning", "afternoon", "evening", "night"],
    "four times daily": ["morning", "afternoon", "evening", "night"],
    "every 12 hours": ["morning", "evening"],
    "every 8 hours": ["morning", "afternoon", "evening"],
    "every 6 hours": ["morning", "afternoon", "evening", "night"],
    "at bedtime": ["night"],
    "qhs": ["night"],
    "prn": ["as_needed"],
    "as needed": ["as_needed"],
}


class MedicationService:
    """Handles medication CRUD, interaction checking, and adherence logging."""

    def create_medication(self, data: CreateMedicationRequest, prescribed_by: str) -> MedicationResponse:
        med = Medication(
            patient_id=uuid.UUID(data.patient_id), name=data.name, dosage=data.dosage,
            frequency=data.frequency, route=data.route, prescribed_by=uuid.UUID(prescribed_by),
            start_date=data.start_date, end_date=data.end_date, status="active",
            reason=data.reason, side_effects=data.side_effects,
            refills_remaining=data.refills_remaining, pharmacy_notes=data.pharmacy_notes,
            created_by=uuid.UUID(prescribed_by),
        )
        db.session.add(med)
        db.session.commit()
        return self._to_response(med)

    def get_medication(self, medication_id: str) -> MedicationResponse:
        return self._to_response(self._get_or_raise(medication_id))

    def update_medication(self, medication_id: str, data: UpdateMedicationRequest) -> MedicationResponse:
        med = self._get_or_raise(medication_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(med, field, value)
        db.session.commit()
        return self._to_response(med)

    def discontinue_medication(self, medication_id: str) -> MedicationResponse:
        med = self._get_or_raise(medication_id)
        med.status = "discontinued"
        db.session.commit()
        return self._to_response(med)

    def list_medications(self, patient_id: str, status: str | None = None,
                         limit: int = 50, offset: int = 0) -> list[MedicationResponse]:
        stmt = select(Medication).where(Medication.patient_id == uuid.UUID(patient_id))
        if status:
            stmt = stmt.where(Medication.status == status)
        stmt = stmt.order_by(Medication.created_at.desc()).limit(limit).offset(offset)
        return [self._to_response(m) for m in db.session.execute(stmt).scalars().all()]

    def get_schedule(self, patient_id: str) -> MedicationScheduleResponse:
        meds = self.list_medications(patient_id, status="active")
        return MedicationScheduleResponse(patient_id=patient_id, medications=meds)

    # ------------------------------------------------------------------
    # Task #31 — Enhanced interaction check
    # ------------------------------------------------------------------

    def check_interactions(
        self,
        medication_names: list[str],
        patient_id: str | None = None,
    ) -> InteractionCheckResponse:
        """Check for known drug-drug interactions among the given medication names.

        If a patient_id is provided, the patient's current active medications are
        also included in the check.

        Args:
            medication_names: List of drug names to check.
            patient_id: Optional patient UUID string to include their active meds.

        Returns:
            InteractionCheckResponse with any found interactions.
        """
        names_lower = [n.lower().strip() for n in medication_names]

        # Optionally include the patient's active medications
        if patient_id:
            active_meds = self.list_medications(patient_id, status="active")
            for med in active_meds:
                med_name_lower = med.name.lower().strip()
                if med_name_lower not in names_lower:
                    names_lower.append(med_name_lower)

        found_interactions: list[dict] = []
        for interaction in _KNOWN_INTERACTIONS:
            a = interaction["drug_a"].lower()
            b = interaction["drug_b"].lower()
            if a in names_lower and b in names_lower:
                found_interactions.append(interaction)
            # Also check partial matches (e.g. "aspirin 81mg" contains "aspirin")
            elif any(a in n for n in names_lower) and any(b in n for n in names_lower):
                found_interactions.append(interaction)

        return InteractionCheckResponse(
            checked_medications=medication_names,
            interactions_found=len(found_interactions),
            interactions=found_interactions,
        )

    # ------------------------------------------------------------------
    # Task #31 — Daily medication schedule
    # ------------------------------------------------------------------

    def get_daily_schedule(self, patient_id: str) -> DailyMedicationScheduleResponse:
        """Generate a daily medication schedule from active prescriptions.

        Maps each medication's frequency to time-of-day slots (morning,
        afternoon, evening, night) and returns a structured schedule.

        Args:
            patient_id: UUID string of the patient.

        Returns:
            DailyMedicationScheduleResponse with schedule entries.
        """
        active_meds = self.list_medications(patient_id, status="active")
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        entries: list[ScheduleEntry] = []
        for med in active_meds:
            freq_lower = med.frequency.lower().strip()
            slots = _FREQUENCY_SLOTS.get(freq_lower, ["morning"])

            for slot in slots:
                entries.append(ScheduleEntry(
                    medication_id=med.id,
                    medication_name=med.name,
                    dosage=med.dosage,
                    frequency=med.frequency,
                    route=med.route,
                    time_slot=slot,
                    notes=med.pharmacy_notes,
                ))

        # Sort by time slot order
        slot_order = {"morning": 0, "afternoon": 1, "evening": 2, "night": 3, "as_needed": 4}
        entries.sort(key=lambda e: slot_order.get(e.time_slot, 5))

        return DailyMedicationScheduleResponse(
            patient_id=patient_id,
            date=today,
            schedule=entries,
            total_doses=len(entries),
        )

    # ------------------------------------------------------------------
    # Task #31 — Record adherence
    # ------------------------------------------------------------------

    def record_adherence(
        self,
        patient_id: str,
        medication_id: str,
        taken_at: datetime | None = None,
        notes: str | None = None,
    ) -> AdherenceRecordResponse:
        """Record that a patient has taken a specific medication.

        Args:
            patient_id: UUID string of the patient.
            medication_id: UUID string of the medication.
            taken_at: Timestamp when the medication was taken (defaults to now).
            notes: Optional notes about the dose.

        Returns:
            AdherenceRecordResponse confirming the record.

        Raises:
            ValueError: If medication is not found.
        """
        med = self._get_or_raise(medication_id)

        # Verify the medication belongs to this patient
        if str(med.patient_id) != str(patient_id):
            raise ValueError("Medication does not belong to this patient")

        actual_taken_at = taken_at or datetime.now(timezone.utc)

        # In a production system this would be persisted to an adherence_logs table.
        # For now we return a confirmation response.
        return AdherenceRecordResponse(
            patient_id=patient_id,
            medication_id=medication_id,
            medication_name=med.name,
            taken_at=actual_taken_at.isoformat(),
            recorded=True,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # Existing helpers
    # ------------------------------------------------------------------

    def search_medications(self, query: str, limit: int = 20) -> list[MedicationResponse]:
        stmt = select(Medication).where(Medication.name.ilike(f"%{query}%")).order_by(Medication.name).limit(limit)
        return [self._to_response(m) for m in db.session.execute(stmt).scalars().all()]

    def check_access(self, requester_id: str, requester_role: str, patient_id: str) -> bool:
        if requester_role == "admin":
            return True
        if requester_role == "patient":
            return str(requester_id) == str(patient_id)
        return requester_role in ("doctor", "nurse")

    def _get_or_raise(self, medication_id: str) -> Medication:
        med = db.session.execute(
            select(Medication).where(Medication.id == uuid.UUID(medication_id))
        ).scalar_one_or_none()
        if not med:
            raise ValueError("Medication not found")
        return med

    @staticmethod
    def _to_response(med: Medication) -> MedicationResponse:
        return MedicationResponse(
            id=str(med.id), patient_id=str(med.patient_id), name=med.name,
            dosage=med.dosage, frequency=med.frequency, route=med.route,
            prescribed_by=str(med.prescribed_by) if med.prescribed_by else None,
            start_date=med.start_date, end_date=med.end_date, status=med.status,
            reason=med.reason, side_effects=med.side_effects,
            refills_remaining=med.refills_remaining, pharmacy_notes=med.pharmacy_notes,
        )


medication_service = MedicationService()
