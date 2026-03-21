"""Auth request/response schemas — Pydantic validation for auth endpoints."""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: str = Field(pattern=r"^(patient|doctor|nurse)$")
    phone: str | None = Field(default=None, max_length=20)


class LoginRequest(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    """Schema for user data in responses."""

    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


class ChangePasswordRequest(BaseModel):
    """Schema for password change."""

    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)
