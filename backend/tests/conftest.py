import os

import pytest
from fastapi.testclient import TestClient

os.environ["DB_NAME"] = "equipment_reservation_test"

from app.database import get_connection
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_database():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "TRUNCATE reservations, equipment, categories, users RESTART IDENTITY CASCADE;"
            )

    yield
