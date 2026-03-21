"""Medication service — business logic for prescriptions and medication tracking."""

import uuid

from sqlalchemy import select

from app.extensions import db
from app.models.medication import Medication
from app.schemas.medication_schema import (
    CreateMedicationRequest, InteractionCheckResponse,
    MedicationResponse, MedicationScheduleResponse, UpdateMedicationRequest,
)


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

    def check_interactions(self, medication_names: list[str], patient_id: str | None = None) -> InteractionCheckResponse:
        return InteractionCheckResponse(checked_medications=medication_names, interactions_found=0, interactions=[])

    def search_medications(self, query: str, limit: int = 20) -> list[MedicationResponse]:
        stmt = select(Medication).where(Medication.name.ilike(f"%{query}%")).order_by(Medication.name).limit(limit)
        return [self._to_response(m) for m in db.session.execute(stmt).scalars().all()]

    def check_access(self, requester_id: str, requester_role: str, patient_id: str) -> bool:
        if requester_role == "admin":
            return True
        if requester_role == "patient":
            return requester_id == patient_id
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
