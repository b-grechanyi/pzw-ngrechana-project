import pytest


@pytest.mark.asyncio
async def test_login_returns_tokens_and_user(client, regular_user):
    response = await client.post(
        "/auth/login",
        json={"email": regular_user.email, "password": "marko123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == regular_user.email
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert "password_hash" not in body["user"]


@pytest.mark.asyncio
async def test_unknown_email_and_wrong_password_have_same_401(client, regular_user):
    unknown_email = await client.post(
        "/auth/login",
        json={"email": "missing@example.com", "password": "marko123"},
    )
    wrong_password = await client.post(
        "/auth/login",
        json={"email": regular_user.email, "password": "wrong-password"},
    )

    assert unknown_email.status_code == wrong_password.status_code == 401
    assert unknown_email.json() == wrong_password.json()
    assert unknown_email.json()["code"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_refresh_token_issues_new_token_pair(client, regular_user):
    login_response = await client.post(
        "/auth/login",
        json={"email": regular_user.email, "password": "marko123"},
    )

    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": login_response.json()["refresh_token"]},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]


@pytest.mark.asyncio
async def test_me_requires_valid_access_token(client, regular_user, auth_header):
    headers = await auth_header(regular_user.email, "marko123")

    response = await client.get("/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == regular_user.email
    assert "password_hash" not in response.json()


@pytest.mark.asyncio
async def test_protected_endpoint_rejects_missing_token(client):
    response = await client.get("/books/")

    assert response.status_code == 401
