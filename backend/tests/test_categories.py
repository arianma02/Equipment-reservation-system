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


def test_admin_can_create_category(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/categories",
        json={"name": "Sports"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "Sports",
    }


def test_normal_user_cannot_create_category(client):
    client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    )

    login_response = client.post(
        "/login",
        json={"email": "user@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/categories",
        json={"name": "Sports"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_create_category_requires_authentication(client):
    response = client.post(
        "/categories",
        json={"name": "Sports"},
    )

    assert response.status_code == 401


def test_admin_cannot_create_duplicate_category(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s)",
                ("Sports",),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/categories",
        json={"name": "Sports"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Category already exists"}


def test_create_category_requires_name(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/categories",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_admin_can_update_category(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
                ("Sports",),
            )
            category = cursor.fetchone()

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/categories/{category['id']}",
        json={"name": "Indoor Sports"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": category["id"],
        "name": "Indoor Sports",
    }


def test_normal_user_cannot_update_category(client):
    user = client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
                ("Sports",),
            )
            category = cursor.fetchone()

    login_response = client.post(
        "/login",
        json={"email": "user@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/categories/{category['id']}",
        json={"name": "Indoor Sports"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_update_category_requires_authentication(client):
    response = client.patch(
        "/categories/1",
        json={"name": "Indoor Sports"},
    )

    assert response.status_code == 401


def test_admin_gets_404_when_updating_missing_category(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        "/categories/999",
        json={"name": "Indoor Sports"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Category not found"}


def test_admin_cannot_rename_category_to_existing_name(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
                ("Sports",),
            )
            sports = cursor.fetchone()

            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s)",
                ("Training",),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/categories/{sports['id']}",
        json={"name": "Training"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Category already exists"}


def test_update_category_requires_name(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
                ("Sports",),
            )
            category = cursor.fetchone()

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/categories/{category['id']}",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_admin_can_delete_unused_category(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
                ("Sports",),
            )
            category = cursor.fetchone()

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.delete(
        f"/categories/{category['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204


def test_normal_user_cannot_delete_category(client):
    user = client.post(
        "/register",
        json={"email": "user@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
                ("Sports",),
            )
            category = cursor.fetchone()

    login_response = client.post(
        "/login",
        json={"email": "user@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.delete(
        f"/categories/{category['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_delete_category_requires_authentication(client):
    response = client.delete("/categories/1")

    assert response.status_code == 401


def test_admin_gets_404_when_deleting_missing_category(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.delete(
        "/categories/999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Category not found"}


def test_admin_cannot_delete_category_in_use(client):
    admin = client.post(
        "/register",
        json={"email": "admin@example.com", "password": "testpassword"},
    ).json()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role = 'admin' WHERE id = %s",
                (admin["id"],),
            )

            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) RETURNING id",
                ("Sports",),
            )
            category = cursor.fetchone()

            cursor.execute(
                """
                INSERT INTO equipment (name, asset_tag, category_id)
                VALUES (%s, %s, %s)
                """,
                ("Basketball", "BB-001", category["id"]),
            )

    login_response = client.post(
        "/login",
        json={"email": "admin@example.com", "password": "testpassword"},
    )
    token = login_response.json()["access_token"]

    response = client.delete(
        f"/categories/{category['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Category is still in use"}
