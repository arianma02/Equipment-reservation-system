from app.database import get_connection


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
                (user["id"], equipment["id"], "2026-09-10", "2026-09-15"),
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
                (user["id"], equipment["id"], "2026-09-10", "2026-09-15"),
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
