from app.database import get_connection
from datetime import date, timedelta


def test_get_equipment_empty(client):
    response = client.get("/equipment")
    assert response.status_code == 200
    assert response.json() == []


def test_get_equipment(client):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id;", ("Sports",)
            )
            category = cursor.fetchone()

            cursor.execute(
                "INSERT INTO equipment (name, asset_tag, category_id) VALUES (%s, %s, %s);",
                ("Basketball", "BB-001", category["id"]),
            )
    response = client.get("/equipment")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "name": "Basketball",
            "asset_tag": "BB-001",
            "category_id": 1,
            "category_name": "Sports",
            "status": "active",
        }
    ]


def test_get_equipment_by_id(client):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id;", ("Sports",)
            )
            category = cursor.fetchone()

            cursor.execute(
                "INSERT INTO equipment (name, asset_tag, category_id) VALUES (%s, %s, %s);",
                ("Basketball", "BB-001", category["id"]),
            )

    response = client.get("/equipment/1")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Basketball",
        "asset_tag": "BB-001",
        "category_id": 1,
        "category_name": "Sports",
        "status": "active",
    }


def test_get_equipment_by_id_not_found(client):
    response = client.get("/equipment/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Equipment not found"}


def test_get_equipment_by_category(client):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s), (%s) RETURNING id;",
                ("Sports", "Cameras"),
            )
            category = cursor.fetchall()

            cursor.execute(
                "INSERT INTO equipment (name, asset_tag, category_id) VALUES (%s, %s, %s), (%s, %s, %s);",
                (
                    "Basketball",
                    "BB-001",
                    category[0]["id"],
                    "Camera",
                    "CAM-001",
                    category[1]["id"],
                ),
            )
    response = client.get("/equipment?category_id=1")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "name": "Basketball",
            "asset_tag": "BB-001",
            "category_id": 1,
            "category_name": "Sports",
            "status": "active",
        }
    ]


def test_get_equipment_by_status(client):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s), (%s) RETURNING id;",
                ("Sports", "Cameras"),
            )
            category = cursor.fetchall()

            cursor.execute(
                "INSERT INTO equipment (name, asset_tag, category_id, status) VALUES (%s, %s, %s, %s), (%s, %s, %s, %s);",
                (
                    "Basketball",
                    "BB-001",
                    category[0]["id"],
                    "active",
                    "Camera",
                    "CAM-001",
                    category[1]["id"],
                    "retired",
                ),
            )
    response = client.get("/equipment?status=active")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "name": "Basketball",
            "asset_tag": "BB-001",
            "category_id": 1,
            "category_name": "Sports",
            "status": "active",
        }
    ]


def test_get_equipment_invalid_status(client):
    response = client.get("/equipment?status=broken")
    assert response.status_code == 422


def test_get_equipment_by_category_and_status(client):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s), (%s) RETURNING id;",
                ("Sports", "Cameras"),
            )
            category = cursor.fetchall()

            cursor.execute(
                "INSERT INTO equipment (name, asset_tag, category_id, status) VALUES (%s, %s, %s, %s), (%s, %s, %s, %s), (%s, %s, %s, %s);",
                (
                    "Basketball",
                    "BB-001",
                    category[0]["id"],
                    "active",
                    "Camera",
                    "CAM-001",
                    category[1]["id"],
                    "active",
                    "Tripod",
                    "TR-001",
                    category[0]["id"],
                    "maintenance",
                ),
            )
    response = client.get("/equipment?category_id=1&status=active")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "name": "Basketball",
            "asset_tag": "BB-001",
            "category_id": 1,
            "category_name": "Sports",
            "status": "active",
        }
    ]


def test_equipment_available_when_no_reservations(client):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id;", ("Sports",)
            )
            category = cursor.fetchone()

            cursor.execute(
                "INSERT INTO equipment (name, asset_tag, category_id) VALUES (%s, %s, %s);",
                ("Basketball", "BB-001", category["id"]),
            )

    response = client.get(
        "/equipment/1/availability?start_date=2026-09-15&end_date=2026-09-18"
    )
    assert response.status_code == 200
    assert response.json() == {"available": True}


