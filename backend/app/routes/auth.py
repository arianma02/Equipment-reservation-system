from fastapi import APIRouter, HTTPException

from app.security import hash_password, create_access_token, verify_password
from app.database import get_connection
from app.schemas import UserRegister, UserResponse, UserLogin, TokenResponse
from fastapi import Depends
from app.dependencies import get_current_user

import psycopg

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
def register_user(user: UserRegister):
    hashed_password = hash_password(user.password)
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id, email, role, status",
                    (user.email, hashed_password),
                )
                new_user = cursor.fetchone()
        return new_user
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Email already registered")


@router.post("/login", response_model=TokenResponse)
def login_user(user: UserLogin):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, password_hash, status FROM users WHERE email = %s",
                (user.email,),
            )
            db_user = cursor.fetchone()

    if not db_user or not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if db_user["status"] == "disabled":
        raise HTTPException(status_code=403, detail="Account is disabled")

    access_token = create_access_token(db_user["id"])
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    return current_user
