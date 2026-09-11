from fastapi import FastAPI
from app.routes import auth, categories, equipment, reservations, users

app = FastAPI()
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(equipment.router)
app.include_router(reservations.router)
app.include_router(users.router)
