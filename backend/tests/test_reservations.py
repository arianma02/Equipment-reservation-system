from app.database import get_connection
from datetime import timedelta
from app.time_utils import utc_today


def test_create_reservation(client):
    client.post(
        "/register",
        json={"email": "test@example.com", "password": "testpassword"},
    )

    login_response = client.post(
        "/login",
        json={"email": "test@example.com", "password": "testpassword"},
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
    start_date = today + timedelta(days=10)
    end_date = today + timedelta(days=13)

    response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "user_id": 1,
        "equipment_id": 1,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "status": "active",
    }


def test_create_overlapping_reservation_rejected(client):
    client.post(
        "/register",
        json={"email": "test@example.com", "password": "testpassword"},
    )
    login_response = client.post(
        "/login",
        json={"email": "test@example.com", "password": "testpassword"},
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

    first_response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={
            "start_date": (today + timedelta(days=10)).isoformat(),
            "end_date": (today + timedelta(days=15)).isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    second_response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={
            "start_date": (today + timedelta(days=12)).isoformat(),
            "end_date": (today + timedelta(days=14)).isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Equipment is already reserved for the selected dates"
    }


def test_create_non_overlapping_reservations(client):
    client.post(
        "/register",
        json={"email": "test@example.com", "password": "testpassword"},
    )
    login_response = client.post(
        "/login",
        json={"email": "test@example.com", "password": "testpassword"},
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

    first_response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={
            "start_date": (today + timedelta(days=10)).isoformat(),
            "end_date": (today + timedelta(days=15)).isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    second_response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={
            "start_date": (today + timedelta(days=16)).isoformat(),
            "end_date": (today + timedelta(days=20)).isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201


def test_create_reservation_invalid_date_range(client):
    client.post(
        "/register",
        json={"email": "test@example.com", "password": "testpassword"},
    )

    login_response = client.post(
        "/login",
        json={"email": "test@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    today = utc_today()

    response = client.post(
        "/equipment/999/reservations",
        json={
            "start_date": (today + timedelta(days=10)).isoformat(),
            "end_date": (today + timedelta(days=5)).isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Start date cannot be after end date"}


def test_create_reservation_equipment_not_found(client):
    client.post(
        "/register",
        json={"email": "test@example.com", "password": "testpassword"},
    )

    login_response = client.post(
        "/login",
        json={"email": "test@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    today = utc_today()

    response = client.post(
        "/equipment/999/reservations",
        json={
            "start_date": (today + timedelta(days=10)).isoformat(),
            "end_date": (today + timedelta(days=15)).isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Equipment not found"}


def test_create_reservation_maintenance_equipment_rejected(client):
    client.post(
        "/register",
        json={"email": "test@example.com", "password": "testpassword"},
    )
    login_response = client.post(
        "/login",
        json={"email": "test@example.com", "password": "testpassword"},
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
                INSERT INTO equipment (
                    name,
                    asset_tag,
                    category_id,
                    status
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                ("Basketball", "BB-001", category["id"], "maintenance"),
            )
            equipment = cursor.fetchone()

    today = utc_today()

    response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={
            "start_date": (today + timedelta(days=10)).isoformat(),
            "end_date": (today + timedelta(days=15)).isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Equipment is not available for reservation"}


def test_create_reservation_requires_authentication(client):
    today = utc_today()

    response = client.post(
        "/equipment/1/reservations",
        json={
            "start_date": (today + timedelta(days=10)).isoformat(),
            "end_date": (today + timedelta(days=15)).isoformat(),
        },
    )

    assert response.status_code == 401


def test_create_same_day_reservation(client):
    client.post(
        "/register",
        json={"email": "test@example.com", "password": "testpassword"},
    )

    login_response = client.post(
        "/login",
        json={"email": "test@example.com", "password": "testpassword"},
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

    reservation_date = utc_today() + timedelta(days=10)

    response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={
            "start_date": reservation_date.isoformat(),
            "end_date": reservation_date.isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201


def test_get_my_reservations_only_returns_current_users_reservation(client):
    user1 = client.post(
        "/register",
        json={"email": "test1@example.com", "password": "testpassword"},
    ).json()
    user2 = client.post(
        "/register",
        json={"email": "test2@example.com", "password": "testpassword"},
    ).json()

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
                    equipment_id,
                    user_id,
                    start_date,
                    end_date
                )
                VALUES
                    (%s, %s, %s, %s),
                    (%s, %s, %s, %s)
                """,
                (
                    equipment["id"],
                    user1["id"],
                    utc_today() + timedelta(days=1),
                    utc_today() + timedelta(days=5),
                    equipment["id"],
                    user2["id"],
                    utc_today() + timedelta(days=10),
                    utc_today() + timedelta(days=15),
                ),
            )
    user_one = client.post(
        "/login", json={"email": "test1@example.com", "password": "testpassword"}
    )
    token_one = user_one.json()["access_token"]
    user_one_reservations = client.get(
        "/reservations/me", headers={"Authorization": f"Bearer {token_one}"}
    )
    assert user_one_reservations.status_code == 200
    assert user_one_reservations.json() == [
        {
            "id": 1,
            "user_id": 1,
            "equipment_id": 1,
            "equipment_name": "Basketball",
            "start_date": (utc_today() + timedelta(days=1)).isoformat(),
            "end_date": (utc_today() + timedelta(days=5)).isoformat(),
            "status": "active",
        }
    ]


def test_get_my_reservations_empty(client):
    client.post(
        "/register", json={"email": "test@example.com", "password": "testpassword"}
    )
    login_response = client.post(
        "/login", json={"email": "test@example.com", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]
    response = client.get(
        "/reservations/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.json() == []
    assert response.status_code == 200


def test_get_my_reservations_requires_authentication(client):
    response = client.get("/reservations/me")
    assert response.status_code == 401


def test_cancel_own_reservation(client):
    register_response = client.post(
        "/register",
        json={"email": "test@example.com", "password": "testpassword"},
    ).json()

    login_response = client.post(
        "/login",
        json={"email": "test@example.com", "password": "testpassword"},
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
                    equipment_id,
                    user_id,
                    start_date,
                    end_date
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    equipment["id"],
                    register_response["id"],
                    today + timedelta(days=10),
                    today + timedelta(days=15),
                ),
            )
            reservation = cursor.fetchone()

    response = client.patch(
        f"/reservations/{reservation['id']}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_cannot_cancel_another_users_reservation(client):
    user1 = client.post(
        "/register",
        json={"email": "user1@example.com", "password": "testpassword"},
    ).json()

    client.post(
        "/register",
        json={"email": "user2@example.com", "password": "testpassword"},
    )

    login_user2 = client.post(
        "/login",
        json={"email": "user2@example.com", "password": "testpassword"},
    )
    token_user2 = login_user2.json()["access_token"]

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
                    equipment_id,
                    user_id,
                    start_date,
                    end_date
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    equipment["id"],
                    user1["id"],
                    today + timedelta(days=10),
                    today + timedelta(days=15),
                ),
            )
            reservation = cursor.fetchone()

    response = client.patch(
        f"/reservations/{reservation['id']}/cancel",
        headers={"Authorization": f"Bearer {token_user2}"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Not authorized to cancel this reservation"}


def test_cancel_already_cancelled_reservation(client):
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
                    equipment_id,
                    user_id,
                    start_date,
                    end_date,
                    status
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    equipment["id"],
                    user["id"],
                    today + timedelta(days=10),
                    today + timedelta(days=15),
                    "cancelled",
                ),
            )
            reservation = cursor.fetchone()

    response = client.patch(
        f"/reservations/{reservation['id']}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Reservation already cancelled"}


def test_cancel_completed_reservation(client):
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
                    equipment_id,
                    user_id,
                    start_date,
                    end_date
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    equipment["id"],
                    user["id"],
                    today - timedelta(days=5),
                    today - timedelta(days=2),
                ),
            )
            reservation = cursor.fetchone()

    response = client.patch(
        f"/reservations/{reservation['id']}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Completed reservations cannot be cancelled"}


def test_cancel_reservation_not_found(client):
    client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    ).json()

    login_response = client.post(
        "/login",
        json={"email": "user@example.com", "password": "testpassword"},
    )

    token = login_response.json()["access_token"]

    response = client.patch(
        "/reservations/999/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Reservation not found"}


def test_admin_can_cancel_another_users_reservation(client):
    owner = client.post(
        "/register",
        json={"email": "owner@example.com", "password": "testpassword"},
    ).json()

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
                    equipment_id,
                    user_id,
                    start_date,
                    end_date
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    equipment["id"],
                    owner["id"],
                    today + timedelta(days=10),
                    today + timedelta(days=15),
                ),
            )
            reservation = cursor.fetchone()

    admin_login = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    admin_token = admin_login.json()["access_token"]

    response = client.patch(
        f"/reservations/{reservation['id']}/cancel",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_admin_can_get_all_reservations(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    user1 = client.post(
        "/register",
        json={"email": "user1@example.com", "password": "testpassword"},
    ).json()

    user2 = client.post(
        "/register",
        json={"email": "user2@example.com", "password": "testpassword"},
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
                """,
                (
                    user1["id"],
                    equipment["id"],
                    today + timedelta(days=10),
                    today + timedelta(days=12),
                ),
            )

            cursor.execute(
                """
                INSERT INTO reservations (
                    user_id,
                    equipment_id,
                    start_date,
                    end_date
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    user2["id"],
                    equipment["id"],
                    today + timedelta(days=15),
                    today + timedelta(days=17),
                ),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/reservations",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 2

    assert response.json()[0]["user_email"] == "user1@example.com"
    assert response.json()[0]["equipment_name"] == "Basketball"

    assert response.json()[1]["user_email"] == "user2@example.com"
    assert response.json()[1]["equipment_name"] == "Basketball"


def test_normal_user_cannot_get_all_reservations(client):
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
        "/reservations",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_get_all_reservations_requires_authentication(client):
    response = client.get("/reservations")
    assert response.status_code == 401


def test_past_reservation_is_returned_as_completed(client):
    user = client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    ).json()

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
                """,
                (
                    user["id"],
                    equipment["id"],
                    utc_today() - timedelta(days=5),
                    utc_today() - timedelta(days=2),
                ),
            )

    login_response = client.post(
        "/login",
        json={"email": "user@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/reservations/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()[0]["status"] == "completed"


def test_admin_sees_past_reservation_as_completed(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    user = client.post(
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
                """,
                (
                    user["id"],
                    equipment["id"],
                    utc_today() - timedelta(days=5),
                    utc_today() - timedelta(days=2),
                ),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/reservations",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()[0]["status"] == "completed"


def test_create_reservation_rejects_past_start_date(client):
    client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    )

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

    login_response = client.post(
        "/login",
        json={"email": "user@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    today = utc_today()

    response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={
            "start_date": (today - timedelta(days=2)).isoformat(),
            "end_date": (today - timedelta(days=1)).isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Start date cannot be in the past"}


def test_create_reservation_allows_start_date_today(client):
    client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    )

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

    login_response = client.post(
        "/login",
        json={"email": "user@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    today = utc_today()

    response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={
            "start_date": today.isoformat(),
            "end_date": today.isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["equipment_id"] == equipment["id"]
    assert response.json()["start_date"] == today.isoformat()
    assert response.json()["end_date"] == today.isoformat()
    assert response.json()["status"] == "active"


def test_cancelled_reservation_does_not_block_new_reservation(client):
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
                    end_date,
                    status
                )
                VALUES (%s, %s, %s, %s, 'cancelled')
                """,
                (
                    user["id"],
                    equipment["id"],
                    today + timedelta(days=10),
                    today + timedelta(days=15),
                ),
            )

    response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={
            "start_date": (today + timedelta(days=10)).isoformat(),
            "end_date": (today + timedelta(days=15)).isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "active"


def test_reservation_ending_today_can_be_cancelled(client):
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
                    utc_today(),
                ),
            )
            reservation = cursor.fetchone()

    response = client.patch(
        f"/reservations/{reservation['id']}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
