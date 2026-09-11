from fastapi import APIRouter, Depends, HTTPException

from app.database import get_connection
from app.dependencies import get_current_user, get_current_admin
from app.schemas import ReservationCreate, ReservationResponse, AdminReservationResponse

from datetime import date

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


@router.get("/reservations/me", response_model=list[ReservationResponse])
def get_my_reservations(current_user=Depends(get_current_user)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, user_id, equipment_id, start_date, end_date, status "
                "FROM reservations WHERE user_id = %s "
                "ORDER BY start_date",
                (current_user["id"],),
            )
            reservations = cursor.fetchall()

    return reservations


@router.patch("/reservations/{reservation_id}/cancel")
def cancel_reservation(reservation_id: int, current_user=Depends(get_current_user)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, user_id, equipment_id, start_date, end_date, status "
                "FROM reservations "
                "WHERE id = %s "
                "FOR UPDATE ",
                (reservation_id,),
            )
            reservation = cursor.fetchone()
            if not reservation:
                raise HTTPException(status_code=404, detail="Reservation not found")
            if (
                reservation["user_id"] != current_user["id"]
                and current_user["role"] != "admin"
            ):
                raise HTTPException(
                    status_code=403, detail="Not authorized to cancel this reservation"
                )
            if reservation["status"] != "active":
                raise HTTPException(
                    status_code=409, detail="Reservation already cancelled"
                )
            if reservation["end_date"] < date.today():
                raise HTTPException(
                    status_code=409, detail="Completed reservations cannot be cancelled"
                )
            cursor.execute(
                "UPDATE reservations "
                "SET status = 'cancelled' "
                "WHERE id = %s "
                "RETURNING id, user_id, equipment_id, start_date, end_date, status;",
                (reservation["id"],),
            )
            cancelled_reservation = cursor.fetchone()
    return cancelled_reservation


@router.get(
    "/reservations",
    response_model=list[AdminReservationResponse],
    dependencies=[Depends(get_current_admin)],
)
def get_all_reservations():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    r.id,
                    r.user_id,
                    u.email AS user_email,
                    r.equipment_id,
                    e.name AS equipment_name,
                    r.start_date,
                    r.end_date,
                    r.status
                FROM reservations r
                JOIN users u ON r.user_id = u.id
                JOIN equipment e ON r.equipment_id = e.id
                ORDER BY r.start_date
                """)
            reservations = cursor.fetchall()
    return reservations
