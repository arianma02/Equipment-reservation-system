from fastapi import FastAPI
from app.routes import auth, categories, equipment

app = FastAPI()
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(equipment.router)
