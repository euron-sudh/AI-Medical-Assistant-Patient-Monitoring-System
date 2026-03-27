"""Initial schema -- all MedAssist AI models.

Revision ID: 001_initial
Revises: None
Create Date: 2026-03-26

Captures the full database schema for MedAssist AI.
"""

from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_verified", sa.Boolean(), default=False),
        sa.Column("mfa_enabled", sa.Boolean(), default=False),
        sa.Column("mfa_secret", sa.String(255), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "patient_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("gender", sa.String(20), nullable=True),
        sa.Column("blood_type", sa.String(5), nullable=True),
        sa.Column("height_cm", sa.Numeric(5, 1), nullable=True),
        sa.Column("weight_kg", sa.Numeric(5, 1), nullable=True),
        sa.Column("emergency_contact", sa.Text(), nullable=True),
        sa.Column("insurance_info", sa.Text(), nullable=True),
        sa.Column("assigned_doctor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "doctor_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("specialization", sa.String(100), nullable=False),
        sa.Column("license_number", sa.String(50), nullable=False),
        sa.Column("license_state", sa.String(5), nullable=True),
        sa.Column("years_of_experience", sa.Integer(), nullable=True),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("consultation_fee", sa.Numeric(10, 2), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("availability", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "medical_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("condition_name", sa.String(255), nullable=False),
        sa.Column("diagnosis_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="active"),
        sa.Column("icd_10_code", sa.String(10), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("diagnosed_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "allergies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("allergen", sa.String(255), nullable=False),
        sa.Column("reaction", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("diagnosed_date", sa.Date(), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "devices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("device_type", sa.String(50), nullable=False),
        sa.Column("device_name", sa.String(100), nullable=False),
        sa.Column("manufacturer", sa.String(100), nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("serial_number", sa.String(100), nullable=True),
        sa.Column("firmware_version", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="active"),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("battery_level", sa.Integer(), nullable=True),
        sa.Column("configuration", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "vitals_readings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("heart_rate", sa.Integer(), nullable=True),
        sa.Column("blood_pressure_systolic", sa.Integer(), nullable=True),
        sa.Column("blood_pressure_diastolic", sa.Integer(), nullable=True),
        sa.Column("temperature", sa.Numeric(5, 2), nullable=True),
        sa.Column("oxygen_saturation", sa.Numeric(5, 2), nullable=True),
        sa.Column("respiratory_rate", sa.Integer(), nullable=True),
        sa.Column("blood_glucose", sa.Numeric(6, 2), nullable=True),
        sa.Column("weight_kg", sa.Numeric(5, 1), nullable=True),
        sa.Column("pain_level", sa.Integer(), nullable=True),
        sa.Column("device_id", sa.String(36), sa.ForeignKey("devices.id"), nullable=True),
        sa.Column("is_manual_entry", sa.Boolean(), default=False, nullable=False),
        sa.Column("is_anomalous", sa.Boolean(), default=False, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "monitoring_alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("vitals_reading_id", sa.String(36), sa.ForeignKey("vitals_readings.id"), nullable=True),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("ai_analysis", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), default="active", nullable=False),
        sa.Column("acknowledged_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalation_level", sa.Integer(), default=0, nullable=False),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "monitoring_thresholds",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("thresholds", sa.Text(), nullable=False),
        sa.Column("updated_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("patient_id", name="uq_monitoring_thresholds_patient_id"),
    )

    op.create_table(
        "care_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("doctor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="active"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("ai_recommendations", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "care_plan_goals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("care_plan_id", sa.String(36), sa.ForeignKey("care_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_value", sa.String(100), nullable=True),
        sa.Column("current_value", sa.String(100), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="in_progress"),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "care_plan_activities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("care_plan_id", sa.String(36), sa.ForeignKey("care_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("goal_id", sa.String(36), sa.ForeignKey("care_plan_goals.id"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("activity_type", sa.String(30), nullable=False),
        sa.Column("frequency", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "medications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("dosage", sa.String(100), nullable=False),
        sa.Column("frequency", sa.String(100), nullable=False),
        sa.Column("route", sa.String(50), nullable=True),
        sa.Column("prescribed_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="active"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("side_effects", sa.Text(), nullable=True),
        sa.Column("refills_remaining", sa.Integer(), default=0),
        sa.Column("pharmacy_notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("patient_id", sa.String(36), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("request_method", sa.String(10), nullable=True),
        sa.Column("request_path", sa.String(500), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("data", sa.Text(), nullable=True),
        sa.Column("read", sa.Boolean(), default=False, nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("channel", sa.String(20), nullable=False, default="in_app"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "medical_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("file_url", sa.String(500), nullable=True),
        sa.Column("file_type", sa.String(20), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("ai_analysis", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("reviewed_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "lab_values",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("report_id", sa.String(36), sa.ForeignKey("medical_reports.id"), nullable=False),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("test_name", sa.String(255), nullable=False),
        sa.Column("value", sa.Numeric(10, 4), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("reference_min", sa.Numeric(10, 4), nullable=True),
        sa.Column("reference_max", sa.Numeric(10, 4), nullable=True),
        sa.Column("is_abnormal", sa.Boolean(), default=False, nullable=False),
        sa.Column("loinc_code", sa.String(20), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "symptom_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="in_progress"),
        sa.Column("chief_complaint", sa.Text(), nullable=True),
        sa.Column("symptoms", sa.Text(), nullable=True),
        sa.Column("ai_analysis", sa.Text(), nullable=True),
        sa.Column("triage_level", sa.String(20), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("escalated_to", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("conversation_log", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "conversations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("agent_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("messages", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="active"),
        sa.Column("escalated_to", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "appointments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("doctor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("appointment_type", sa.String(30), nullable=False, default="in_person"),
        sa.Column("status", sa.String(20), nullable=False, default="scheduled"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, default=30),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("cancelled_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("cancelled_reason", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "telemedicine_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("appointment_id", sa.String(36), sa.ForeignKey("appointments.id"), nullable=False),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("doctor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("room_url", sa.String(500), nullable=False),
        sa.Column("room_token", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="waiting"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("recording_url", sa.String(500), nullable=True),
        sa.Column("ai_transcript", sa.Text(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "telemedicine_sessions", "appointments", "conversations",
        "symptom_sessions", "lab_values", "medical_reports",
        "notifications", "audit_logs", "medications",
        "care_plan_activities", "care_plan_goals", "care_plans",
        "monitoring_thresholds", "monitoring_alerts", "vitals_readings",
        "devices", "allergies", "medical_history",
        "doctor_profiles", "patient_profiles", "users",
    ]:
        op.drop_table(table)
