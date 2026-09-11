from app.database import get_connection


def test_create_reservation(client):
    client.post(
        "/register", json={"email": "test@example.com", "password": "testpassword"}
    )
    login_response = client.post(
        "/login", json={"email": "test@example.com", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]

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

    response = client.post(
        f"/equipment/{equipment["id"]}/reservations",
        json={
            "start_date": "2026-09-15",
            "end_date": "2026-09-18",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    print(response.json())
    assert response.json() == {
        "id": 1,
        "user_id": 1,
        "equipment_id": 1,
        "start_date": "2026-09-15",
        "end_date": "2026-09-18",
        "status": "active",
    }


def test_create_overlapping_reservation_rejected(client):
    client.post(
        "/register", json={"email": "test@example.com", "password": "testpassword"}
    )
    login_response = client.post(
        "/login", json={"email": "test@example.com", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]

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

    first_response = client.post(
        f"/equipment/{equipment["id"]}/reservations",
        json={
            "start_date": "2026-09-10",
            "end_date": "2026-09-15",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    second_response = client.post(
        f"/equipment/{equipment["id"]}/reservations",
        json={
            "start_date": "2026-09-12",
            "end_date": "2026-09-14",
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
        "/register", json={"email": "test@example.com", "password": "testpassword"}
    )
    login_response = client.post(
        "/login", json={"email": "test@example.com", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]

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

    first_response = client.post(
        f"/equipment/{equipment["id"]}/reservations",
        json={
            "start_date": "2026-09-10",
            "end_date": "2026-09-15",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    second_response = client.post(
        f"/equipment/{equipment["id"]}/reservations",
        json={
            "start_date": "2026-09-16",
            "end_date": "2026-09-20",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201


def test_create_reservation_invalid_date_range(client):
    client.post(
        "/register", json={"email": "test@example.com", "password": "testpassword"}
    )
    login_response = client.post(
        "/login", json={"email": "test@example.com", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/equipment/999/reservations",
        json={
            "start_date": "2026-09-15",
            "end_date": "2026-09-14",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Start date cannot be after end date"}


def test_create_reservation_equipment_not_found(client):
    client.post(
        "/register", json={"email": "test@example.com", "password": "testpassword"}
    )
    login_response = client.post(
        "/login", json={"email": "test@example.com", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/equipment/999/reservations",
        json={
            "start_date": "2026-09-15",
            "end_date": "2026-09-20",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Equipment not found"}


def test_create_reservation_maintenance_equipment_rejected(client):
    client.post(
        "/register", json={"email": "test@example.com", "password": "testpassword"}
    )
    login_response = client.post(
        "/login", json={"email": "test@example.com", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id;", ("Sports",)
            )
            category = cursor.fetchone()

            cursor.execute(
                "INSERT INTO equipment (name, asset_tag, category_id, status) VALUES (%s, %s, %s, %s) RETURNING id;",
                ("Basketball", "BB-001", category["id"], "maintenance"),
            )

            equipment = cursor.fetchone()

    response = client.post(
        f"/equipment/{equipment["id"]}/reservations",
        json={
            "start_date": "2026-09-10",
            "end_date": "2026-09-15",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409
    assert response.json() == {"detail": "Equipment is not available for reservation"}


def test_create_reservation_requires_authentication(client):
    response = client.post(
        "/equipment/1/reservations",
        json={
            "start_date": "2026-09-10",
            "end_date": "2026-09-15",
        },
    )

    assert response.status_code == 401


def test_create_same_day_reservation(client):
    client.post(
        "/register", json={"email": "test@example.com", "password": "testpassword"}
    )
    login_response = client.post(
        "/login", json={"email": "test@example.com", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]

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

    first_response = client.post(
        f"/equipment/{equipment["id"]}/reservations",
        json={
            "start_date": "2026-09-15",
            "end_date": "2026-09-15",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert first_response.status_code == 201
