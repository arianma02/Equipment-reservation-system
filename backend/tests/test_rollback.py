from datetime import timedelta

from app.time_utils import utc_today


def test_failed_maintenance_update_rolls_back_cancellations(
    client,
    auth_user,
    make_equipment,
    make_reservation,
    get_reservation_status,
):
    user, headers = auth_user("admin@example.com", role="admin")
    equipment = make_equipment(asset_tag="ORIGINAL")
    other = make_equipment(asset_tag="TAKEN", category_id=equipment["category_id"])
    dates = {
        "start_date": utc_today() + timedelta(days=1),
        "end_date": utc_today() + timedelta(days=2),
    }
    reservation = make_reservation(user["id"], equipment["id"], **dates)
    response = client.patch(
        f"/equipment/{equipment['id']}",
        headers=headers,
        json={"status": "maintenance", "asset_tag": other["asset_tag"]},
    )
    assert response.status_code == 409
    assert get_reservation_status(reservation["id"]) == "active"
    current = client.get(f"/equipment/{equipment['id']}").json()
    assert current["status"] == "active"
    assert current["asset_tag"] == "ORIGINAL"
    # A subsequent valid transaction still commits normally.
    assert (
        client.patch(
            f"/equipment/{equipment['id']}",
            headers=headers,
            json={"status": "maintenance"},
        ).status_code
        == 200
    )
    assert get_reservation_status(reservation["id"]) == "cancelled"


def test_booking_conflict_does_not_poison_next_transaction(
    client, auth_user, make_equipment
):
    _, headers = auth_user()
    equipment = make_equipment()
    path = f"/equipment/{equipment['id']}/reservations"
    today = utc_today()
    first = {
        "start_date": str(today + timedelta(days=1)),
        "end_date": str(today + timedelta(days=2)),
    }
    assert client.post(path, headers=headers, json=first).status_code == 201
    assert client.post(path, headers=headers, json=first).status_code == 409
    next_dates = {
        "start_date": str(today + timedelta(days=3)),
        "end_date": str(today + timedelta(days=4)),
    }
    assert client.post(path, headers=headers, json=next_dates).status_code == 201
    assert len(client.get("/reservations/me", headers=headers).json()) == 2
