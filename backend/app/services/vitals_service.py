"""Vitals service — business logic for vitals readings and history."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.extensions import db
from app.models.vitals import VitalsReading
from app.schemas.vitals_schema import CreateVitalsRequest, VitalsResponse


class VitalsService:
    """Handles creating, querying, and managing patient vitals readings."""

    def create_reading(
        self, patient_id: uuid.UUID, data: CreateVitalsRequest, created_by: uuid.UUID
    ) -> VitalsResponse:
        """Create a new vitals reading for a patient.

        Args:
            patient_id: UUID of the patient.
            data: Validated vitals data.
            created_by: UUID of the user creating the reading.

        Returns:
            VitalsResponse with the created reading.
        """
        reading = VitalsReading(
            patient_id=patient_id,
            heart_rate=data.heart_rate,
            blood_pressure_systolic=data.blood_pressure_systolic,
            blood_pressure_diastolic=data.blood_pressure_diastolic,
            temperature=data.temperature,
            oxygen_saturation=data.oxygen_saturation,
            respiratory_rate=data.respiratory_rate,
            blood_glucose=data.blood_glucose,
            weight_kg=data.weight_kg,
            pain_level=data.pain_level,
            device_id=uuid.UUID(data.device_id) if data.device_id else None,
            is_manual_entry=data.is_manual_entry,
            notes=data.notes,
            recorded_at=data.recorded_at or datetime.now(timezone.utc),
            created_by=created_by,
        )

        db.session.add(reading)
        db.session.commit()

        return self._to_response(reading)

    def get_patient_vitals(
        self, patient_id: uuid.UUID, limit: int = 100
    ) -> list[VitalsResponse]:
        """Get the most recent vitals readings for a patient.

        Args:
            patient_id: UUID of the patient.
            limit: Maximum number of readings to return.

        Returns:
            List of VitalsResponse ordered by recorded_at descending.
        """
        stmt = (
            select(VitalsReading)
            .where(VitalsReading.patient_id == patient_id)
            .order_by(VitalsReading.recorded_at.desc())
            .limit(limit)
        )
        readings = db.session.execute(stmt).scalars().all()
        return [self._to_response(r) for r in readings]

    def get_vitals_history(
        self,
        patient_id: uuid.UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[VitalsResponse]:
        """Get vitals history for a patient within a time range.

        Args:
            patient_id: UUID of the patient.
            start_date: Start of time range (inclusive).
            end_date: End of time range (inclusive).
            limit: Maximum number of readings to return.
            offset: Number of readings to skip.

        Returns:
            List of VitalsResponse within the time range.
        """
        stmt = (
            select(VitalsReading)
            .where(VitalsReading.patient_id == patient_id)
        )

        if start_date:
            stmt = stmt.where(VitalsReading.recorded_at >= start_date)
        if end_date:
            stmt = stmt.where(VitalsReading.recorded_at <= end_date)

        stmt = (
            stmt.order_by(VitalsReading.recorded_at.desc())
            .offset(offset)
            .limit(limit)
        )

        readings = db.session.execute(stmt).scalars().all()
        return [self._to_response(r) for r in readings]

    def _to_response(self, reading: VitalsReading) -> VitalsResponse:
        """Convert a VitalsReading model to a VitalsResponse schema."""
        return VitalsResponse(
            id=str(reading.id),
            patient_id=str(reading.patient_id),
            heart_rate=reading.heart_rate,
            blood_pressure_systolic=reading.blood_pressure_systolic,
            blood_pressure_diastolic=reading.blood_pressure_diastolic,
            temperature=float(reading.temperature) if reading.temperature else None,
            oxygen_saturation=float(reading.oxygen_saturation) if reading.oxygen_saturation else None,
            respiratory_rate=reading.respiratory_rate,
            blood_glucose=float(reading.blood_glucose) if reading.blood_glucose else None,
            weight_kg=float(reading.weight_kg) if reading.weight_kg else None,
            pain_level=reading.pain_level,
            device_id=str(reading.device_id) if reading.device_id else None,
            is_manual_entry=reading.is_manual_entry,
            is_anomalous=reading.is_anomalous,
            notes=reading.notes,
            recorded_at=reading.recorded_at,
            created_at=reading.created_at,
        )


# Module-level instance for use by routes
vitals_service = VitalsService()
