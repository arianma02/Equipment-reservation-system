from datetime import timedelta

from app.time_utils import utc_today


def test_create_reservation(client, auth_user, make_equipment):
    _, headers = auth_user("test@example.com")
    equipment = make_equipment()
    today = utc_today()
    start_date = today + timedelta(days=10)
    end_date = today + timedelta(days=13)

    response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        headers=headers,
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


def test_create_overlapping_reservation_rejected(client, auth_user, make_equipment):
    _, headers = auth_user("test@example.com")
    equipment = make_equipment()
    today = utc_today()

    first_response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={
            "start_date": (today + timedelta(days=10)).isoformat(),
            "end_date": (today + timedelta(days=15)).isoformat(),
        },
        headers=headers,
    )
    second_response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={
            "start_date": (today + timedelta(days=12)).isoformat(),
            "end_date": (today + timedelta(days=14)).isoformat(),
        },
        headers=headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Equipment is already reserved for the selected dates"
    }


def test_create_non_overlapping_reservations(client, auth_user, make_equipment):
    _, headers = auth_user("test@example.com")
    equipment = make_equipment()
    today = utc_today()

    first_response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={
            "start_date": (today + timedelta(days=10)).isoformat(),
            "end_date": (today + timedelta(days=15)).isoformat(),
        },
        headers=headers,
    )
    second_response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={
            "start_date": (today + timedelta(days=16)).isoformat(),
            "end_date": (today + timedelta(days=20)).isoformat(),
        },
        headers=headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201


def test_create_reservation_invalid_date_range(client, auth_user):
    _, headers = auth_user("test@example.com")
    today = utc_today()

    response = client.post(
        "/equipment/999/reservations",
        json={
            "start_date": (today + timedelta(days=10)).isoformat(),
            "end_date": (today + timedelta(days=5)).isoformat(),
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Start date cannot be after end date"}


def test_create_reservation_equipment_not_found(client, auth_user):
    _, headers = auth_user("test@example.com")
    today = utc_today()

    response = client.post(
        "/equipment/999/reservations",
        json={
            "start_date": (today + timedelta(days=10)).isoformat(),
            "end_date": (today + timedelta(days=15)).isoformat(),
        },
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Equipment not found"}


def test_create_reservation_maintenance_equipment_rejected(
    client, auth_user, make_equipment
):
    _, headers = auth_user("test@example.com")
    equipment = make_equipment(status="maintenance")
    today = utc_today()

    response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={
            "start_date": (today + timedelta(days=10)).isoformat(),
            "end_date": (today + timedelta(days=15)).isoformat(),
        },
        headers=headers,
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


def test_create_same_day_reservation(client, auth_user, make_equipment):
    _, headers = auth_user("test@example.com")
    equipment = make_equipment()
    reservation_date = utc_today() + timedelta(days=10)

    response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={
            "start_date": reservation_date.isoformat(),
            "end_date": reservation_date.isoformat(),
        },
        headers=headers,
    )

    assert response.status_code == 201


def test_get_my_reservations_only_returns_current_users_reservation(
    client, auth_user, make_user, make_equipment, make_reservation
):
    user1, headers = auth_user("test1@example.com")
    user2 = make_user("test2@example.com")
    equipment = make_equipment()
    today = utc_today()
    make_reservation(
        user1["id"],
        equipment["id"],
        today + timedelta(days=1),
        today + timedelta(days=5),
    )
    make_reservation(
        user2["id"],
        equipment["id"],
        today + timedelta(days=10),
        today + timedelta(days=15),
    )

    response = client.get("/reservations/me", headers=headers)

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "user_id": 1,
            "equipment_id": 1,
            "equipment_name": "Basketball",
            "start_date": (today + timedelta(days=1)).isoformat(),
            "end_date": (today + timedelta(days=5)).isoformat(),
            "status": "active",
        }
    ]


def test_get_my_reservations_empty(client, auth_user):
    _, headers = auth_user("test@example.com")

    response = client.get("/reservations/me", headers=headers)

    assert response.json() == []
    assert response.status_code == 200


def test_get_my_reservations_requires_authentication(client):
    response = client.get("/reservations/me")
    assert response.status_code == 401


