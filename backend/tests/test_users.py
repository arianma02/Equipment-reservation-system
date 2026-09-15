from datetime import timedelta

from app.time_utils import utc_today


def test_user_can_deactivate_own_account(
    client,
    auth_user,
    make_equipment,
    make_reservation,
    get_reservation_status,
):
    user, headers = auth_user()
    equipment = make_equipment()
    today = utc_today()
    reservation = make_reservation(
        user["id"],
        equipment["id"],
        today + timedelta(days=10),
        today + timedelta(days=15),
    )

    response = client.patch("/users/me/deactivate", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "disabled"
    assert get_reservation_status(reservation["id"]) == "cancelled"


def test_deactivation_keeps_past_reservations(
    client,
    auth_user,
    make_equipment,
    make_reservation,
    get_reservation_status,
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

    response = client.patch("/users/me/deactivate", headers=headers)

    assert response.status_code == 200
    assert get_reservation_status(reservation["id"]) == "active"


def test_deactivate_requires_authentication(client):
    response = client.patch("/users/me/deactivate")
    assert response.status_code == 401


def test_last_active_admin_cannot_deactivate_self(client, auth_user, get_user_status):
    admin, headers = auth_user("admin@example.com", role="admin")

    response = client.patch("/users/me/deactivate", headers=headers)

    assert response.status_code == 409
    assert response.json() == {"detail": "Cannot deactivate the last active admin"}
    assert get_user_status(admin["id"]) == "active"


def test_admin_can_deactivate_self_when_another_active_admin_exists(
    client, auth_user, make_user
):
    admin1, headers = auth_user("admin1@example.com", role="admin")
    make_user("admin2@example.com", role="admin")

    response = client.patch("/users/me/deactivate", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "disabled"


def test_admin_can_get_users(client, auth_user, make_user):
    _, headers = auth_user("admin@example.com", role="admin")
    make_user()

    response = client.get("/users", headers=headers)

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


def test_normal_user_cannot_get_users(client, auth_user):
    _, headers = auth_user()

    response = client.get("/users", headers=headers)

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_get_users_requires_authentication(client):
    response = client.get("/users")
    assert response.status_code == 401


def test_admin_can_disable_user(client, auth_user, make_user):
    _, headers = auth_user("admin@example.com", role="admin")
    target_user = make_user()

    response = client.patch(
        f"/users/{target_user['id']}",
        json={"status": "disabled"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == target_user["id"]
    assert response.json()["status"] == "disabled"
    assert response.json()["role"] == "user"


def test_cannot_disable_last_active_admin(client, auth_user):
    admin, headers = auth_user("admin@example.com", role="admin")

    response = client.patch(
        f"/users/{admin['id']}",
        json={"status": "disabled"},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Cannot remove the last active admin"}


def test_admin_can_disable_admin_when_another_active_admin_exists(client, auth_user):
    admin1, headers = auth_user("admin1@example.com", role="admin")
    auth_user("admin2@example.com", role="admin")

    response = client.patch(
        f"/users/{admin1['id']}",
        json={"status": "disabled"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "disabled"
    assert response.json()["role"] == "admin"


def test_cannot_demote_last_active_admin(client, auth_user):
    admin, headers = auth_user("admin@example.com", role="admin")

    response = client.patch(
        f"/users/{admin['id']}",
        json={"role": "user"},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Cannot remove the last active admin"}


def test_admin_can_demote_admin_when_another_active_admin_exists(client, auth_user):
    _, headers = auth_user("admin1@example.com", role="admin")
    admin2, _ = auth_user("admin2@example.com", role="admin")

    response = client.patch(
        f"/users/{admin2['id']}",
        json={"role": "user"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["role"] == "user"
    assert response.json()["status"] == "active"


def test_disabling_user_cancels_future_reservations(
    client,
    auth_user,
    make_user,
    make_equipment,
    make_reservation,
    get_reservation_status,
):
    _, headers = auth_user("admin@example.com", role="admin")
    target_user = make_user()
    equipment = make_equipment()
    reservation = make_reservation(
        target_user["id"],
        equipment["id"],
        utc_today() + timedelta(days=1),
        utc_today() + timedelta(days=3),
    )

    response = client.patch(
        f"/users/{target_user['id']}",
        json={"status": "disabled"},
        headers=headers,
    )

    assert response.status_code == 200
    assert get_reservation_status(reservation["id"]) == "cancelled"


def test_disabling_user_keeps_past_reservations(
    client,
    auth_user,
    make_user,
    make_equipment,
    make_reservation,
    get_reservation_status,
):
    _, headers = auth_user("admin@example.com", role="admin")
    target_user = make_user()
    equipment = make_equipment()
    reservation = make_reservation(
        target_user["id"],
        equipment["id"],
        utc_today() - timedelta(days=5),
        utc_today() - timedelta(days=2),
    )

    response = client.patch(
        f"/users/{target_user['id']}",
        json={"status": "disabled"},
        headers=headers,
    )

    assert response.status_code == 200
    assert get_reservation_status(reservation["id"]) == "active"


def test_normal_user_cannot_update_users(client, auth_user, make_user):
    _, headers = auth_user()
    target_user = make_user("target@example.com")

    response = client.patch(
        f"/users/{target_user['id']}",
        json={"status": "disabled"},
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_admin_gets_404_when_updating_missing_user(client, auth_user):
    _, headers = auth_user("admin@example.com", role="admin")

    response = client.patch(
        "/users/999",
        json={"status": "disabled"},
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_admin_can_promote_user_to_admin(client, auth_user, make_user):
    _, headers = auth_user("admin@example.com", role="admin")
    target_user = make_user()

    response = client.patch(
        f"/users/{target_user['id']}",
        json={"role": "admin"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    assert response.json()["status"] == "active"


def test_admin_cannot_set_invalid_role(client, auth_user, make_user):
    _, headers = auth_user("admin@example.com", role="admin")
    target_user = make_user()

    response = client.patch(
        f"/users/{target_user['id']}",
        json={"role": "superadmin"},
        headers=headers,
    )

    assert response.status_code == 422


def test_admin_cannot_set_invalid_status(client, auth_user, make_user):
    _, headers = auth_user("admin@example.com", role="admin")
    target_user = make_user()

    response = client.patch(
        f"/users/{target_user['id']}",
        json={"status": "banned"},
        headers=headers,
    )

    assert response.status_code == 422


def test_disabling_user_cancels_in_progress_reservation(
    client,
    auth_user,
    make_user,
    make_equipment,
    make_reservation,
    get_reservation_status,
):
    _, headers = auth_user("admin@example.com", role="admin")
    target_user = make_user()
    equipment = make_equipment()
    reservation = make_reservation(
        target_user["id"],
        equipment["id"],
        utc_today() - timedelta(days=2),
        utc_today() + timedelta(days=2),
    )

    response = client.patch(
        f"/users/{target_user['id']}",
        json={"status": "disabled"},
        headers=headers,
    )

    assert response.status_code == 200
    assert get_reservation_status(reservation["id"]) == "cancelled"


def test_deactivation_cancels_in_progress_reservation(
    client,
    auth_user,
    make_equipment,
    make_reservation,
    get_reservation_status,
):
    user, headers = auth_user()
    equipment = make_equipment()
    reservation = make_reservation(
        user["id"],
        equipment["id"],
        utc_today() - timedelta(days=2),
        utc_today() + timedelta(days=2),
    )

    response = client.patch("/users/me/deactivate", headers=headers)

    assert response.status_code == 200
    assert get_reservation_status(reservation["id"]) == "cancelled"


def test_admin_can_reenable_disabled_user(client, auth_user, make_user):
    _, headers = auth_user("admin@example.com", role="admin")
    target_user = make_user()

    disable_response = client.patch(
        f"/users/{target_user['id']}",
        json={"status": "disabled"},
        headers=headers,
    )
    assert disable_response.status_code == 200
    assert disable_response.json()["status"] == "disabled"

    enable_response = client.patch(
        f"/users/{target_user['id']}",
        json={"status": "active"},
        headers=headers,
    )
    assert enable_response.status_code == 200
    assert enable_response.json()["status"] == "active"

    user_login = client.post(
        "/login",
        json={"email": "user@example.com", "password": "testpassword"},
    )
    assert user_login.status_code == 200
