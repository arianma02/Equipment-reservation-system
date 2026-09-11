from pydantic import BaseModel, EmailStr, Field
from datetime import date


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    status: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class CategoryResponse(BaseModel):
    id: int
    name: str


class EquipmentResponse(BaseModel):
    id: int
    name: str
    asset_tag: str
    category_id: int
    category_name: str
    status: str


class AvailabilityResponse(BaseModel):
    available: bool


class ReservationCreate(BaseModel):
    start_date: date
    end_date: date


class ReservationResponse(BaseModel):
    id: int
    user_id: int
    equipment_id: int
    start_date: date
    end_date: date
    status: str