def test_cancel_own_reservation(client, auth_user, make_equipment, make_reservation):
    user, headers = auth_user("test@example.com")
    equipment = make_equipment()
    today = utc_today()
    reservation = make_reservation(
        user["id"],
        equipment["id"],
        today + timedelta(days=10),
        today + timedelta(days=15),
    )

    response = client.patch(
        f"/reservations/{reservation['id']}/cancel",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_cannot_cancel_another_users_reservation(
    client, make_user, auth_user, make_equipment, make_reservation
):
    user1 = make_user("user1@example.com")
    _, user2_headers = auth_user("user2@example.com")
    equipment = make_equipment()
    today = utc_today()
    reservation = make_reservation(
        user1["id"],
        equipment["id"],
        today + timedelta(days=10),
        today + timedelta(days=15),
    )

    response = client.patch(
        f"/reservations/{reservation['id']}/cancel",
        headers=user2_headers,
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Not authorized to cancel this reservation"}


def test_cancel_already_cancelled_reservation(
    client, auth_user, make_equipment, make_reservation
):
    user, headers = auth_user()
    equipment = make_equipment()
    today = utc_today()
    reservation = make_reservation(
        user["id"],
        equipment["id"],
        today + timedelta(days=10),
        today + timedelta(days=15),
        status="cancelled",
    )

    response = client.patch(
        f"/reservations/{reservation['id']}/cancel",
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Reservation already cancelled"}


def test_cancel_completed_reservation(
    client, auth_user, make_equipment, make_reservation
):
    user, headers = auth_user()
    equipment = make_equipment()
    today = utc_today()
    reservation = make_reservation(
        user["id"],
        equipment["id"],
        today - timedelta(days=5),
        today - timedelta(days=2),
    )

    response = client.patch(
        f"/reservations/{reservation['id']}/cancel",
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Completed reservations cannot be cancelled"}


def test_cancel_reservation_not_found(client, auth_user):
    _, headers = auth_user()

    response = client.patch("/reservations/999/cancel", headers=headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Reservation not found"}


def test_admin_can_cancel_another_users_reservation(
    client, make_user, auth_user, make_equipment, make_reservation
):
    owner = make_user("owner@example.com")
    _, admin_headers = auth_user("admin@example.com", role="admin")
    equipment = make_equipment()
    today = utc_today()
    reservation = make_reservation(
        owner["id"],
        equipment["id"],
        today + timedelta(days=10),
        today + timedelta(days=15),
    )

    response = client.patch(
        f"/reservations/{reservation['id']}/cancel",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_admin_can_get_all_reservations(
    client, auth_user, make_user, make_equipment, make_reservation
):
    _, admin_headers = auth_user("admin@example.com", role="admin")
    user1 = make_user("user1@example.com")
    user2 = make_user("user2@example.com")
    equipment = make_equipment()
    today = utc_today()
    make_reservation(
        user1["id"],
        equipment["id"],
        today + timedelta(days=10),
        today + timedelta(days=12),
    )
    make_reservation(
        user2["id"],
        equipment["id"],
        today + timedelta(days=15),
        today + timedelta(days=17),
    )

    response = client.get("/reservations", headers=admin_headers)

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["user_email"] == "user1@example.com"
    assert response.json()[0]["equipment_name"] == "Basketball"
    assert response.json()[1]["user_email"] == "user2@example.com"
    assert response.json()[1]["equipment_name"] == "Basketball"


def test_normal_user_cannot_get_all_reservations(client, auth_user):
    _, headers = auth_user()

    response = client.get("/reservations", headers=headers)

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_get_all_reservations_requires_authentication(client):
    response = client.get("/reservations")
    assert response.status_code == 401


def test_past_reservation_is_returned_as_completed(
    client, auth_user, make_equipment, make_reservation
):
    user, headers = auth_user()
    equipment = make_equipment()
    make_reservation(
        user["id"],
        equipment["id"],
        utc_today() - timedelta(days=5),
        utc_today() - timedelta(days=2),
    )

    response = client.get("/reservations/me", headers=headers)

    assert response.status_code == 200
    assert response.json()[0]["status"] == "completed"


def test_admin_sees_past_reservation_as_completed(
    client, auth_user, make_user, make_equipment, make_reservation
):
    _, admin_headers = auth_user("admin@example.com", role="admin")
    user = make_user()
    equipment = make_equipment()
    make_reservation(
        user["id"],
        equipment["id"],
        utc_today() - timedelta(days=5),
        utc_today() - timedelta(days=2),
    )

    response = client.get("/reservations", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()[0]["status"] == "completed"


def test_create_reservation_rejects_past_start_date(client, auth_user, make_equipment):
    _, headers = auth_user()
    equipment = make_equipment()
    today = utc_today()

    response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={
            "start_date": (today - timedelta(days=2)).isoformat(),
            "end_date": (today - timedelta(days=1)).isoformat(),
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Start date cannot be in the past"}


def test_create_reservation_allows_start_date_today(client, auth_user, make_equipment):
    _, headers = auth_user()
    equipment = make_equipment()
    today = utc_today()

    response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={"start_date": today.isoformat(), "end_date": today.isoformat()},
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["equipment_id"] == equipment["id"]
    assert response.json()["start_date"] == today.isoformat()
    assert response.json()["end_date"] == today.isoformat()
    assert response.json()["status"] == "active"


def test_cancelled_reservation_does_not_block_new_reservation(
    client, auth_user, make_equipment, make_reservation
):
    user, headers = auth_user()
    equipment = make_equipment()
    today = utc_today()
    make_reservation(
        user["id"],
        equipment["id"],
        today + timedelta(days=10),
        today + timedelta(days=15),
        status="cancelled",
    )

    response = client.post(
        f"/equipment/{equipment['id']}/reservations",
        json={
            "start_date": (today + timedelta(days=10)).isoformat(),
            "end_date": (today + timedelta(days=15)).isoformat(),
        },
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "active"


def test_reservation_ending_today_can_be_cancelled(
    client, auth_user, make_equipment, make_reservation
):
    user, headers = auth_user()
    equipment = make_equipment()
    reservation = make_reservation(
        user["id"],
        equipment["id"],
        utc_today() - timedelta(days=2),
        utc_today(),
    )

    response = client.patch(
        f"/reservations/{reservation['id']}/cancel",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
