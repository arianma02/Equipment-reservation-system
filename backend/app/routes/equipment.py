from fastapi import APIRouter, HTTPException
from app.database import get_connection
from app.schemas import EquipmentResponse

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
