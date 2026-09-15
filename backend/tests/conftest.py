import os

import pytest
from fastapi.testclient import TestClient

os.environ["DB_NAME"] = "equipment_reservation_test"

from app.database import get_connection
from app.main import app

DEFAULT_PASSWORD = "testpassword"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_database():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                TRUNCATE reservations, equipment, categories, users
                RESTART IDENTITY CASCADE
                """)
    yield


@pytest.fixture
def make_user(client):
    """Create a user through the public registration endpoint."""

    def _make_user(
        email="user@example.com",
        password=DEFAULT_PASSWORD,
        role="user",
        status="active",
    ):
        response = client.post("/register", json={"email": email, "password": password})
        assert response.status_code == 201, response.text
        user = response.json()

        if role != "user" or status != "active":
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE users
                        SET role = %s, status = %s
                        WHERE id = %s
                        """,
                        (role, status, user["id"]),
                    )
            user["role"] = role
            user["status"] = status

        return user

    return _make_user


@pytest.fixture
def auth_user(client, make_user):
    """Create an active user and return (user, Authorization headers)."""

    def _auth_user(
        email="user@example.com",
        password=DEFAULT_PASSWORD,
        role="user",
    ):
        user = make_user(email=email, password=password, role=role)
        response = client.post("/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        token = response.json()["access_token"]
        return user, {"Authorization": f"Bearer {token}"}

    return _auth_user


@pytest.fixture
def make_db_user():
    """Insert a user directly when authentication behavior is not under test."""

    def _make_db_user(
        email="user@example.com",
        password_hash="fake-hash",
        role="user",
        status="active",
    ):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (email, password_hash, role, status)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, email, role, status
                    """,
                    (email, password_hash, role, status),
                )
                return cursor.fetchone()

    return _make_db_user


@pytest.fixture
def make_category():
    def _make_category(name="Sports"):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO categories (name)
                    VALUES (%s)
                    RETURNING id, name
                    """,
                    (name,),
                )
                return cursor.fetchone()

    return _make_category


@pytest.fixture
def make_equipment(make_category):
    def _make_equipment(
        name="Basketball",
        asset_tag="BB-001",
        category_id=None,
        status="active",
    ):
        if category_id is None:
            category_id = make_category()["id"]

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO equipment (name, asset_tag, category_id, status)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, name, asset_tag, category_id, status
                    """,
                    (name, asset_tag, category_id, status),
                )
                return cursor.fetchone()

    return _make_equipment


@pytest.fixture
def make_reservation():
    def _make_reservation(
        user_id,
        equipment_id,
        start_date,
        end_date,
        status="active",
    ):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO reservations (
                        user_id,
                        equipment_id,
                        start_date,
                        end_date,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, user_id, equipment_id, start_date, end_date, status
                    """,
                    (user_id, equipment_id, start_date, end_date, status),
                )
                return cursor.fetchone()

    return _make_reservation


@pytest.fixture
def get_reservation_status():
    def _get_reservation_status(reservation_id):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT status FROM reservations WHERE id = %s",
                    (reservation_id,),
                )
                return cursor.fetchone()["status"]

    return _get_reservation_status


@pytest.fixture
def get_user_status():
    def _get_user_status(user_id):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT status FROM users WHERE id = %s", (user_id,))
                return cursor.fetchone()["status"]

    return _get_user_status
