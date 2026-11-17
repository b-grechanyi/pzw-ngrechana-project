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
