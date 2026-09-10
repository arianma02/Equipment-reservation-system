from fastapi import APIRouter
from app.database import get_connection
from app.schemas import CategoryResponse

router = APIRouter()


@router.get("/categories", response_model=list[CategoryResponse])
def get_categories():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name FROM categories ORDER BY name")
            categories = cursor.fetchall()
    return categories
