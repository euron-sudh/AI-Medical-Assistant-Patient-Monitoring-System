"""Patient service — business logic for patient profiles, medical history, allergies, timeline, and AI summary."""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select

from app.extensions import db
from app.models.alert import MonitoringAlert
from app.models.appointment import Appointment
from app.models.medication import Medication
from app.models.patient import Allergy, MedicalHistory, PatientProfile
from app.models.report import MedicalReport
from app.models.symptom_session import SymptomSession
from app.models.user import User
from app.models.vitals import VitalsReading
from app.schemas.patient_schema import (
    AddAllergyRequest,
    AddMedicalHistoryRequest,
    AISummaryResponse,
    AllergyResponse,
    CreatePatientProfileRequest,
    MedicalHistoryResponse,
    PatientProfileResponse,
    TimelineEntryResponse,
    UpdateMedicalHistoryStatusRequest,
    UpdatePatientProfileRequest,
)


class PatientService:
    """Handles patient profile CRUD, medical history, allergy operations, timeline, and AI summary."""

    def create_profile(
        self, user_id: str, data: CreatePatientProfileRequest
    ) -> PatientProfileResponse:
        """Create a patient profile linked to a user.

        Args:
            user_id: UUID string of the patient user.
            data: Validated patient profile data.

        Returns:
            PatientProfileResponse with the created profile.

        Raises:
            ValueError: If user not found, not a patient, or profile already exists.
        """
        uid = uuid.UUID(user_id)
        user = db.session.execute(
            select(User).where(User.id == uid)
        ).scalar_one_or_none()

        if not user:
            raise ValueError("User not found")
        if user.role != "patient":
            raise ValueError("Only users with role 'patient' can have a patient profile")

        existing = db.session.execute(
            select(PatientProfile).where(PatientProfile.user_id == uid)
        ).scalar_one_or_none()
        if existing:
            raise ValueError("Patient profile already exists for this user")

        profile = PatientProfile(
            user_id=uid,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            blood_type=data.blood_type,
            height_cm=data.height_cm,
            weight_kg=data.weight_kg,
            emergency_contact=data.emergency_contact,
            insurance_info=data.insurance_info,
        )
        db.session.add(profile)
        db.session.commit()

        return self._to_response(profile)

    def get_profile_by_user_id(self, user_id: str) -> PatientProfileResponse:
        """Get a patient profile by user ID.

        Args:
            user_id: UUID string of the patient user.

        Returns:
            PatientProfileResponse.

        Raises:
            ValueError: If profile not found.
        """
        profile = self._get_profile_or_raise(user_id)
        return self._to_response(profile)

    def update_profile(
        self, user_id: str, data: UpdatePatientProfileRequest
    ) -> PatientProfileResponse:
        """Update a patient profile.

        Args:
            user_id: UUID string of the patient user.
            data: Validated update data (only non-None fields are applied).

        Returns:
            Updated PatientProfileResponse.

        Raises:
            ValueError: If profile not found.
        """
        profile = self._get_profile_or_raise(user_id)

        update_data = data.model_dump(exclude_unset=True)

        # Handle User-level fields separately
        user_fields = {"phone"}
        user_updates = {k: v for k, v in update_data.items() if k in user_fields}
        profile_updates = {k: v for k, v in update_data.items() if k not in user_fields}

        # Update User model fields
        if user_updates:
            user = db.session.get(User, profile.user_id)
            if user:
                for field_name, value in user_updates.items():
                    setattr(user, field_name, value)

        # Update PatientProfile fields
        for field_name, value in profile_updates.items():
            setattr(profile, field_name, value)

        db.session.commit()
        return self._to_response(profile)

    def list_patients(
        self, doctor_id: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[PatientProfileResponse]:
        """List patient profiles.

        Args:
            doctor_id: If provided, filter to patients assigned to this doctor.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of PatientProfileResponse.
        """
        stmt = select(PatientProfile)
        if doctor_id:
            stmt = stmt.where(PatientProfile.assigned_doctor_id == uuid.UUID(doctor_id))
        stmt = stmt.order_by(PatientProfile.created_at.desc()).limit(limit).offset(offset)

        profiles = db.session.execute(stmt).scalars().all()
        return [self._to_response(p) for p in profiles]

    def assign_primary_doctor(self, patient_user_id: str, doctor_user_id: str) -> None:
        """Set ``assigned_doctor_id`` on the patient's profile to this doctor (user ids).

        Intended to run in the same SQLAlchemy session as other writes; does **not** commit.
        No-op if the patient has no ``PatientProfile`` row yet.
        """
        try:
            uid = uuid.UUID(patient_user_id)
            did = uuid.UUID(doctor_user_id)
        except ValueError:
            return

        profile = db.session.execute(
            select(PatientProfile).where(PatientProfile.user_id == uid)
        ).scalar_one_or_none()
        if profile is None:
            return
        profile.assigned_doctor_id = did

    def ensure_placeholder_profile_for_patient_user(self, user_id: str) -> None:
        """If the user is a patient with no ``PatientProfile``, insert a minimal row.

        Does not commit. Lets doctors receive ``assign_primary_doctor`` after the patient
        books and the doctor confirms, even when the patient has not completed the full
        profile wizard yet. The patient should replace placeholder demographics via profile.
        """
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            return

        existing = db.session.execute(
            select(PatientProfile).where(PatientProfile.user_id == uid)
        ).scalar_one_or_none()
        if existing is not None:
            return

        user = db.session.get(User, uid)
        if not user or user.role != "patient":
            return

        profile = PatientProfile(
            user_id=uid,
            date_of_birth=date(2000, 1, 1),
            gender=None,
            blood_type=None,
        )
        db.session.add(profile)

    # --- Medical History ---

    def get_medical_history(self, user_id: str) -> list[MedicalHistoryResponse]:
        """Get all medical history entries for a patient.

        Args:
            user_id: UUID string of the patient user.

        Returns:
            List of MedicalHistoryResponse.

        Raises:
            ValueError: If patient profile not found.
        """
        profile = self._get_profile_or_raise(user_id)

        stmt = (
            select(MedicalHistory)
            .where(MedicalHistory.patient_id == profile.id)
            .order_by(MedicalHistory.created_at.desc())
        )
        entries = db.session.execute(stmt).scalars().all()
        return [self._history_to_response(e) for e in entries]

    def add_medical_history(
        self, user_id: str, data: AddMedicalHistoryRequest, created_by: str
    ) -> MedicalHistoryResponse:
        """Add a medical history entry.

        Args:
            user_id: UUID string of the patient user.
            data: Validated medical history data.
            created_by: UUID string of the user creating the entry.

        Returns:
            MedicalHistoryResponse with the created entry.

        Raises:
            ValueError: If patient profile not found.
        """
        profile = self._get_profile_or_raise(user_id)

        entry = MedicalHistory(
            patient_id=profile.id,
            condition_name=data.condition_name,
            diagnosis_date=data.diagnosis_date,
            status=data.status,
            icd_10_code=data.icd_10_code,
            notes=data.notes,
            created_by=uuid.UUID(created_by),
        )
        db.session.add(entry)
        db.session.commit()

        return self._history_to_response(entry)

    def update_medical_history_status(
        self, user_id: str, entry_id: str, data: UpdateMedicalHistoryStatusRequest
    ) -> MedicalHistoryResponse:
        """Update the status of a medical history entry.

        Args:
            user_id: UUID string of the patient user.
            entry_id: UUID string of the medical history entry.
            data: Validated update data with new status and optional notes.

        Returns:
            Updated MedicalHistoryResponse.

        Raises:
            ValueError: If patient profile or entry not found.
        """
        profile = self._get_profile_or_raise(user_id)

        stmt = select(MedicalHistory).where(
            MedicalHistory.id == uuid.UUID(entry_id),
            MedicalHistory.patient_id == profile.id,
        )
        entry = db.session.execute(stmt).scalar_one_or_none()
        if not entry:
            raise ValueError("Medical history entry not found")

        entry.status = data.status
        if data.notes is not None:
            entry.notes = data.notes

        db.session.commit()
        return self._history_to_response(entry)

    # --- Allergies ---

    def get_allergies(self, user_id: str) -> list[AllergyResponse]:
        """Get all allergies for a patient.

        Args:
            user_id: UUID string of the patient user.

        Returns:
            List of AllergyResponse.

        Raises:
            ValueError: If patient profile not found.
        """
        profile = self._get_profile_or_raise(user_id)

        stmt = (
            select(Allergy)
            .where(Allergy.patient_id == profile.id)
            .order_by(Allergy.created_at.desc())
        )
        allergies = db.session.execute(stmt).scalars().all()
        return [self._allergy_to_response(a) for a in allergies]

    def add_allergy(
        self, user_id: str, data: AddAllergyRequest, created_by: str
    ) -> AllergyResponse:
        """Add an allergy record for a patient.

        Args:
            user_id: UUID string of the patient user.
            data: Validated allergy data.
            created_by: UUID string of the user creating the record.

        Returns:
            AllergyResponse with the created allergy.

        Raises:
            ValueError: If patient profile not found.
        """
        profile = self._get_profile_or_raise(user_id)

        allergy = Allergy(
            patient_id=profile.id,
            allergen=data.allergen,
            reaction=data.reaction,
            severity=data.severity,
            diagnosed_date=data.diagnosed_date,
            created_by=uuid.UUID(created_by),
        )
        db.session.add(allergy)
        db.session.commit()

        return self._allergy_to_response(allergy)

    def delete_allergy(self, user_id: str, allergy_id: str) -> None:
        """Remove an allergy record for a patient.

        Args:
            user_id: UUID string of the patient user.
            allergy_id: UUID string of the allergy to remove.

        Raises:
            ValueError: If patient profile or allergy not found.
        """
        profile = self._get_profile_or_raise(user_id)

        stmt = select(Allergy).where(
            Allergy.id == uuid.UUID(allergy_id),
            Allergy.patient_id == profile.id,
        )
        allergy = db.session.execute(stmt).scalar_one_or_none()
        if not allergy:
            raise ValueError("Allergy not found")

        db.session.delete(allergy)
        db.session.commit()

    # --- Timeline ---

    def get_timeline(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> list[TimelineEntryResponse]:
        """Aggregate all patient events into a chronological timeline.

        Collects vitals, appointments, symptoms, reports, medications, and alerts
        and returns them sorted by timestamp (most recent first).

        Args:
            user_id: UUID string of the patient user.
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.

        Returns:
            List of TimelineEntryResponse sorted by timestamp descending.

        Raises:
            ValueError: If patient profile not found.
        """
        self._get_profile_or_raise(user_id)
        uid = uuid.UUID(user_id)

        timeline: list[TimelineEntryResponse] = []

        # Vitals readings
        vitals = db.session.execute(
            select(VitalsReading)
            .where(VitalsReading.patient_id == uid)
            .order_by(VitalsReading.recorded_at.desc())
            .limit(200)
        ).scalars().all()
        for v in vitals:
            parts = []
            if v.heart_rate:
                parts.append(f"HR: {v.heart_rate} bpm")
            if v.blood_pressure_systolic and v.blood_pressure_diastolic:
                parts.append(f"BP: {v.blood_pressure_systolic}/{v.blood_pressure_diastolic}")
            if v.temperature:
                parts.append(f"Temp: {v.temperature}\u00b0C")
            if v.oxygen_saturation:
                parts.append(f"SpO2: {v.oxygen_saturation}%")
            description = ", ".join(parts) if parts else "Vitals recorded"
            timeline.append(TimelineEntryResponse(
                timestamp=v.recorded_at.isoformat(),
                event_type="vitals",
                title="Vitals Reading",
                description=description,
                data={
                    "heart_rate": v.heart_rate,
                    "bp_systolic": v.blood_pressure_systolic,
                    "bp_diastolic": v.blood_pressure_diastolic,
                    "temperature": float(v.temperature) if v.temperature else None,
                    "oxygen_saturation": float(v.oxygen_saturation) if v.oxygen_saturation else None,
                },
            ))

        # Appointments
        appointments = db.session.execute(
            select(Appointment)
            .where(Appointment.patient_id == uid)
            .order_by(Appointment.scheduled_at.desc())
            .limit(200)
        ).scalars().all()
        for a in appointments:
            timeline.append(TimelineEntryResponse(
                timestamp=a.scheduled_at.isoformat(),
                event_type="appointment",
                title=f"Appointment ({a.appointment_type.replace('_', ' ').title()})",
                description=f"Status: {a.status}" + (f" - {a.reason}" if a.reason else ""),
                data={
                    "appointment_type": a.appointment_type,
                    "status": a.status,
                    "duration_minutes": a.duration_minutes,
                    "doctor_id": str(a.doctor_id),
                },
            ))

        # Symptom sessions
        symptoms = db.session.execute(
            select(SymptomSession)
            .where(SymptomSession.patient_id == uid)
            .order_by(SymptomSession.created_at.desc())
            .limit(200)
        ).scalars().all()
        for s in symptoms:
            timeline.append(TimelineEntryResponse(
                timestamp=s.created_at.isoformat(),
                event_type="symptoms",
                title="Symptom Check",
                description=s.chief_complaint or "Symptom session recorded",
                data={
                    "status": s.status,
                    "triage_level": s.triage_level,
                    "chief_complaint": s.chief_complaint,
                },
            ))

        # Medical reports
        reports = db.session.execute(
            select(MedicalReport)
            .where(MedicalReport.patient_id == uid)
            .order_by(MedicalReport.created_at.desc())
            .limit(200)
        ).scalars().all()
        for r in reports:
            timeline.append(TimelineEntryResponse(
                timestamp=r.created_at.isoformat(),
                event_type="report",
                title=r.title,
                description=f"{r.report_type.title()} report - Status: {r.status}",
                data={
                    "report_type": r.report_type,
                    "status": r.status,
                    "file_url": r.file_url,
                },
            ))

        # Medications
        medications = db.session.execute(
            select(Medication)
            .where(Medication.patient_id == uid)
            .order_by(Medication.created_at.desc())
            .limit(200)
        ).scalars().all()
        for m in medications:
            timeline.append(TimelineEntryResponse(
                timestamp=m.created_at.isoformat(),
                event_type="medication",
                title=f"Medication: {m.name}",
                description=f"{m.dosage}, {m.frequency} - Status: {m.status}",
                data={
                    "name": m.name,
                    "dosage": m.dosage,
                    "frequency": m.frequency,
                    "status": m.status,
                    "start_date": m.start_date.isoformat() if m.start_date else None,
                },
            ))

        # Monitoring alerts
        alerts = db.session.execute(
            select(MonitoringAlert)
            .where(MonitoringAlert.patient_id == uid)
            .order_by(MonitoringAlert.created_at.desc())
            .limit(200)
        ).scalars().all()
        for al in alerts:
            timeline.append(TimelineEntryResponse(
                timestamp=al.created_at.isoformat(),
                event_type="alert",
                title=al.title,
                description=al.description,
                data={
                    "severity": al.severity,
                    "status": al.status,
                    "alert_type": al.alert_type,
                },
            ))

        # Sort all entries by timestamp descending
        timeline.sort(key=lambda e: e.timestamp, reverse=True)

        # Apply pagination
        return timeline[offset: offset + limit]

    # --- AI Summary ---

    def get_ai_summary(self, user_id: str) -> AISummaryResponse:
        """Generate an AI-powered health summary for the patient.

        Collects patient profile, medical history, allergies, recent vitals,
        and medications, then uses the OpenAI client to produce a brief summary.

        Args:
            user_id: UUID string of the patient user.

        Returns:
            AISummaryResponse with the generated summary.

        Raises:
            ValueError: If patient profile not found.
            Exception: If AI generation fails.
        """
        from app.integrations.openai_client import openai_client

        profile = self._get_profile_or_raise(user_id)
        uid = uuid.UUID(user_id)

        # Gather patient data for the summary
        history_entries = db.session.execute(
            select(MedicalHistory)
            .where(MedicalHistory.patient_id == profile.id)
            .order_by(MedicalHistory.created_at.desc())
            .limit(20)
        ).scalars().all()

        allergy_entries = db.session.execute(
            select(Allergy)
            .where(Allergy.patient_id == profile.id)
        ).scalars().all()

        recent_vitals = db.session.execute(
            select(VitalsReading)
            .where(VitalsReading.patient_id == uid)
            .order_by(VitalsReading.recorded_at.desc())
            .limit(5)
        ).scalars().all()

        active_medications = db.session.execute(
            select(Medication)
            .where(Medication.patient_id == uid, Medication.status == "active")
            .order_by(Medication.created_at.desc())
            .limit(10)
        ).scalars().all()

        # Build context for the AI
        context_parts = []
        context_parts.append(
            f"Patient: DOB {profile.date_of_birth}, "
            f"Gender: {profile.gender or 'N/A'}, "
            f"Blood Type: {profile.blood_type or 'N/A'}"
        )

        if history_entries:
            conditions = [f"- {h.condition_name} ({h.status})" for h in history_entries]
            context_parts.append("Medical History:\n" + "\n".join(conditions))

        if allergy_entries:
            allergies_list = [f"- {a.allergen} (severity: {a.severity})" for a in allergy_entries]
            context_parts.append("Allergies:\n" + "\n".join(allergies_list))

        if recent_vitals:
            vitals_lines = []
            for v in recent_vitals:
                parts = []
                if v.heart_rate:
                    parts.append(f"HR:{v.heart_rate}")
                if v.blood_pressure_systolic:
                    parts.append(f"BP:{v.blood_pressure_systolic}/{v.blood_pressure_diastolic}")
                if v.temperature:
                    parts.append(f"Temp:{v.temperature}")
                if v.oxygen_saturation:
                    parts.append(f"SpO2:{v.oxygen_saturation}")
                vitals_lines.append(f"- {v.recorded_at.isoformat()}: {', '.join(parts)}")
            context_parts.append("Recent Vitals:\n" + "\n".join(vitals_lines))

        if active_medications:
            meds = [f"- {m.name} {m.dosage} ({m.frequency})" for m in active_medications]
            context_parts.append("Active Medications:\n" + "\n".join(meds))

        patient_context = "\n\n".join(context_parts)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a medical AI assistant. Generate a brief, clear health summary "
                    "for a healthcare provider reviewing this patient's data. Include key conditions, "
                    "allergies, current medications, and any notable vital sign trends. "
                    "Keep the summary concise (3-5 sentences). Do not provide diagnoses or treatment "
                    "recommendations - just summarize the available data."
                ),
            },
            {
                "role": "user",
                "content": f"Please summarize this patient's health data:\n\n{patient_context}",
            },
        ]

        response = openai_client.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=500,
        )

        summary_text = response.content or "Unable to generate summary at this time."

        return AISummaryResponse(
            patient_id=user_id,
            summary=summary_text,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # --- Helpers ---

    def _get_profile_or_raise(self, user_id: str) -> PatientProfile:
        """Get patient profile by user_id or raise ValueError."""
        stmt = select(PatientProfile).where(
            PatientProfile.user_id == uuid.UUID(user_id)
        )
        profile = db.session.execute(stmt).scalar_one_or_none()
        if not profile:
            raise ValueError("Patient profile not found")
        return profile

    def check_access(self, requester_id: str, requester_role: str, target_user_id: str) -> bool:
        """Check if the requester has access to the target patient's data.

        Args:
            requester_id: UUID string of the requesting user.
            requester_role: Role of the requesting user.
            target_user_id: UUID string of the patient whose data is being accessed.

        Returns:
            True if access is permitted.
        """
        if requester_role == "admin":
            return True
        if requester_role == "patient":
            return requester_id == target_user_id
        if requester_role in ("doctor", "nurse"):
            profile = db.session.execute(
                select(PatientProfile).where(
                    PatientProfile.user_id == uuid.UUID(target_user_id)
                )
            ).scalar_one_or_none()
            if not profile:
                return False
            return str(profile.assigned_doctor_id) == requester_id
        return False

    @staticmethod
    def _to_response(profile: PatientProfile) -> PatientProfileResponse:
        from app.models.user import User

        first_name = None
        last_name = None
        email = None
        phone = None
        try:
            user = db.session.get(User, profile.user_id)
            if user:
                first_name = user.first_name
                last_name = user.last_name
                email = user.email
                phone = user.phone
        except Exception:
            pass

        name_parts = [x for x in (first_name, last_name) if x]
        display_name = " ".join(name_parts) if name_parts else None

        assigned_doctor_name = None
        if profile.assigned_doctor_id:
            try:
                doc_user = db.session.get(User, profile.assigned_doctor_id)
                if doc_user:
                    if doc_user.last_name:
                        assigned_doctor_name = f"Dr. {doc_user.last_name}".strip()
                    else:
                        assigned_doctor_name = (
                            f"{doc_user.first_name or ''} {doc_user.last_name or ''}".strip() or None
                        )
            except Exception:
                pass

        return PatientProfileResponse(
            id=str(profile.id),
            user_id=str(profile.user_id),
            first_name=first_name,
            last_name=last_name,
            name=display_name,
            email=email,
            phone=phone,
            date_of_birth=profile.date_of_birth,
            gender=profile.gender,
            blood_type=profile.blood_type,
            height_cm=float(profile.height_cm) if profile.height_cm else None,
            weight_kg=float(profile.weight_kg) if profile.weight_kg else None,
            emergency_contact=profile.emergency_contact,
            insurance_info=profile.insurance_info,
            assigned_doctor_id=str(profile.assigned_doctor_id) if profile.assigned_doctor_id else None,
            assigned_doctor_name=assigned_doctor_name,
        )

    @staticmethod
    def _history_to_response(entry: MedicalHistory) -> MedicalHistoryResponse:
        return MedicalHistoryResponse(
            id=str(entry.id),
            patient_id=str(entry.patient_id),
            condition_name=entry.condition_name,
            diagnosis_date=entry.diagnosis_date,
            status=entry.status,
            icd_10_code=entry.icd_10_code,
            notes=entry.notes,
        )

    @staticmethod
    def _allergy_to_response(allergy: Allergy) -> AllergyResponse:
        return AllergyResponse(
            id=str(allergy.id),
            patient_id=str(allergy.patient_id),
            allergen=allergy.allergen,
            reaction=allergy.reaction,
            severity=allergy.severity,
            diagnosed_date=allergy.diagnosed_date,
        )


# Module-level instance for use by routes
patient_service = PatientService()
