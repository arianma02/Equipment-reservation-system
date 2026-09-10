from app.database import get_connection


def test_get_categories_empty(client):
    response = client.get("/categories")
    assert response.status_code == 200
    assert response.json() == []


def test_get_categories(client):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s), (%s);",
                ("Sports", "Cameras"),
            )

    response = client.get("/categories")
    assert response.status_code == 200
    assert response.json() == [
        {"id": 2, "name": "Cameras"},
        {"id": 1, "name": "Sports"},
    ]
