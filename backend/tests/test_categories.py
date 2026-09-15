def test_get_categories_empty(client):
    response = client.get("/categories")
    assert response.status_code == 200
    assert response.json() == []


def test_get_categories(client, make_category):
    make_category("Sports")
    make_category("Cameras")

    response = client.get("/categories")
    assert response.status_code == 200
    assert response.json() == [
        {"id": 2, "name": "Cameras"},
        {"id": 1, "name": "Sports"},
    ]


def test_admin_can_create_category(client, auth_user):
    _, headers = auth_user("admin@example.com", role="admin")

    response = client.post("/categories", json={"name": "Sports"}, headers=headers)

    assert response.status_code == 201
    assert response.json() == {"id": 1, "name": "Sports"}


def test_normal_user_cannot_create_category(client, auth_user):
    _, headers = auth_user()

    response = client.post("/categories", json={"name": "Sports"}, headers=headers)

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_create_category_requires_authentication(client):
    response = client.post("/categories", json={"name": "Sports"})
    assert response.status_code == 401


def test_admin_cannot_create_duplicate_category(client, auth_user, make_category):
    _, headers = auth_user("admin@example.com", role="admin")
    make_category("Sports")

    response = client.post("/categories", json={"name": "Sports"}, headers=headers)

    assert response.status_code == 409
    assert response.json() == {"detail": "Category already exists"}


def test_create_category_requires_name(client, auth_user):
    _, headers = auth_user("admin@example.com", role="admin")

    response = client.post("/categories", json={}, headers=headers)

    assert response.status_code == 422


def test_admin_can_update_category(client, auth_user, make_category):
    _, headers = auth_user("admin@example.com", role="admin")
    category = make_category("Sports")

    response = client.patch(
        f"/categories/{category['id']}",
        json={"name": "Indoor Sports"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == {"id": category["id"], "name": "Indoor Sports"}


def test_normal_user_cannot_update_category(client, auth_user, make_category):
    _, headers = auth_user()
    category = make_category("Sports")

    response = client.patch(
        f"/categories/{category['id']}",
        json={"name": "Indoor Sports"},
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_update_category_requires_authentication(client):
    response = client.patch("/categories/1", json={"name": "Indoor Sports"})
    assert response.status_code == 401


def test_admin_gets_404_when_updating_missing_category(client, auth_user):
    _, headers = auth_user("admin@example.com", role="admin")

    response = client.patch(
        "/categories/999",
        json={"name": "Indoor Sports"},
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Category not found"}


def test_admin_cannot_rename_category_to_existing_name(
    client, auth_user, make_category
):
    _, headers = auth_user("admin@example.com", role="admin")
    sports = make_category("Sports")
    make_category("Training")

    response = client.patch(
        f"/categories/{sports['id']}",
        json={"name": "Training"},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Category already exists"}


def test_update_category_requires_name(client, auth_user, make_category):
    _, headers = auth_user("admin@example.com", role="admin")
    category = make_category("Sports")

    response = client.patch(
        f"/categories/{category['id']}",
        json={},
        headers=headers,
    )

    assert response.status_code == 422


def test_admin_can_delete_unused_category(client, auth_user, make_category):
    _, headers = auth_user("admin@example.com", role="admin")
    category = make_category("Sports")

    response = client.delete(f"/categories/{category['id']}", headers=headers)

    assert response.status_code == 204


def test_normal_user_cannot_delete_category(client, auth_user, make_category):
    _, headers = auth_user()
    category = make_category("Sports")

    response = client.delete(f"/categories/{category['id']}", headers=headers)

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_delete_category_requires_authentication(client):
    response = client.delete("/categories/1")
    assert response.status_code == 401


def test_admin_gets_404_when_deleting_missing_category(client, auth_user):
    _, headers = auth_user("admin@example.com", role="admin")

    response = client.delete("/categories/999", headers=headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Category not found"}


def test_admin_cannot_delete_category_in_use(
    client, auth_user, make_category, make_equipment
):
    _, headers = auth_user("admin@example.com", role="admin")
    category = make_category("Sports")
    make_equipment(category_id=category["id"])

    response = client.delete(f"/categories/{category['id']}", headers=headers)

    assert response.status_code == 409
    assert response.json() == {"detail": "Category is still in use"}
