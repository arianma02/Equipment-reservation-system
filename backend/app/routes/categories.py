from fastapi import APIRouter, Depends, HTTPException
from app.database import get_connection
from app.schemas import CategoryResponse, CategoryCreate, CategoryUpdate

from psycopg.errors import UniqueViolation
from app.dependencies import get_current_admin

router = APIRouter()


@router.get("/categories", response_model=list[CategoryResponse])
def get_categories():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, name
                FROM categories
                ORDER BY name
                """)
            categories = cursor.fetchall()
    return categories


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=201,
    dependencies=[Depends(get_current_admin)],
)
def create_category(category: CategoryCreate):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO categories (name)
                    VALUES (%s)
                    RETURNING id, name
                    """,
                    (category.name,),
                )

                new_category = cursor.fetchone()

            except UniqueViolation:
                raise HTTPException(
                    status_code=409,
                    detail="Category already exists",
                )

    return new_category


@router.patch(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    dependencies=[Depends(get_current_admin)],
)
def update_category(category_id: int, update: CategoryUpdate):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM categories
                WHERE id = %s
                """,
                (category_id,),
            )

            category = cursor.fetchone()

            if not category:
                raise HTTPException(
                    status_code=404,
                    detail="Category not found",
                )
            try:
                cursor.execute(
                    """
                    UPDATE categories
                    SET name = %s
                    WHERE id = %s
                    RETURNING id, name
                    """,
                    (update.name, category_id),
                )

                updated_category = cursor.fetchone()
            except UniqueViolation:
                raise HTTPException(
                    status_code=409,
                    detail="Category already exists",
                )
    return updated_category


@router.delete(
    "/categories/{category_id}",
    status_code=204,
    dependencies=[Depends(get_current_admin)],
)
def delete_category(category_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM categories
                WHERE id = %s
                """,
                (category_id,),
            )

            category = cursor.fetchone()

            if not category:
                raise HTTPException(
                    status_code=404,
                    detail="Category not found",
                )

            cursor.execute(
                """
                SELECT 1
                FROM equipment
                WHERE category_id = %s
                LIMIT 1
                """,
                (category_id,),
            )

            equipment = cursor.fetchone()

            if equipment:
                raise HTTPException(
                    status_code=409,
                    detail="Category is still in use",
                )
            cursor.execute(
                """
                DELETE FROM categories
                WHERE id = %s
                """,
                (category_id,),
            )
