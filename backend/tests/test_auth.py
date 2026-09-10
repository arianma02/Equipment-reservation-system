from app.database import get_connection


def test_register_user(client):
    new_user = client.post(
        "/register", json={"email": "test@example.com", "password": "testpassword"}
    )
    assert new_user.status_code == 201
    assert new_user.json() == {
        "id": 1,
        "email": "test@example.com",
        "role": "user",
        "status": "active",
    }


def test_register_user_duplicate_email(client):
    first_user = client.post(
        "/register", json={"email": "test@example.com", "password": "testpassword"}
    )
    duplicate_user = client.post(
        "/register", json={"email": "test@example.com", "password": "examplepassword"}
    )
    assert first_user.status_code == 201
    assert duplicate_user.status_code == 409
    assert duplicate_user.json() == {"detail": "Email already registered"}


def test_register_invalid_email(client):
    response = client.post(
        "/register", json={"email": "invalid-email", "password": "testpassword"}
    )
    assert response.status_code == 422


def test_register_short_password(client):
    response = client.post(
        "/register", json={"email": "test@example.com", "password": "short"}
    )
    assert response.status_code == 422


def test_successful_login(client):
    client.post(
        "/register", json={"email": "test@example.com", "password": "testpassword"}
    )
    user_login = client.post(
        "/login", json={"email": "test@example.com", "password": "testpassword"}
    )
    assert user_login.status_code == 200
    assert "access_token" in user_login.json()
    assert user_login.json()["token_type"] == "bearer"


def test_wrong_password_login(client):
    client.post(
        "/register", json={"email": "test@example.com", "password": "testpassword"}
    )
    user_login_wrong_password = client.post(
        "/login", json={"email": "test@example.com", "password": "wrongpassword"}
    )
    assert user_login_wrong_password.status_code == 401
    assert user_login_wrong_password.json() == {"detail": "Invalid email or password"}


def test_wrong_email_login(client):
    user_login_wrong_email = client.post(
        "/login", json={"email": "wrong@example.com", "password": "testpassword"}
    )
    assert user_login_wrong_email.status_code == 401
    assert user_login_wrong_email.json() == {"detail": "Invalid email or password"}


def test_disabled_user_login(client):
    client.post(
        "/register", json={"email": "test@example.com", "password": "testpassword"}
    )
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET status = 'disabled' WHERE email = %s",
                ("test@example.com",),
            )

    user_login_disabled = client.post(
        "/login", json={"email": "test@example.com", "password": "testpassword"}
    )
    assert user_login_disabled.status_code == 403
    assert user_login_disabled.json() == {"detail": "Account is disabled"}


def test_get_me_with_valid_token(client):
    client.post(
        "/register", json={"email": "test@example.com", "password": "testpassword"}
    )
    user_login = client.post(
        "/login", json={"email": "test@example.com", "password": "testpassword"}
    )
    assert user_login.status_code == 200
    access_token = user_login.json()["access_token"]
    response = client.get("/me", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "email": "test@example.com",
        "role": "user",
        "status": "active",
    }


def test_get_me_without_token(client):
    response = client.get("/me")
    assert response.status_code == 401


def test_get_me_with_invalid_token(client):
    response = client.get("/me", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


def test_get_me_with_disabled_user(client):
    client.post(
        "/register", json={"email": "test@example.com", "password": "testpassword"}
    )
    user_login = client.post(
        "/login", json={"email": "test@example.com", "password": "testpassword"}
    )
    assert user_login.status_code == 200
    access_token = user_login.json()["access_token"]
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET status = 'disabled' WHERE email = %s",
                ("test@example.com",),
            )
    response = client.get("/me", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Account is disabled"}
