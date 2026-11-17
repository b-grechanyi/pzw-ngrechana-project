import pytest


async def admin_headers(admin_user, auth_header):
    return await auth_header(admin_user.email, "admin-pass")


@pytest.mark.asyncio
async def test_regular_user_cannot_manage_books(
    client, regular_user, auth_header, available_book
):
    headers = await auth_header(regular_user.email, "marko123")

    create_response = await client.post(
        "/books/",
        json={"title": "New", "author": "Author", "isbn": "9780000000030"},
        headers=headers,
    )
    update_response = await client.patch(
        f"/books/{available_book.id}",
        json={"title": "Changed"},
        headers=headers,
    )
    delete_response = await client.delete(
        f"/books/{available_book.id}", headers=headers
    )

    assert [
        create_response.status_code,
        update_response.status_code,
        delete_response.status_code,
    ] == [403, 403, 403]
    assert all(
        response.json()["code"] == "forbidden"
        for response in (create_response, update_response, delete_response)
    )


@pytest.mark.asyncio
async def test_admin_can_create_read_update_and_delete_book(
    client, admin_user, auth_header
):
    headers = await admin_headers(admin_user, auth_header)
    payload = {
        "title": "Test Driven APIs",
        "author": "A. Developer",
        "isbn": "9780000000031",
    }

    create_response = await client.post("/books/", json=payload, headers=headers)

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["title"] == payload["title"]
    assert created["is_available"] is True

    read_response = await client.get(f"/books/{created['id']}", headers=headers)
    assert read_response.status_code == 200
    assert read_response.json()["isbn"] == payload["isbn"]

    update_response = await client.patch(
        f"/books/{created['id']}",
        json={"title": "Updated title"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated title"
    assert update_response.json()["author"] == payload["author"]

    delete_response = await client.delete(
        f"/books/{created['id']}", headers=headers
    )
    assert delete_response.status_code == 204
    missing_response = await client.get(f"/books/{created['id']}", headers=headers)
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_book_isbn_must_be_unique(
    client, available_book, admin_user, auth_header
):
    headers = await admin_headers(admin_user, auth_header)

    response = await client.post(
        "/books/",
        json={
            "title": "Duplicate ISBN",
            "author": "Another Author",
            "isbn": available_book.isbn,
        },
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json()["code"] == "duplicate"


@pytest.mark.asyncio
async def test_book_with_rental_history_cannot_be_deleted(
    client, rental_fixture, admin_user, auth_header
):
    headers = await admin_headers(admin_user, auth_header)

    response = await client.delete(
        f"/books/{rental_fixture.book_id}", headers=headers
    )

    assert response.status_code == 409
    assert response.json()["code"] == "has_rentals"
