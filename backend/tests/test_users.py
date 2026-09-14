from app.database import get_connection
from datetime import timedelta
from app.time_utils import utc_today


def test_user_can_deactivate_own_account(client):
    user = client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    ).json()

    login_response = client.post(
        "/login",
        json={"email": "user@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO categories (name)
                VALUES (%s)
                RETURNING id
                """,
                ("Sports",),
            )
            category = cursor.fetchone()

            cursor.execute(
                """
                INSERT INTO equipment (name, asset_tag, category_id)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                ("Basketball", "BB-001", category["id"]),
            )
            equipment = cursor.fetchone()

            today = utc_today()

            cursor.execute(
                """
                INSERT INTO reservations (
                    user_id,
                    equipment_id,
                    start_date,
                    end_date
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    user["id"],
                    equipment["id"],
                    today + timedelta(days=10),
                    today + timedelta(days=15),
                ),
            )
            reservation = cursor.fetchone()

    response = client.patch(
        "/users/me/deactivate",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "disabled"

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT status
                FROM reservations
                WHERE id = %s
                """,
                (reservation["id"],),
            )
            updated_reservation = cursor.fetchone()

    assert updated_reservation["status"] == "cancelled"


def test_deactivation_keeps_past_reservations(client):
    user = client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    ).json()

    login_response = client.post(
        "/login",
        json={"email": "user@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO categories (name)
                VALUES (%s)
                RETURNING id
                """,
                ("Sports",),
            )
            category = cursor.fetchone()

            cursor.execute(
                """
                INSERT INTO equipment (name, asset_tag, category_id)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                ("Basketball", "BB-001", category["id"]),
            )
            equipment = cursor.fetchone()

            today = utc_today()

            cursor.execute(
                """
                INSERT INTO reservations (
                    user_id,
                    equipment_id,
                    start_date,
                    end_date
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    user["id"],
                    equipment["id"],
                    today - timedelta(days=5),
                    today - timedelta(days=2),
                ),
            )
            reservation = cursor.fetchone()

    response = client.patch(
        "/users/me/deactivate",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT status
                FROM reservations
                WHERE id = %s
                """,
                (reservation["id"],),
            )
            updated_reservation = cursor.fetchone()

    assert updated_reservation["status"] == "active"


def test_deactivate_requires_authentication(client):
    response = client.patch("/users/me/deactivate")

    assert response.status_code == 401


def test_last_active_admin_cannot_deactivate_self(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET role = 'admin'
                WHERE id = %s
                """,
                (admin["id"],),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        "/users/me/deactivate",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Cannot deactivate the last active admin"}

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT status
                FROM users
                WHERE id = %s
                """,
                (admin["id"],),
            )
            updated_admin = cursor.fetchone()

    assert updated_admin["status"] == "active"


def test_admin_can_deactivate_self_when_another_active_admin_exists(client):
    admin1 = client.post(
        "/register",
        json={"email": "admin1@example.com", "password": "testpassword"},
    ).json()

    admin2 = client.post(
        "/register",
        json={"email": "admin2@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET role = 'admin'
                WHERE id IN (%s, %s)
                """,
                (admin1["id"], admin2["id"]),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin1@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        "/users/me/deactivate",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "disabled"


def test_admin_can_get_users(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET role = 'admin'
                WHERE id = %s
                """,
                (admin["id"],),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "email": "admin@example.com",
            "role": "admin",
            "status": "active",
        },
        {
            "id": 2,
            "email": "user@example.com",
            "role": "user",
            "status": "active",
        },
    ]


def test_normal_user_cannot_get_users(client):
    client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    )

    login_response = client.post(
        "/login",
        json={"email": "user@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_get_users_requires_authentication(client):
    response = client.get("/users")
    assert response.status_code == 401


def test_admin_can_disable_user(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    target_user = client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET role = 'admin'
                WHERE id = %s
                """,
                (admin["id"],),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/users/{target_user['id']}",
        json={"status": "disabled"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == target_user["id"]
    assert response.json()["status"] == "disabled"
    assert response.json()["role"] == "user"


def test_cannot_disable_last_active_admin(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET role = 'admin'
                WHERE id = %s
                """,
                (admin["id"],),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/users/{admin['id']}",
        json={"status": "disabled"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Cannot remove the last active admin"}


def test_admin_can_disable_admin_when_another_active_admin_exists(client):
    admin1 = client.post(
        "/register",
        json={"email": "admin1@example.com", "password": "testpassword"},
    ).json()

    admin2 = client.post(
        "/register",
        json={"email": "admin2@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET role = 'admin'
                WHERE id IN (%s, %s)
                """,
                (admin1["id"], admin2["id"]),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin1@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/users/{admin1['id']}",
        json={"status": "disabled"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "disabled"
    assert response.json()["role"] == "admin"


def test_cannot_demote_last_active_admin(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET role = 'admin'
                WHERE id = %s
                """,
                (admin["id"],),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/users/{admin['id']}",
        json={"role": "user"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Cannot remove the last active admin"}


def test_admin_can_demote_admin_when_another_active_admin_exists(client):
    admin1 = client.post(
        "/register",
        json={"email": "admin1@example.com", "password": "testpassword"},
    ).json()

    admin2 = client.post(
        "/register",
        json={"email": "admin2@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET role = 'admin'
                WHERE id IN (%s, %s)
                """,
                (admin1["id"], admin2["id"]),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin1@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/users/{admin2['id']}",
        json={"role": "user"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "user"
    assert response.json()["status"] == "active"


def test_disabling_user_cancels_future_reservations(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    target_user = client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET role = 'admin'
                WHERE id = %s
                """,
                (admin["id"],),
            )

            cursor.execute(
                """
                INSERT INTO categories (name)
                VALUES (%s)
                RETURNING id
                """,
                ("Sports",),
            )
            category = cursor.fetchone()

            cursor.execute(
                """
                INSERT INTO equipment (name, asset_tag, category_id)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                ("Basketball", "BB-001", category["id"]),
            )
            equipment = cursor.fetchone()

            cursor.execute(
                """
                INSERT INTO reservations (
                    user_id,
                    equipment_id,
                    start_date,
                    end_date
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    target_user["id"],
                    equipment["id"],
                    utc_today() + timedelta(days=1),
                    utc_today() + timedelta(days=3),
                ),
            )
            reservation = cursor.fetchone()

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/users/{target_user['id']}",
        json={"status": "disabled"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT status
                FROM reservations
                WHERE id = %s
                """,
                (reservation["id"],),
            )
            updated_reservation = cursor.fetchone()

    assert updated_reservation["status"] == "cancelled"


def test_disabling_user_keeps_past_reservations(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    target_user = client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET role = 'admin'
                WHERE id = %s
                """,
                (admin["id"],),
            )

            cursor.execute(
                """
                INSERT INTO categories (name)
                VALUES (%s)
                RETURNING id
                """,
                ("Sports",),
            )
            category = cursor.fetchone()

            cursor.execute(
                """
                INSERT INTO equipment (name, asset_tag, category_id)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                ("Basketball", "BB-001", category["id"]),
            )
            equipment = cursor.fetchone()

            cursor.execute(
                """
                INSERT INTO reservations (
                    user_id,
                    equipment_id,
                    start_date,
                    end_date
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    target_user["id"],
                    equipment["id"],
                    utc_today() - timedelta(days=5),
                    utc_today() - timedelta(days=2),
                ),
            )
            reservation = cursor.fetchone()

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/users/{target_user['id']}",
        json={"status": "disabled"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT status
                FROM reservations
                WHERE id = %s
                """,
                (reservation["id"],),
            )
            updated_reservation = cursor.fetchone()

    assert updated_reservation["status"] == "active"


def test_normal_user_cannot_update_users(client):
    user = client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    ).json()

    target_user = client.post(
        "/register",
        json={"email": "target@example.com", "password": "testpassword"},
    ).json()

    login_response = client.post(
        "/login",
        json={"email": "user@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/users/{target_user['id']}",
        json={"status": "disabled"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_admin_gets_404_when_updating_missing_user(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET role = 'admin'
                WHERE id = %s
                """,
                (admin["id"],),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        "/users/999",
        json={"status": "disabled"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_admin_can_promote_user_to_admin(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    target_user = client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET role = 'admin'
                WHERE id = %s
                """,
                (admin["id"],),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/users/{target_user['id']}",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    assert response.json()["status"] == "active"


def test_admin_cannot_set_invalid_role(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    target_user = client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET role = 'admin'
                WHERE id = %s
                """,
                (admin["id"],),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/users/{target_user['id']}",
        json={"role": "superadmin"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_admin_cannot_set_invalid_status(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    target_user = client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET role = 'admin'
                WHERE id = %s
                """,
                (admin["id"],),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/users/{target_user['id']}",
        json={"status": "banned"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_disabling_user_cancels_in_progress_reservation(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    target_user = client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET role = 'admin'
                WHERE id = %s
                """,
                (admin["id"],),
            )

            cursor.execute(
                """
                INSERT INTO categories (name)
                VALUES (%s)
                RETURNING id
                """,
                ("Sports",),
            )
            category = cursor.fetchone()

            cursor.execute(
                """
                INSERT INTO equipment (name, asset_tag, category_id)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                ("Basketball", "BB-001", category["id"]),
            )
            equipment = cursor.fetchone()

            cursor.execute(
                """
                INSERT INTO reservations (
                    user_id,
                    equipment_id,
                    start_date,
                    end_date
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    target_user["id"],
                    equipment["id"],
                    utc_today() - timedelta(days=2),
                    utc_today() + timedelta(days=2),
                ),
            )
            reservation = cursor.fetchone()

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/users/{target_user['id']}",
        json={"status": "disabled"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT status
                FROM reservations
                WHERE id = %s
                """,
                (reservation["id"],),
            )
            updated_reservation = cursor.fetchone()

    assert updated_reservation["status"] == "cancelled"


def test_deactivation_cancels_in_progress_reservation(client):
    user = client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    ).json()

    login_response = client.post(
        "/login",
        json={"email": "user@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO categories (name)
                VALUES (%s)
                RETURNING id
                """,
                ("Sports",),
            )
            category = cursor.fetchone()

            cursor.execute(
                """
                INSERT INTO equipment (name, asset_tag, category_id)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                ("Basketball", "BB-001", category["id"]),
            )
            equipment = cursor.fetchone()

            cursor.execute(
                """
                INSERT INTO reservations (
                    user_id,
                    equipment_id,
                    start_date,
                    end_date
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    user["id"],
                    equipment["id"],
                    utc_today() - timedelta(days=2),
                    utc_today() + timedelta(days=2),
                ),
            )
            reservation = cursor.fetchone()

    response = client.patch(
        "/users/me/deactivate",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT status
                FROM reservations
                WHERE id = %s
                """,
                (reservation["id"],),
            )
            updated_reservation = cursor.fetchone()

    assert updated_reservation["status"] == "cancelled"


def test_admin_can_reenable_disabled_user(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    target_user = client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET role = 'admin'
                WHERE id = %s
                """,
                (admin["id"],),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    disable_response = client.patch(
        f"/users/{target_user['id']}",
        json={"status": "disabled"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert disable_response.status_code == 200
    assert disable_response.json()["status"] == "disabled"

    enable_response = client.patch(
        f"/users/{target_user['id']}",
        json={"status": "active"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert enable_response.status_code == 200
    assert enable_response.json()["status"] == "active"

    user_login = client.post(
        "/login",
        json={"email": "user@example.com", "password": "testpassword"},
    )

    assert user_login.status_code == 200
