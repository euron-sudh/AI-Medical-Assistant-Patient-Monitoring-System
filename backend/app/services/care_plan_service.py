"""Care plan service — business logic for care plans, goals, and adherence."""

import uuid

from sqlalchemy import select, func

from app.extensions import db
from app.models.care_plan import CarePlan, CarePlanActivity, CarePlanGoal
from app.schemas.care_plan_schema import (
    AddGoalRequest,
    AdherenceResponse,
    CarePlanGoalResponse,
    CarePlanResponse,
    CreateCarePlanRequest,
    UpdateCarePlanRequest,
    UpdateGoalRequest,
)


class CarePlanService:
    """Handles care plan CRUD, goal management, and adherence tracking."""

    def create_care_plan(self, data: CreateCarePlanRequest, doctor_id: str) -> CarePlanResponse:
        plan = CarePlan(
            patient_id=uuid.UUID(data.patient_id),
            doctor_id=uuid.UUID(doctor_id),
            title=data.title,
            description=data.description,
            status=data.status,
            start_date=data.start_date,
            end_date=data.end_date,
            created_by=uuid.UUID(doctor_id),
        )
        db.session.add(plan)
        db.session.commit()
        return self._to_response(plan)

    def get_care_plan(self, plan_id: str) -> CarePlanResponse:
        plan = self._get_plan_or_raise(plan_id)
        return self._to_response(plan)

    def update_care_plan(self, plan_id: str, data: UpdateCarePlanRequest) -> CarePlanResponse:
        plan = self._get_plan_or_raise(plan_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(plan, field, value)
        db.session.commit()
        return self._to_response(plan)

    def list_care_plans(self, patient_id: str | None = None, doctor_id: str | None = None,
                        status: str | None = None, limit: int = 50, offset: int = 0) -> list[CarePlanResponse]:
        stmt = select(CarePlan)
        if patient_id:
            stmt = stmt.where(CarePlan.patient_id == uuid.UUID(patient_id))
        if doctor_id:
            stmt = stmt.where(CarePlan.doctor_id == uuid.UUID(doctor_id))
        if status:
            stmt = stmt.where(CarePlan.status == status)
        stmt = stmt.order_by(CarePlan.created_at.desc()).limit(limit).offset(offset)
        plans = db.session.execute(stmt).scalars().all()
        return [self._to_response(p) for p in plans]

    def delete_care_plan(self, plan_id: str) -> None:
        plan = self._get_plan_or_raise(plan_id)
        db.session.delete(plan)
        db.session.commit()

    def add_goal(self, plan_id: str, data: AddGoalRequest) -> CarePlanGoalResponse:
        self._get_plan_or_raise(plan_id)
        goal = CarePlanGoal(
            care_plan_id=uuid.UUID(plan_id),
            title=data.title, description=data.description,
            target_value=data.target_value, current_value=data.current_value,
            unit=data.unit, status=data.status, target_date=data.target_date,
        )
        db.session.add(goal)
        db.session.commit()
        return self._goal_to_response(goal)

    def update_goal(self, goal_id: str, data: UpdateGoalRequest) -> CarePlanGoalResponse:
        goal = db.session.execute(
            select(CarePlanGoal).where(CarePlanGoal.id == uuid.UUID(goal_id))
        ).scalar_one_or_none()
        if not goal:
            raise ValueError("Care plan goal not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(goal, field, value)
        db.session.commit()
        return self._goal_to_response(goal)

    def get_adherence(self, plan_id: str) -> AdherenceResponse:
        self._get_plan_or_raise(plan_id)
        pid = uuid.UUID(plan_id)
        total_goals = db.session.execute(
            select(func.count()).where(CarePlanGoal.care_plan_id == pid)
        ).scalar() or 0
        achieved_goals = db.session.execute(
            select(func.count()).where(CarePlanGoal.care_plan_id == pid, CarePlanGoal.status == "achieved")
        ).scalar() or 0
        total_activities = db.session.execute(
            select(func.count()).where(CarePlanActivity.care_plan_id == pid)
        ).scalar() or 0
        completed_activities = db.session.execute(
            select(func.count()).where(CarePlanActivity.care_plan_id == pid, CarePlanActivity.status == "completed")
        ).scalar() or 0
        total = total_goals + total_activities
        pct = (achieved_goals + completed_activities) / total * 100 if total > 0 else 0.0
        return AdherenceResponse(
            care_plan_id=plan_id, total_goals=total_goals, achieved_goals=achieved_goals,
            total_activities=total_activities, completed_activities=completed_activities,
            adherence_percentage=round(pct, 1),
        )

    def check_access(self, requester_id: str, requester_role: str,
                     plan: CarePlan | None = None, patient_id: str | None = None) -> bool:
        if requester_role == "admin":
            return True
        if requester_role == "patient":
            return str(plan.patient_id) == requester_id if plan else patient_id == requester_id
        if requester_role in ("doctor", "nurse"):
            return str(plan.doctor_id) == requester_id if plan else True
        return False

    def _get_plan_or_raise(self, plan_id: str) -> CarePlan:
        plan = db.session.execute(
            select(CarePlan).where(CarePlan.id == uuid.UUID(plan_id))
        ).scalar_one_or_none()
        if not plan:
            raise ValueError("Care plan not found")
        return plan

    @staticmethod
    def _to_response(plan: CarePlan) -> CarePlanResponse:
        goals = [CarePlanGoalResponse(
            id=str(g.id), care_plan_id=str(g.care_plan_id), title=g.title,
            description=g.description, target_value=g.target_value,
            current_value=g.current_value, unit=g.unit, status=g.status, target_date=g.target_date,
        ) for g in plan.goals]
        return CarePlanResponse(
            id=str(plan.id), patient_id=str(plan.patient_id), doctor_id=str(plan.doctor_id),
            title=plan.title, description=plan.description, status=plan.status,
            start_date=plan.start_date, end_date=plan.end_date,
            ai_recommendations=plan.ai_recommendations, goals=goals,
        )

    @staticmethod
    def _goal_to_response(goal: CarePlanGoal) -> CarePlanGoalResponse:
        return CarePlanGoalResponse(
            id=str(goal.id), care_plan_id=str(goal.care_plan_id), title=goal.title,
            description=goal.description, target_value=goal.target_value,
            current_value=goal.current_value, unit=goal.unit, status=goal.status,
            target_date=goal.target_date,
        )


care_plan_service = CarePlanService()