def test_equipment_unavailable_when_reservation_overlaps(client):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id;", ("Sports",)
            )
            category = cursor.fetchone()

            cursor.execute(
                "INSERT INTO equipment (name, asset_tag, category_id) VALUES (%s, %s, %s) RETURNING id;",
                ("Basketball", "BB-001", category["id"]),
            )
            equipment = cursor.fetchone()

            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id;",
                ("test@example.com", "fake-hash"),
            )

            user = cursor.fetchone()

            cursor.execute(
                "INSERT INTO reservations (equipment_id, user_id, start_date, end_date) VALUES (%s, %s, %s, %s);",
                (equipment["id"], user["id"], "2026-09-10", "2026-09-15"),
            )

    response = client.get(
        "/equipment/1/availability?start_date=2026-09-15&end_date=2026-09-18"
    )
    assert response.status_code == 200
    assert response.json() == {"available": False}


def test_equipment_available_when_reservation_does_not_overlap(client):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id;", ("Sports",)
            )
            category = cursor.fetchone()

            cursor.execute(
                "INSERT INTO equipment (name, asset_tag, category_id) VALUES (%s, %s, %s) RETURNING id;",
                ("Basketball", "BB-001", category["id"]),
            )
            equipment = cursor.fetchone()

            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id;",
                ("test@example.com", "fake-hash"),
            )

            user = cursor.fetchone()

            cursor.execute(
                "INSERT INTO reservations (equipment_id, user_id, start_date, end_date) VALUES (%s, %s, %s, %s);",
                (equipment["id"], user["id"], "2026-09-10", "2026-09-15"),
            )

    response = client.get(
        "/equipment/1/availability?start_date=2026-09-16&end_date=2026-09-20"
    )
    assert response.status_code == 200
    assert response.json() == {"available": True}


def test_equipment_unavailable_when_not_active(client):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id;", ("Sports",)
            )
            category = cursor.fetchone()

            cursor.execute(
                "INSERT INTO equipment (name, asset_tag, category_id, status) VALUES (%s, %s, %s, %s) "
                "RETURNING id;",
                ("Basketball", "BB-001", category["id"], "maintenance"),
            )

            equipment = cursor.fetchone()

    response = client.get(
        f"/equipment/{equipment['id']}/availability?start_date=2026-09-16&end_date=2026-09-20"
    )
    assert response.status_code == 200
    assert response.json() == {"available": False}


