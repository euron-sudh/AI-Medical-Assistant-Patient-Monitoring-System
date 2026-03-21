"""Unit tests for CarePlanService."""

import uuid
from datetime import date

import pytest

from app.models.care_plan import CarePlan, CarePlanGoal
from app.models.user import User
from app.schemas.care_plan_schema import (
    AddGoalRequest, CreateCarePlanRequest, UpdateCarePlanRequest, UpdateGoalRequest,
)
from app.services.care_plan_service import CarePlanService


@pytest.fixture
def service() -> CarePlanService:
    return CarePlanService()


@pytest.fixture
def patient_user(db) -> User:
    user = User(email="cp_patient@test.com", first_name="Care", last_name="Patient", role="patient")
    user.set_password("testpass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def doctor_user(db) -> User:
    user = User(email="cp_doctor@test.com", first_name="Dr. Care", last_name="Doctor", role="doctor")
    user.set_password("testpass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def care_plan(db, patient_user, doctor_user) -> CarePlan:
    plan = CarePlan(
        patient_id=patient_user.id, doctor_id=doctor_user.id,
        title="Diabetes Management", status="active",
        start_date=date(2026, 1, 1), created_by=doctor_user.id,
    )
    db.session.add(plan)
    db.session.commit()
    return plan


class TestCreateCarePlan:
    def test_create_success(self, service, patient_user, doctor_user):
        data = CreateCarePlanRequest(
            patient_id=str(patient_user.id), title="Hypertension Control", start_date=date(2026, 3, 1),
        )
        result = service.create_care_plan(data, str(doctor_user.id))
        assert result.title == "Hypertension Control"
        assert result.status == "active"

    def test_create_draft(self, service, patient_user, doctor_user):
        data = CreateCarePlanRequest(
            patient_id=str(patient_user.id), title="Draft Plan", status="draft", start_date=date(2026, 4, 1),
        )
        assert service.create_care_plan(data, str(doctor_user.id)).status == "draft"


class TestGetCarePlan:
    def test_get_success(self, service, care_plan):
        assert service.get_care_plan(str(care_plan.id)).title == "Diabetes Management"

    def test_get_not_found(self, service, db):
        with pytest.raises(ValueError, match="not found"):
            service.get_care_plan(str(uuid.uuid4()))


class TestUpdateCarePlan:
    def test_update_status(self, service, care_plan):
        data = UpdateCarePlanRequest(status="completed")
        assert service.update_care_plan(str(care_plan.id), data).status == "completed"

    def test_update_not_found(self, service, db):
        with pytest.raises(ValueError, match="not found"):
            service.update_care_plan(str(uuid.uuid4()), UpdateCarePlanRequest(status="completed"))


class TestDeleteCarePlan:
    def test_delete_cascades_goals(self, service, care_plan, db):
        from sqlalchemy import select
        db.session.add(CarePlanGoal(care_plan_id=care_plan.id, title="G1", status="in_progress"))
        db.session.commit()
        service.delete_care_plan(str(care_plan.id))
        assert len(db.session.execute(select(CarePlanGoal).where(CarePlanGoal.care_plan_id == care_plan.id)).scalars().all()) == 0


class TestGoals:
    def test_add_goal(self, service, care_plan):
        data = AddGoalRequest(title="Lower A1C to 7%", target_value="7.0", unit="%")
        result = service.add_goal(str(care_plan.id), data)
        assert result.title == "Lower A1C to 7%"
        assert result.status == "in_progress"

    def test_add_goal_plan_not_found(self, service, db):
        with pytest.raises(ValueError, match="not found"):
            service.add_goal(str(uuid.uuid4()), AddGoalRequest(title="Test"))

    def test_update_goal(self, service, care_plan, db):
        goal = CarePlanGoal(care_plan_id=care_plan.id, title="Exercise", status="in_progress")
        db.session.add(goal)
        db.session.commit()
        result = service.update_goal(str(goal.id), UpdateGoalRequest(status="achieved"))
        assert result.status == "achieved"

    def test_update_goal_not_found(self, service, db):
        with pytest.raises(ValueError, match="not found"):
            service.update_goal(str(uuid.uuid4()), UpdateGoalRequest(status="achieved"))


class TestAdherence:
    def test_adherence_empty(self, service, care_plan):
        result = service.get_adherence(str(care_plan.id))
        assert result.total_goals == 0 and result.adherence_percentage == 0.0

    def test_adherence_with_goals(self, service, care_plan, db):
        db.session.add_all([
            CarePlanGoal(care_plan_id=care_plan.id, title="G1", status="achieved"),
            CarePlanGoal(care_plan_id=care_plan.id, title="G2", status="in_progress"),
        ])
        db.session.commit()
        result = service.get_adherence(str(care_plan.id))
        assert result.total_goals == 2 and result.achieved_goals == 1 and result.adherence_percentage == 50.0


class TestAccessControl:
    def test_patient_own(self, service, care_plan, patient_user):
        assert service.check_access(str(patient_user.id), "patient", plan=care_plan) is True

    def test_patient_other(self, service, care_plan):
        assert service.check_access(str(uuid.uuid4()), "patient", plan=care_plan) is False

    def test_doctor_own(self, service, care_plan, doctor_user):
        assert service.check_access(str(doctor_user.id), "doctor", plan=care_plan) is True

    def test_admin_any(self, service, care_plan):
        assert service.check_access(str(uuid.uuid4()), "admin", plan=care_plan) is True
