from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from time import monotonic, sleep

from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app
from app.time_utils import utc_today


def wait_for_two_blocked_connections(blocker_pid):
    deadline = monotonic() + 10
    with get_connection() as observer:
        observer.autocommit = True
        while monotonic() < deadline:
            with observer.cursor() as cursor:
                cursor.execute(
                    """
                    WITH RECURSIVE blocked(pid) AS (
                        SELECT %s::integer
                        UNION
                        SELECT activity.pid
                        FROM pg_stat_activity activity
                        JOIN blocked ON blocked.pid = ANY(pg_blocking_pids(activity.pid))
                        WHERE activity.datname = current_database()
                    )
                    SELECT count(*) - 1 AS count FROM blocked
                    """,
                    (blocker_pid,),
                )
                if cursor.fetchone()["count"] >= 2:
                    return
            sleep(0.02)
    raise AssertionError("Requests did not genuinely contend for the database lock")


def request(method, path, headers, payload=None):
    with TestClient(app) as client:
        return client.request(method, path, headers=headers, json=payload)


def test_two_users_cannot_book_overlapping_dates(auth_user, make_equipment):
    _, first = auth_user("first@example.com")
    _, second = auth_user("second@example.com")
    equipment = make_equipment()
    dates = {
        "start_date": (utc_today() + timedelta(days=1)).isoformat(),
        "end_date": (utc_today() + timedelta(days=3)).isoformat(),
    }
    path = f"/equipment/{equipment['id']}/reservations"
    with ThreadPoolExecutor(max_workers=2) as pool:
        with get_connection() as blocker:
            with blocker.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM equipment WHERE id = %s FOR UPDATE",
                    (equipment["id"],),
                )
            futures = [
                pool.submit(request, "POST", path, headers, dates)
                for headers in (first, second)
            ]
            try:
                wait_for_two_blocked_connections(blocker.info.backend_pid)
            finally:
                blocker.rollback()
        responses = [future.result(timeout=15) for future in futures]
    assert sorted(response.status_code for response in responses) == [201, 409]
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT count(*) AS count FROM reservations WHERE equipment_id = %s",
            (equipment["id"],),
        )
        assert cursor.fetchone()["count"] == 1


def test_concurrent_admin_demotions_preserve_one_admin(auth_user):
    first, first_headers = auth_user("first-admin@example.com", role="admin")
    second, second_headers = auth_user("second-admin@example.com", role="admin")
    with ThreadPoolExecutor(max_workers=2) as pool:
        with get_connection() as blocker:
            with blocker.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(73241, 1)")
            futures = [
                pool.submit(
                    request, "PATCH", f"/users/{user['id']}", headers, {"role": "user"}
                )
                for user, headers in ((first, first_headers), (second, second_headers))
            ]
            try:
                wait_for_two_blocked_connections(blocker.info.backend_pid)
            finally:
                blocker.rollback()
        responses = [future.result(timeout=15) for future in futures]
    assert sorted(response.status_code for response in responses) == [200, 409]
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT count(*) AS count FROM users WHERE role = 'admin' AND status = 'active'"
        )
        assert cursor.fetchone()["count"] == 1


def test_concurrent_self_deactivation_preserves_one_admin(auth_user):
    _, first = auth_user("first-admin@example.com", role="admin")
    _, second = auth_user("second-admin@example.com", role="admin")
    with ThreadPoolExecutor(max_workers=2) as pool:
        with get_connection() as blocker:
            with blocker.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(73241, 1)")
            futures = [
                pool.submit(request, "PATCH", "/users/me/deactivate", headers)
                for headers in (first, second)
            ]
            try:
                wait_for_two_blocked_connections(blocker.info.backend_pid)
            finally:
                blocker.rollback()
        responses = [future.result(timeout=15) for future in futures]
    assert sorted(response.status_code for response in responses) == [200, 409]
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT count(*) AS count FROM users WHERE role = 'admin' AND status = 'active'"
        )
        assert cursor.fetchone()["count"] == 1