def test_equipment_availability_invalid_date_range(client):
    response = client.get(
        "/equipment/1/availability?start_date=2026-09-20&end_date=2026-09-16"
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Start date cannot be after end date"}


def test_equipment_availability_not_found(client):
    response = client.get(
        "/equipment/999/availability?start_date=2026-09-16&end_date=2026-09-20"
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Equipment not found"}


def test_admin_can_create_equipment(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
                ("Sports",),
            )
            category = cursor.fetchone()

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/equipment",
        json={
            "name": "Basketball",
            "asset_tag": "BB-001",
            "category_id": category["id"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "Basketball",
        "asset_tag": "BB-001",
        "category_id": category["id"],
        "category_name": "Sports",
        "status": "active",
    }


def test_normal_user_cannot_create_equipment(client):
    user = client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
                ("Sports",),
            )
            category = cursor.fetchone()

    login_response = client.post(
        "/login",
        json={"email": "user@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/equipment",
        json={
            "name": "Basketball",
            "asset_tag": "BB-001",
            "category_id": category["id"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_create_equipment_requires_authentication(client):
    response = client.post(
        "/equipment",
        json={
            "name": "Basketball",
            "asset_tag": "BB-001",
            "category_id": 1,
        },
    )

    assert response.status_code == 401


def test_admin_cannot_create_equipment_with_missing_category(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]
    response = client.post(
        "/equipment",
        json={
            "name": "Basketball",
            "asset_tag": "BB-001",
            "category_id": 999,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Category not found"}


def test_admin_cannot_create_duplicate_asset_tag(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
                ("Sports",),
            )
            category = cursor.fetchone()

            cursor.execute(
                """
                INSERT INTO equipment (name, asset_tag, category_id)
                VALUES (%s, %s, %s)
                """,
                ("Basketball", "BB-001", category["id"]),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/equipment",
        json={
            "name": "Basketball",
            "asset_tag": "BB-001",
            "category_id": category["id"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Asset tag already exists"}


def test_admin_can_update_equipment_name(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
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
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"name": "Indoor Basketball"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": equipment["id"],
        "name": "Indoor Basketball",
        "asset_tag": "BB-001",
        "category_id": category["id"],
        "category_name": "Sports",
        "status": "active",
    }


def test_admin_can_change_equipment_category(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
                ("Sports",),
            )
            sports = cursor.fetchone()

            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
                ("Training",),
            )
            training = cursor.fetchone()

            cursor.execute(
                """
                INSERT INTO equipment (name, asset_tag, category_id)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                ("Basketball", "BB-001", sports["id"]),
            )
            equipment = cursor.fetchone()

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"category_id": training["id"]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["category_id"] == training["id"]
    assert response.json()["category_name"] == "Training"


def test_setting_equipment_to_maintenance_cancels_future_reservations(client):
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
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
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
                    date.today() + timedelta(days=1),
                    date.today() + timedelta(days=3),
                ),
            )
            reservation = cursor.fetchone()

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"status": "maintenance"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "maintenance"

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT status FROM reservations WHERE id = %s",
                (reservation["id"],),
            )
            updated_reservation = cursor.fetchone()

    assert updated_reservation["status"] == "cancelled"


def test_setting_equipment_to_maintenance_keeps_past_reservations(client):
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
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
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
                    date.today() - timedelta(days=5),
                    date.today() - timedelta(days=2),
                ),
            )
            reservation = cursor.fetchone()

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"status": "maintenance"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT status FROM reservations WHERE id = %s",
                (reservation["id"],),
            )
            updated_reservation = cursor.fetchone()

    assert updated_reservation["status"] == "active"


def test_cannot_retire_equipment_with_active_reservations(client):
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
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
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
                    date.today() + timedelta(days=1),
                    date.today() + timedelta(days=3),
                ),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"status": "retired"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Cannot retire equipment with active reservations"
    }


def test_admin_can_retire_equipment_without_active_reservations(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
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
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"status": "retired"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "retired"


def test_admin_gets_404_when_updating_missing_equipment(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        "/equipment/999",
        json={"name": "Indoor Basketball"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Equipment not found"}


def test_admin_cannot_update_equipment_to_missing_category(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
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
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"category_id": 999},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Category not found"}


def test_admin_cannot_update_equipment_to_duplicate_asset_tag(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
                ("Sports",),
            )
            category = cursor.fetchone()

            cursor.execute(
                """
                INSERT INTO equipment (name, asset_tag, category_id)
                VALUES (%s, %s, %s)
                """,
                ("Basketball", "BB-001", category["id"]),
            )

            cursor.execute(
                """
                INSERT INTO equipment (name, asset_tag, category_id)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                ("Basketball 2", "BB-002", category["id"]),
            )
            equipment = cursor.fetchone()

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"asset_tag": "BB-001"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Asset tag already exists"}


def test_normal_user_cannot_update_equipment(client):
    user = client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
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

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"name": "Indoor Basketball"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_update_equipment_requires_authentication(client):
    response = client.patch(
        "/equipment/1",
        json={"name": "Indoor Basketball"},
    )

    assert response.status_code == 401


def test_admin_cannot_set_invalid_equipment_status(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
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
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"status": "broken"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_availability_rejects_past_start_date(client):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
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

    today = date.today()

    response = client.get(
        f"/equipment/{equipment['id']}/availability",
        params={
            "start_date": (today - timedelta(days=2)).isoformat(),
            "end_date": (today - timedelta(days=1)).isoformat(),
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Start date cannot be in the past"}


def test_availability_allows_start_date_today(client):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
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

    today = date.today()

    response = client.get(
        f"/equipment/{equipment['id']}/availability",
        params={
            "start_date": today.isoformat(),
            "end_date": today.isoformat(),
        },
    )

    assert response.status_code == 200
    assert response.json() == {"available": True}
