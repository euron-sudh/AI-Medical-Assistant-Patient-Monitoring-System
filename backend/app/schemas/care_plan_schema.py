"""Care plan request/response schemas — Pydantic validation."""

from datetime import date

from pydantic import BaseModel, Field


class CreateCarePlanRequest(BaseModel):
    patient_id: str
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: str = Field(default="active", pattern=r"^(draft|active|completed|cancelled)$")
    start_date: date
    end_date: date | None = None


class UpdateCarePlanRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    status: str | None = Field(default=None, pattern=r"^(draft|active|completed|cancelled)$")
    end_date: date | None = None


class CarePlanGoalResponse(BaseModel):
    id: str
    care_plan_id: str
    title: str
    description: str | None = None
    target_value: str | None = None
    current_value: str | None = None
    unit: str | None = None
    status: str
    target_date: date | None = None

    class Config:
        from_attributes = True


class CarePlanResponse(BaseModel):
    id: str
    patient_id: str
    doctor_id: str
    title: str
    description: str | None = None
    status: str
    start_date: date
    end_date: date | None = None
    ai_recommendations: dict | None = None
    goals: list[CarePlanGoalResponse] = []

    class Config:
        from_attributes = True


class AddGoalRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    target_value: str | None = Field(default=None, max_length=100)
    current_value: str | None = Field(default=None, max_length=100)
    unit: str | None = Field(default=None, max_length=50)
    status: str = Field(default="in_progress", pattern=r"^(not_started|in_progress|achieved|missed)$")
    target_date: date | None = None


class UpdateGoalRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    target_value: str | None = Field(default=None, max_length=100)
    current_value: str | None = Field(default=None, max_length=100)
    unit: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, pattern=r"^(not_started|in_progress|achieved|missed)$")
    target_date: date | None = None


class AdherenceResponse(BaseModel):
    care_plan_id: str
    total_goals: int
    achieved_goals: int
    total_activities: int
    completed_activities: int
    adherence_percentage: float
