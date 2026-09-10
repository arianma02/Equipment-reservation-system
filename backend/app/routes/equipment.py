from fastapi import APIRouter, HTTPException
from app.database import get_connection
from app.schemas import EquipmentResponse, AvailabilityResponse
from datetime import date

router = APIRouter()


@router.get("/equipment", response_model=list[EquipmentResponse])
def get_equipment(category_id: int | None = None, status: str | None = None):
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
