from datetime import timedelta

from app.time_utils import utc_today


def test_get_equipment_empty(client):
    response = client.get("/equipment")
    assert response.status_code == 200
    assert response.json() == []


def test_get_equipment(client, make_equipment):
    make_equipment()

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


def test_get_equipment_by_id(client, make_equipment):
    equipment = make_equipment()

    response = client.get(f"/equipment/{equipment['id']}")

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


def test_get_equipment_by_category(client, make_category, make_equipment):
    sports = make_category("Sports")
    cameras = make_category("Cameras")
    make_equipment(category_id=sports["id"])
    make_equipment("Camera", "CAM-001", cameras["id"])

    response = client.get(f"/equipment?category_id={sports['id']}")

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


def test_get_equipment_by_status(client, make_category, make_equipment):
    sports = make_category("Sports")
    cameras = make_category("Cameras")
    make_equipment(category_id=sports["id"])
    make_equipment("Camera", "CAM-001", cameras["id"], status="retired")

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


def test_get_equipment_by_category_and_status(client, make_category, make_equipment):
    sports = make_category("Sports")
    cameras = make_category("Cameras")
    make_equipment(category_id=sports["id"])
    make_equipment("Camera", "CAM-001", cameras["id"])
    make_equipment("Tripod", "TR-001", sports["id"], status="maintenance")

    response = client.get(f"/equipment?category_id={sports['id']}&status=active")

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


def test_equipment_available_when_no_reservations(client, make_equipment):
    equipment = make_equipment()
    today = utc_today()

    response = client.get(
        f"/equipment/{equipment['id']}/availability",
        params={
            "start_date": (today + timedelta(days=10)).isoformat(),
            "end_date": (today + timedelta(days=13)).isoformat(),
        },
    )

    assert response.status_code == 200
    assert response.json() == {"available": True}


def test_equipment_unavailable_when_reservation_overlaps(
    client, make_db_user, make_equipment, make_reservation
):
    equipment = make_equipment()
    user = make_db_user("test@example.com")
    today = utc_today()
    make_reservation(
        user["id"],
        equipment["id"],
        today + timedelta(days=10),
        today + timedelta(days=15),
    )

    response = client.get(
        f"/equipment/{equipment['id']}/availability",
        params={
            "start_date": (today + timedelta(days=15)).isoformat(),
            "end_date": (today + timedelta(days=18)).isoformat(),
        },
    )

    assert response.status_code == 200
    assert response.json() == {"available": False}


def test_equipment_available_when_reservation_does_not_overlap(
    client, make_db_user, make_equipment, make_reservation
):
    equipment = make_equipment()
    user = make_db_user("test@example.com")
    today = utc_today()
    make_reservation(
        user["id"],
        equipment["id"],
        today + timedelta(days=10),
        today + timedelta(days=15),
    )

    response = client.get(
        f"/equipment/{equipment['id']}/availability",
        params={
            "start_date": (today + timedelta(days=16)).isoformat(),
            "end_date": (today + timedelta(days=20)).isoformat(),
        },
    )

    assert response.status_code == 200
    assert response.json() == {"available": True}


def test_equipment_unavailable_when_not_active(client, make_equipment):
    equipment = make_equipment(status="maintenance")
    today = utc_today()

    response = client.get(
        f"/equipment/{equipment['id']}/availability",
        params={
            "start_date": (today + timedelta(days=10)).isoformat(),
            "end_date": (today + timedelta(days=15)).isoformat(),
        },
    )

    assert response.status_code == 200
    assert response.json() == {"available": False}


