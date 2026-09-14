from fastapi import APIRouter, Depends, HTTPException

from app.database import get_connection
from app.dependencies import get_current_user, get_current_admin
from app.schemas import UserResponse, UserUpdate

router = APIRouter()


@router.patch("/users/me/deactivate", response_model=UserResponse)
def deactivate_account(current_user=Depends(get_current_user)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            if current_user["role"] == "admin":
                cursor.execute("""
                    SELECT id
                    FROM users
                    WHERE role = 'admin'
                      AND status = 'active'
                    FOR UPDATE
                    """)
                active_admins = cursor.fetchall()

                if len(active_admins) == 1:
                    raise HTTPException(
                        status_code=409,
                        detail="Cannot deactivate the last active admin",
                    )

            cursor.execute(
                # Disable first so the user row is locked before reservations are cancelled.
                """
                UPDATE users
                SET status = 'disabled'
                WHERE id = %s
                RETURNING id, email, role, status
                """,
                (current_user["id"],),
            )

            updated_user = cursor.fetchone()

            cursor.execute(
                """
                UPDATE reservations
                SET status = 'cancelled'
                WHERE user_id = %s
                  AND status = 'active'
                  AND end_date >= CURRENT_DATE
                """,
                (current_user["id"],),
            )

    return updated_user


@router.get(
    "/users",
    response_model=list[UserResponse],
    dependencies=[Depends(get_current_admin)],
)
def get_users():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, email, role, status
                FROM users
                ORDER BY id
                """)
            users = cursor.fetchall()
    return users


@router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(get_current_admin)],
)
def update_user(user_id: int, update: UserUpdate):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, email, role, status
                FROM users
                WHERE id = %s
                FOR UPDATE
                """,
                (user_id,),
            )

            target_user = cursor.fetchone()

            if not target_user:
                raise HTTPException(
                    status_code=404,
                    detail="User not found",
                )
            new_role = update.role if update.role is not None else target_user["role"]

            new_status = (
                update.status if update.status is not None else target_user["status"]
            )
            if (
                target_user["role"] == "admin"
                and target_user["status"] == "active"
                and (new_role != "admin" or new_status != "active")
            ):
                cursor.execute("""
                    SELECT id
                    FROM users
                    WHERE role = 'admin'
                      AND status = 'active'
                    FOR UPDATE
                    """)

                active_admins = cursor.fetchall()

                if len(active_admins) == 1:
                    raise HTTPException(
                        status_code=409,
                        detail="Cannot remove the last active admin",
                    )
            if new_status == "disabled":
                cursor.execute(
                    """
                    UPDATE reservations
                    SET status = 'cancelled'
                    WHERE user_id = %s
                      AND status = 'active'
                      AND end_date >= CURRENT_DATE
                    """,
                    (user_id,),
                )

            cursor.execute(
                """
                UPDATE users
                SET role = %s,
                    status = %s
                WHERE id = %s
                RETURNING id, email, role, status
                """,
                (new_role, new_status, user_id),
            )

            updated_user = cursor.fetchone()
    return updated_user
