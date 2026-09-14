import os
from fastapi import FastAPI
from app.routes import auth, categories, equipment, reservations, users
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(equipment.router)
app.include_router(reservations.router)
app.include_router(users.router)
