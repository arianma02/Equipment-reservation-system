from pydantic import BaseModel, EmailStr, Field, BeforeValidator, StringConstraints
from datetime import date
from typing import Literal, Annotated


def normalize_email(value: str) -> str:
    return str(value).strip().lower()


NormalizedEmail = Annotated[
    EmailStr,
    BeforeValidator(normalize_email),
]

NonEmptyText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
    ),
]

AssetTag = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        to_upper=True,
    ),
]


class UserRegister(BaseModel):
    email: NormalizedEmail
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    status: str


class UserLogin(BaseModel):
    email: NormalizedEmail
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


class UserReservationResponse(BaseModel):
    id: int
    user_id: int
    equipment_id: int
    equipment_name: str
    start_date: date
    end_date: date
    status: str


class UserUpdate(BaseModel):
    role: Literal["user", "admin"] | None = None
    status: Literal["active", "disabled"] | None = None


class AdminReservationResponse(BaseModel):
    id: int
    user_id: int
    user_email: str
    equipment_id: int
    equipment_name: str
    start_date: date
    end_date: date
    status: str


class EquipmentCreate(BaseModel):
    name: NonEmptyText
    asset_tag: AssetTag
    category_id: int


class EquipmentUpdate(BaseModel):
    name: NonEmptyText | None = None
    asset_tag: AssetTag | None = None
    category_id: int | None = None
    status: Literal["active", "maintenance", "retired"] | None = None


class CategoryCreate(BaseModel):
    name: NonEmptyText


class CategoryUpdate(BaseModel):
    name: NonEmptyText
