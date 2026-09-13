from fastapi import APIRouter, HTTPException, Depends
from typing import Literal
from app.database import get_connection
from app.schemas import (
    EquipmentResponse,
    AvailabilityResponse,
    EquipmentCreate,
    EquipmentUpdate,
)
from app.dependencies import get_current_admin
from datetime import date
from psycopg.errors import UniqueViolation

router = APIRouter()


@router.get("/equipment", response_model=list[EquipmentResponse])
def get_equipment(
    category_id: int | None = None,
    status: Literal["active", "maintenance", "retired"] | None = None,
):
    params = []
    conditions = []
    with get_connection() as connection:
        with connection.cursor() as cursor:
            sql = (
                "SELECT e.id, e.name, e.asset_tag, e.category_id, e.status, c.name AS category_name "
                "FROM equipment e "
                "JOIN categories c ON e.category_id = c.id"
            )
            if category_id is not None:
                params.append(category_id)
                conditions.append("e.category_id = %s")
            if status is not None:
                params.append(status)
                conditions.append("e.status = %s")
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY e.name"
            cursor.execute(sql, params)
            equipment = cursor.fetchall()
    return equipment


@router.get("/equipment/{equipment_id}", response_model=EquipmentResponse)
def get_equipment_by_id(equipment_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT e.id, e.name, e.asset_tag, e.category_id, e.status, c.name AS category_name "
                "FROM equipment e "
                "JOIN categories c ON e.category_id = c.id WHERE e.id = %s",
                (equipment_id,),
            )
            equipment = cursor.fetchone()

    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    return equipment


@router.get(
    "/equipment/{equipment_id}/availability", response_model=AvailabilityResponse
)
def check_availability(equipment_id: int, start_date: date, end_date: date):
    if start_date > end_date:
        raise HTTPException(
            status_code=400, detail="Start date cannot be after end date"
        )
    if start_date < date.today():
        raise HTTPException(
            status_code=400,
            detail="Start date cannot be in the past",
        )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT status FROM equipment WHERE id = %s", (equipment_id,)
            )
            equipment_status = cursor.fetchone()

            if not equipment_status:
                raise HTTPException(status_code=404, detail="Equipment not found")

            if equipment_status["status"] != "active":
                return {"available": False}
            cursor.execute(
                "SELECT 1 FROM reservations "
                "WHERE equipment_id = %s AND status = 'active' "
                "AND start_date <= %s "
                "AND end_date >= %s",
                (equipment_id, end_date, start_date),
            )

            overlapping_reservation = cursor.fetchone()

    if overlapping_reservation:
        return {"available": False}

    return {"available": True}


@router.post(
    "/equipment",
    response_model=EquipmentResponse,
    status_code=201,
    dependencies=[Depends(get_current_admin)],
)
def create_equipment(equipment: EquipmentCreate):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name
                FROM categories
                WHERE id = %s
                """,
                (equipment.category_id,),
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
                    INSERT INTO equipment (
                        name,
                        asset_tag,
                        category_id
                    )
                    VALUES (%s, %s, %s)
                    RETURNING id, name, asset_tag, category_id, status
                    """,
                    (
                        equipment.name,
                        equipment.asset_tag,
                        equipment.category_id,
                    ),
                )

                new_equipment = cursor.fetchone()
            except UniqueViolation:
                raise HTTPException(status_code=409, detail="Asset tag already exists")

    new_equipment["category_name"] = category["name"]

    return new_equipment


@router.patch(
    "/equipment/{equipment_id}",
    response_model=EquipmentResponse,
    dependencies=[Depends(get_current_admin)],
)
def update_equipment(equipment_id: int, update: EquipmentUpdate):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT name, asset_tag, category_id, status
                FROM equipment
                WHERE id = %s
                FOR UPDATE
                """,
                (equipment_id,),
            )

            current_equipment = cursor.fetchone()

            if not current_equipment:
                raise HTTPException(
                    status_code=404,
                    detail="Equipment not found",
                )

            new_name = (
                update.name if update.name is not None else current_equipment["name"]
            )

            new_asset_tag = (
                update.asset_tag
                if update.asset_tag is not None
                else current_equipment["asset_tag"]
            )

            new_category_id = (
                update.category_id
                if update.category_id is not None
                else current_equipment["category_id"]
            )
            cursor.execute(
                """
                SELECT name
                FROM categories
                WHERE id = %s
                """,
                (new_category_id,),
            )

            category = cursor.fetchone()

            if not category:
                raise HTTPException(
                    status_code=404,
                    detail="Category not found",
                )

            new_status = (
                update.status
                if update.status is not None
                else current_equipment["status"]
            )
            if new_status == "maintenance":
                cursor.execute(
                    """
                    UPDATE reservations
                    SET status = 'cancelled'
                    WHERE equipment_id = %s
                    AND status = 'active'
                    AND end_date >= CURRENT_DATE
                    """,
                    (equipment_id,),
                )
            if new_status == "retired":
                cursor.execute(
                    """
                    SELECT 1
                    FROM reservations
                    WHERE equipment_id = %s
                    AND status = 'active'
                    AND end_date >= CURRENT_DATE
                    LIMIT 1
                    """,
                    (equipment_id,),
                )

                active_reservation = cursor.fetchone()

                if active_reservation:
                    raise HTTPException(
                        status_code=409,
                        detail="Cannot retire equipment with active reservations",
                    )
            try:
                cursor.execute(
                    """
                    UPDATE equipment
                    SET name = %s,
                        asset_tag = %s,
                        category_id = %s,
                        status = %s
                    WHERE id = %s
                    RETURNING id, name, asset_tag, category_id, status
                    """,
                    (
                        new_name,
                        new_asset_tag,
                        new_category_id,
                        new_status,
                        equipment_id,
                    ),
                )

                updated_equipment = cursor.fetchone()

            except UniqueViolation:
                raise HTTPException(
                    status_code=409,
                    detail="Asset tag already exists",
                )
            updated_equipment["category_name"] = category["name"]

    return updated_equipment
