import pytest


@pytest.mark.asyncio
async def test_admin_can_create_update_and_delete_user(
    client, admin_user, auth_header
):
    headers = await auth_header(admin_user.email, "admin-pass")
    payload = {
        "first_name": "New",
        "last_name": "Reader",
        "email": "new-reader@example.com",
        "password": "new-reader-pass",
        "role": "user",
    }

    create_response = await client.post("/users/", json=payload, headers=headers)

    assert create_response.status_code == 201
    created = create_response.json()
    user_id = created["id"]
    assert created["email"] == payload["email"]
    assert "password_hash" not in created

    login_response = await client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login_response.status_code == 200

    update_response = await client.patch(
        f"/users/{user_id}",
        json={"first_name": "Updated", "password": "updated-reader-pass"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["first_name"] == "Updated"
    assert "password_hash" not in update_response.json()

    old_password_response = await client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    new_password_response = await client.post(
        "/auth/login",
        json={"email": payload["email"], "password": "updated-reader-pass"},
    )
    assert old_password_response.status_code == 401
    assert new_password_response.status_code == 200

    delete_response = await client.delete(f"/users/{user_id}", headers=headers)
    assert delete_response.status_code == 204

    list_response = await client.get("/users/", headers=headers)
    assert all(user["id"] != user_id for user in list_response.json())


@pytest.mark.asyncio
async def test_regular_user_cannot_create_edit_or_delete_users(
    client, regular_user, other_user, auth_header
):
    headers = await auth_header(regular_user.email, "marko123")
    payload = {
        "first_name": "New",
        "last_name": "Reader",
        "email": "new-reader@example.com",
        "password": "new-reader-pass",
    }

    responses = [
        await client.post("/users/", json=payload, headers=headers),
        await client.patch(
            f"/users/{other_user.id}",
            json={"first_name": "Changed"},
            headers=headers,
        ),
        await client.delete(f"/users/{other_user.id}", headers=headers),
    ]

    assert [response.status_code for response in responses] == [403, 403, 403]
    assert all(response.json()["code"] == "forbidden" for response in responses)


@pytest.mark.asyncio
async def test_admin_user_management_handles_duplicate_and_missing_user(
    client, admin_user, regular_user, auth_header
):
    headers = await auth_header(admin_user.email, "admin-pass")
    payload = {
        "first_name": "Duplicate",
        "last_name": "Email",
        "email": regular_user.email,
        "password": "valid-password",
    }

    duplicate_response = await client.post("/users/", json=payload, headers=headers)
    missing_response = await client.patch(
        "/users/999999", json={"first_name": "Missing"}, headers=headers
    )

    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["code"] == "duplicate"
    assert missing_response.status_code == 404
    assert missing_response.json()["code"] == "not_found"


@pytest.mark.asyncio
async def test_user_with_rental_history_cannot_be_deleted(
    client, rental_fixture, admin_user, auth_header
):
    headers = await auth_header(admin_user.email, "admin-pass")

    response = await client.delete(
        f"/users/{rental_fixture.user_id}", headers=headers
    )

    assert response.status_code == 409
    assert response.json()["code"] == "has_rentals"
