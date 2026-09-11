from fastapi import APIRouter, Depends, HTTPException

from app.database import get_connection
from app.dependencies import get_current_user
from app.schemas import ReservationCreate, ReservationResponse

router = APIRouter()


@router.post(
    "/equipment/{equipment_id}/reservations",
    response_model=ReservationResponse,
    status_code=201,
)
def create_reservation(
    equipment_id: int,
    reservation: ReservationCreate,
    current_user=Depends(get_current_user),
):
    if reservation.start_date > reservation.end_date:
        raise HTTPException(
            status_code=400, detail="Start date cannot be after end date"
        )
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT status FROM equipment WHERE id = %s FOR UPDATE",
                (equipment_id,),
            )
            equipment = cursor.fetchone()
            if not equipment:
                raise HTTPException(status_code=404, detail="Equipment not found")

            if equipment["status"] != "active":
                raise HTTPException(
                    status_code=409, detail="Equipment is not available for reservation"
                )

            cursor.execute(
                "SELECT 1 FROM reservations WHERE equipment_id = %s AND status = 'active' AND start_date <= %s AND end_date >= %s",
                (equipment_id, reservation.end_date, reservation.start_date),
            )
            overlapping_reservation = cursor.fetchone()
            if overlapping_reservation:
                raise HTTPException(
                    status_code=409,
                    detail="Equipment is already reserved for the selected dates",
                )
            cursor.execute(
                "INSERT INTO reservations "
                "(user_id, equipment_id, start_date, end_date) "
                "VALUES (%s, %s, %s, %s) "
                "RETURNING id, user_id, equipment_id, start_date, end_date, status",
                (
                    current_user["id"],
                    equipment_id,
                    reservation.start_date,
                    reservation.end_date,
                ),
            )

            new_reservation = cursor.fetchone()
    return new_reservation
