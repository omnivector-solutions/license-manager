from fastapi import status
from pytest import mark

from lm_simulator.models import License, LicenseInUse


@mark.asyncio
async def test__health_check(backend_client):
    """
    Test the health check route.
    """
    response = await backend_client.get("/health")
    assert response.status_code == status.HTTP_204_NO_CONTENT


@mark.asyncio
async def test__create_license__success(backend_client, one_license):
    """
    Test that the correct status code and response are returned on in use license creation.
    """
    response = await backend_client.post(
        "/licenses",
        json=one_license.model_dump(),
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        "name": one_license.name,
        "total": one_license.total,
        "in_use": 0,
        "licenses_in_use": [],
    }


@mark.asyncio
async def test__create_license__fail_with_duplicate(backend_client, one_license, insert_objects):
    """
    Test that the correct response is returned when a duplicate license creation is attempted.
    """
    await insert_objects([one_license], License)

    response = backend_client.post(
        "/licenses",
        json=one_license.model_dump(),
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@mark.asyncio
async def test__list_licenses__empty(backend_client):
    response = await backend_client.get("/licenses")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@mark.asyncio
async def test__list_licenses__success(backend_client, licenses, insert_objects):
    """
    Test that the correct response is returned when listing licenses.
    """
    await insert_objects(licenses, License)

    response = await backend_client.get("/licenses")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "name": licenses[0].name,
            "total": licenses[0].total,
            "in_use": 0,
            "licenses_in_use": [],
        },
        {
            "name": licenses[1].name,
            "total": licenses[1].total,
            "in_use": 0,
            "licenses_in_use": [],
        },
    ]


@mark.asyncio
async def test__delete_license__success(backend_client, one_license, insert_objects):
    """
    Test that the correct response is returned when deleting a license.
    """
    await insert_objects([one_license], License)

    response = await backend_client.delete(f"/licenses/{one_license.name}")

    assert response.status_code == status.HTTP_204_NO_CONTENT


@mark.asyncio
async def test__delete_license__fail_with_not_found(backend_client):
    """
    Test that the correct response is returned when attempting to delete a non-existent license.
    """
    response = await backend_client.delete("/licenses/not-a-license")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@mark.asyncio
async def test__create_license_in_use__success(
    backend_client, one_license, one_license_in_use, insert_objects
):
    """
    Test that the correct response is returned when creating a license in use.
    """
    await insert_objects([one_license], License)

    response = await backend_client.post(
        "/licenses-in-use",
        json=one_license_in_use.model_dump(),
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == one_license_in_use.model_dump()


@mark.asyncio
async def test__create_license_in_use__fail_with_not_enough(backend_client, one_license, insert_objects):
    """
    Test that the correct response is returned when creating a license in use with not enough licenses.
    """
    await insert_objects([one_license], License)

    response = await backend_client.post(
        "/licenses-in-use",
        json={
            "license_name": one_license.name,
            "quantity": 9999,
            "user_name": "user1",
            "lead_host": "host1",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Not enough licenses" in response.text


@mark.asyncio
async def test__create_license_in_use__fail_with_license_not_found(
    backend_client, one_license, insert_objects
):
    """
    Test that the correct response is returned when creating a license in use with a non-existent license.
    """
    await insert_objects([one_license], License)

    response = await backend_client.post(
        "/licenses-in-use",
        json={
            "license_name": "not-a-license",
            "quantity": 1,
            "user_name": "user1",
            "lead_host": "host1",
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "doesn't exist" in response.text


@mark.asyncio
async def test__list_licenses_in_use__empty(backend_client):
    """
    Test that the correct response is returned when listing licenses in use with no licenses in use.
    """
    response = await backend_client.get("/licenses-in-use")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@mark.asyncio
async def test__list_licenses_in_use__success(backend_client, licenses, licenses_in_use, insert_objects):
    """
    Test that the correct response is returned when listing licenses in use.
    """
    await insert_objects(licenses, License)
    await insert_objects(licenses_in_use, LicenseInUse)

    response = await backend_client.get("/licenses-in-use")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "id": 1,
            "quantity": licenses_in_use[0].quantity,
            "user_name": licenses_in_use[0].user_name,
            "lead_host": licenses_in_use[0].lead_host,
            "license_name": licenses_in_use[0].license_name,
        },
        {
            "id": 2,
            "quantity": licenses_in_use[1].quantity,
            "user_name": licenses_in_use[1].user_name,
            "lead_host": licenses_in_use[1].lead_host,
            "license_name": licenses_in_use[1].license_name,
        },
    ]


@mark.asyncio
async def test__delete_license_in_use__success(
    backend_client, one_license, one_license_in_use, insert_objects
):
    """
    Test that the correct response is returned when deleting a license in use.
    """
    await insert_objects([one_license], License)
    inserted = await insert_objects([one_license_in_use], LicenseInUse)

    response = await backend_client.delete(f"/licenses-in-use/{inserted.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT


@mark.asyncio
async def test__delete_license_in_use__fail_with_not_found(backend_client):
    """
    Test that the correct response is returned when attempting to delete a non-existent license in use.
    """
    response = await backend_client.delete("/licenses-in-use/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "License In Use not found" in response.text
