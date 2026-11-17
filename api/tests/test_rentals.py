import pytest
from freezegun import freeze_time


@pytest.fixture(autouse=True)
def default_time():
    with freeze_time("2026-11-01 10:00:00"):
        yield


@pytest.mark.asyncio
async def test_cannot_rent_unavailable_book(
    client, available_book, regular_user, auth_header
):
    headers = await auth_header(regular_user.email, "marko123")

    first = await client.post(
        "/rentals/", json={"book_id": available_book.id}, headers=headers
    )
    assert first.status_code == 201

    second = await client.post(
        "/rentals/", json={"book_id": available_book.id}, headers=headers
    )
    assert second.status_code == 409
    assert second.json()["code"] == "book_unavailable"


@pytest.mark.asyncio
async def test_user_cannot_return_another_users_rental(
    client, rental_fixture, other_user, auth_header
):
    headers = await auth_header(other_user.email, "pass")

    response = await client.post(
        f"/rentals/{rental_fixture.id}/return", headers=headers
    )

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


@pytest.mark.asyncio
async def test_returning_rental_makes_book_available(
    client, rental_fixture, auth_header
):
    headers = await auth_header("owner@example.com", "owner-pass")

    response = await client.post(
        f"/rentals/{rental_fixture.id}/return", headers=headers
    )

    assert response.status_code == 200
    assert response.json()["status"] == "returned"

    book_response = await client.get(
        f"/books/{rental_fixture.book_id}", headers=headers
    )
    assert book_response.status_code == 200
    assert book_response.json()["is_available"] is True


@pytest.mark.asyncio
async def test_user_cannot_view_another_users_rental(
    client, rental_fixture, other_user, auth_header
):
    headers = await auth_header(other_user.email, "pass")

    response = await client.get(f"/rentals/{rental_fixture.id}", headers=headers)

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


@pytest.mark.asyncio
async def test_user_rental_list_only_contains_their_rentals(
    client, rental_fixture, other_user, auth_header, available_book
):
    owner_headers = await auth_header("owner@example.com", "owner-pass")
    other_headers = await auth_header(other_user.email, "pass")
    await client.post(
        "/rentals/", json={"book_id": available_book.id}, headers=other_headers
    )

    owner_response = await client.get("/rentals/", headers=owner_headers)
    other_response = await client.get("/rentals/", headers=other_headers)

    assert [item["id"] for item in owner_response.json()] == [rental_fixture.id]
    assert len(other_response.json()) == 1
    assert other_response.json()[0]["user_id"] != rental_fixture.user_id


@pytest.mark.asyncio
async def test_rental_limit_is_five_active_rentals(
    client, regular_user, admin_user, auth_header
):
    headers = await auth_header(regular_user.email, "marko123")
    admin_headers = await auth_header(admin_user.email, "admin-pass")
    for index in range(6):
        book_response = await client.post(
            "/books/",
            json={
                "title": f"Book {index}",
                "author": "Rental Limit Test",
                "isbn": f"97800000001{index:02d}",
            },
            headers=admin_headers,
        )
        assert book_response.status_code == 201
        response = await client.post(
            "/rentals/", json={"book_id": book_response.json()["id"]}, headers=headers
        )
        if index < 5:
            assert response.status_code == 201
        else:
            assert response.status_code == 409
            assert response.json()["code"] == "rental_limit_reached"


@pytest.mark.asyncio
async def test_rental_due_date_is_21_days_after_renting(
    client, available_book, regular_user, auth_header
):
    headers = await auth_header(regular_user.email, "marko123")

    response = await client.post(
        "/rentals/", json={"book_id": available_book.id}, headers=headers
    )

    assert response.status_code == 201
    assert response.json()["rented_at"].startswith("2026-11-01T10:00:00")
    assert response.json()["due_date"].startswith("2026-11-22T10:00:00")


@pytest.mark.asyncio
async def test_returning_already_returned_rental_conflicts(
    client, rental_fixture, auth_header
):
    headers = await auth_header("owner@example.com", "owner-pass")
    first_response = await client.post(
        f"/rentals/{rental_fixture.id}/return", headers=headers
    )
    second_response = await client.post(
        f"/rentals/{rental_fixture.id}/return", headers=headers
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert second_response.json()["code"] == "already_returned"