def test_equipment_availability_invalid_date_range(client):
    today = utc_today()
    response = client.get(
        "/equipment/1/availability",
        params={
            "start_date": (today + timedelta(days=10)).isoformat(),
            "end_date": (today + timedelta(days=5)).isoformat(),
        },
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Start date cannot be after end date"}


def test_equipment_availability_not_found(client):
    today = utc_today()
    response = client.get(
        "/equipment/999/availability",
        params={
            "start_date": (today + timedelta(days=10)).isoformat(),
            "end_date": (today + timedelta(days=15)).isoformat(),
        },
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Equipment not found"}


def test_admin_can_create_equipment(client, auth_user, make_category):
    _, headers = auth_user("admin@example.com", role="admin")
    category = make_category()

    response = client.post(
        "/equipment",
        json={
            "name": "Basketball",
            "asset_tag": "BB-001",
            "category_id": category["id"],
        },
        headers=headers,
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


def test_normal_user_cannot_create_equipment(client, auth_user, make_category):
    _, headers = auth_user()
    category = make_category()

    response = client.post(
        "/equipment",
        json={
            "name": "Basketball",
            "asset_tag": "BB-001",
            "category_id": category["id"],
        },
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_create_equipment_requires_authentication(client):
    response = client.post(
        "/equipment",
        json={"name": "Basketball", "asset_tag": "BB-001", "category_id": 1},
    )
    assert response.status_code == 401


def test_admin_cannot_create_equipment_with_missing_category(client, auth_user):
    _, headers = auth_user("admin@example.com", role="admin")

    response = client.post(
        "/equipment",
        json={"name": "Basketball", "asset_tag": "BB-001", "category_id": 999},
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Category not found"}


def test_admin_cannot_create_duplicate_asset_tag(
    client, auth_user, make_category, make_equipment
):
    _, headers = auth_user("admin@example.com", role="admin")
    category = make_category()
    make_equipment(category_id=category["id"])

    response = client.post(
        "/equipment",
        json={
            "name": "Basketball",
            "asset_tag": "BB-001",
            "category_id": category["id"],
        },
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Asset tag already exists"}


def test_admin_can_update_equipment_name(
    client, auth_user, make_category, make_equipment
):
    _, headers = auth_user("admin@example.com", role="admin")
    category = make_category()
    equipment = make_equipment(category_id=category["id"])

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"name": "Indoor Basketball"},
        headers=headers,
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


def test_admin_can_change_equipment_category(
    client, auth_user, make_category, make_equipment
):
    _, headers = auth_user("admin@example.com", role="admin")
    sports = make_category("Sports")
    training = make_category("Training")
    equipment = make_equipment(category_id=sports["id"])

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"category_id": training["id"]},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["category_id"] == training["id"]
    assert response.json()["category_name"] == "Training"


def test_setting_equipment_to_maintenance_cancels_future_reservations(
    client,
    auth_user,
    make_user,
    make_equipment,
    make_reservation,
    get_reservation_status,
):
    _, headers = auth_user("admin@example.com", role="admin")
    user = make_user()
    equipment = make_equipment()
    reservation = make_reservation(
        user["id"],
        equipment["id"],
        utc_today() + timedelta(days=1),
        utc_today() + timedelta(days=3),
    )

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"status": "maintenance"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "maintenance"
    assert get_reservation_status(reservation["id"]) == "cancelled"


def test_setting_equipment_to_maintenance_keeps_past_reservations(
    client,
    auth_user,
    make_user,
    make_equipment,
    make_reservation,
    get_reservation_status,
):
    _, headers = auth_user("admin@example.com", role="admin")
    user = make_user()
    equipment = make_equipment()
    reservation = make_reservation(
        user["id"],
        equipment["id"],
        utc_today() - timedelta(days=5),
        utc_today() - timedelta(days=2),
    )

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"status": "maintenance"},
        headers=headers,
    )

    assert response.status_code == 200
    assert get_reservation_status(reservation["id"]) == "active"


def test_cannot_retire_equipment_with_active_reservations(
    client, auth_user, make_user, make_equipment, make_reservation
):
    _, headers = auth_user("admin@example.com", role="admin")
    user = make_user()
    equipment = make_equipment()
    make_reservation(
        user["id"],
        equipment["id"],
        utc_today() + timedelta(days=1),
        utc_today() + timedelta(days=3),
    )

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"status": "retired"},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Cannot retire equipment with active reservations"
    }


def test_admin_can_retire_equipment_without_active_reservations(
    client, auth_user, make_equipment
):
    _, headers = auth_user("admin@example.com", role="admin")
    equipment = make_equipment()

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"status": "retired"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "retired"


def test_admin_gets_404_when_updating_missing_equipment(client, auth_user):
    _, headers = auth_user("admin@example.com", role="admin")

    response = client.patch(
        "/equipment/999",
        json={"name": "Indoor Basketball"},
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Equipment not found"}


def test_admin_cannot_update_equipment_to_missing_category(
    client, auth_user, make_equipment
):
    _, headers = auth_user("admin@example.com", role="admin")
    equipment = make_equipment()

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"category_id": 999},
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Category not found"}


def test_admin_cannot_update_equipment_to_duplicate_asset_tag(
    client, auth_user, make_category, make_equipment
):
    _, headers = auth_user("admin@example.com", role="admin")
    category = make_category()
    make_equipment(category_id=category["id"])
    equipment = make_equipment("Basketball 2", "BB-002", category["id"])

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"asset_tag": "BB-001"},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Asset tag already exists"}


def test_normal_user_cannot_update_equipment(client, auth_user, make_equipment):
    _, headers = auth_user()
    equipment = make_equipment()

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"name": "Indoor Basketball"},
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_update_equipment_requires_authentication(client):
    response = client.patch("/equipment/1", json={"name": "Indoor Basketball"})
    assert response.status_code == 401


def test_admin_cannot_set_invalid_equipment_status(client, auth_user, make_equipment):
    _, headers = auth_user("admin@example.com", role="admin")
    equipment = make_equipment()

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"status": "broken"},
        headers=headers,
    )

    assert response.status_code == 422


def test_availability_rejects_past_start_date(client, make_equipment):
    equipment = make_equipment()
    today = utc_today()

    response = client.get(
        f"/equipment/{equipment['id']}/availability",
        params={
            "start_date": (today - timedelta(days=2)).isoformat(),
            "end_date": (today - timedelta(days=1)).isoformat(),
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Start date cannot be in the past"}


def test_availability_allows_start_date_today(client, make_equipment):
    equipment = make_equipment()
    today = utc_today()

    response = client.get(
        f"/equipment/{equipment['id']}/availability",
        params={"start_date": today.isoformat(), "end_date": today.isoformat()},
    )

    assert response.status_code == 200
    assert response.json() == {"available": True}


def test_cancelled_reservation_does_not_block_availability(
    client, make_db_user, make_equipment, make_reservation
):
    equipment = make_equipment()
    user = make_db_user()
    today = utc_today()
    make_reservation(
        user["id"],
        equipment["id"],
        today + timedelta(days=10),
        today + timedelta(days=15),
        status="cancelled",
    )

    response = client.get(
        f"/equipment/{equipment['id']}/availability",
        params={
            "start_date": (today + timedelta(days=10)).isoformat(),
            "end_date": (today + timedelta(days=15)).isoformat(),
        },
    )

    assert response.status_code == 200
    assert response.json() == {"available": True}


def test_setting_equipment_to_maintenance_cancels_in_progress_reservation(
    client,
    auth_user,
    make_user,
    make_equipment,
    make_reservation,
    get_reservation_status,
):
    _, headers = auth_user("admin@example.com", role="admin")
    user = make_user()
    equipment = make_equipment()
    reservation = make_reservation(
        user["id"],
        equipment["id"],
        utc_today() - timedelta(days=2),
        utc_today() + timedelta(days=2),
    )

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"status": "maintenance"},
        headers=headers,
    )

    assert response.status_code == 200
    assert get_reservation_status(reservation["id"]) == "cancelled"


def test_cannot_retire_equipment_with_in_progress_reservation(
    client, auth_user, make_user, make_equipment, make_reservation
):
    _, headers = auth_user("admin@example.com", role="admin")
    user = make_user()
    equipment = make_equipment()
    make_reservation(
        user["id"],
        equipment["id"],
        utc_today() - timedelta(days=2),
        utc_today() + timedelta(days=2),
    )

    response = client.patch(
        f"/equipment/{equipment['id']}",
        json={"status": "retired"},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Cannot retire equipment with active reservations"
    }
