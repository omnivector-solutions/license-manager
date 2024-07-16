import pytest
from fastapi import status

from lm_simulator.models import License, LicenseInUse


def test_health_check(client):
    """Test the health check route."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_create_license(client):
    """Test that the correct status code and response are returned on in use license creation."""
    response = client.post(
        "/licenses/",
        json={"name": "test_name", "total": 100},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        "id": 1,
        "name": "test_name",
        "total": 100,
        "in_use": 0,
        "licenses_in_use": [],
    }


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_create_license_duplicate(client, session, one_license):
    """Test that the correct response is returned when a duplicate license creation is attempted."""
    session.add(License(**one_license.dict()))
    session.commit()
    response = client.post(
        "/licenses/",
        json={"name": "test_name", "total": 100},
    )
    assert response.status_code == status.HTTP_409_CONFLICT


def test_list_licenses(client, session):
    session.add(License(name="l1", total=100, id=1))
    session.add(License(name="l2", total=200, id=2))
    session.add(License(name="l3", total=300, id=3))
    session.commit()
    response = client.get("/licenses/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "id": 1,
            "name": "l1",
            "total": 100,
            "in_use": 0,
            "licenses_in_use": [],
        },
        {
            "id": 2,
            "name": "l2",
            "total": 200,
            "in_use": 0,
            "licenses_in_use": [],
        },
        {
            "id": 3,
            "name": "l3",
            "total": 300,
            "in_use": 0,
            "licenses_in_use": [],
        },
    ]


def test_list_licenses_empty(client):
    response = client.get("/licenses/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_list_licenses_in_use(client, session, one_license):
    session.add(License(**one_license.dict()))
    session.add(
        LicenseInUse(quantity=10, user_name="user1", lead_host="host1", license_name="test_name", id=1)
    )
    session.add(
        LicenseInUse(quantity=20, user_name="user1", lead_host="host1", license_name="test_name", id=2)
    )
    session.commit()
    response = client.get("/licenses-in-use/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "id": 1,
            "quantity": 10,
            "user_name": "user1",
            "lead_host": "host1",
            "license_name": "test_name",
        },
        {
            "id": 2,
            "quantity": 20,
            "user_name": "user1",
            "lead_host": "host1",
            "license_name": "test_name",
        },
    ]


def test_list_licenses_in_use_from_name(client, session, one_license):
    session.add(License(**one_license.dict()))
    session.add(
        LicenseInUse(quantity=10, user_name="user1", lead_host="host1", license_name="test_name", id=1)
    )
    session.add(
        LicenseInUse(quantity=20, user_name="user1", lead_host="host1", license_name="test_name", id=2)
    )
    session.commit()
    response = client.get("/licenses-in-use/test_name")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "id": 1,
            "quantity": 10,
            "user_name": "user1",
            "lead_host": "host1",
            "license_name": "test_name",
        },
        {
            "id": 2,
            "quantity": 20,
            "user_name": "user1",
            "lead_host": "host1",
            "license_name": "test_name",
        },
    ]


def test_list_licenses_in_use_from_name_no_match(client, session, one_license):
    session.add(License(**one_license.dict()))
    session.add(
        LicenseInUse(quantity=10, user_name="user1", lead_host="host1", license_name="test_name", id=1)
    )
    session.add(
        LicenseInUse(quantity=20, user_name="user1", lead_host="host1", license_name="test_name", id=2)
    )
    session.commit()
    response = client.get("/licenses-in-use/name_not_in_database")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_list_licenses_in_use_from_name_empty(client):
    response = client.get("/licenses-in-use/test")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_list_licenses_in_use_empty(client):
    response = client.get("/licenses-in-use/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_create_license_in_use(client, session, one_license):
    session.add(License(**one_license.dict()))
    response = client.post(
        "/licenses-in-use/",
        json={"license_name": "test_name", "quantity": 10, "user_name": "user1", "lead_host": "host1"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        "id": 1,
        "quantity": 10,
        "user_name": "user1",
        "lead_host": "host1",
        "license_name": "test_name",
    }


def test_create_license_in_use_not_enough(client, session, one_license):
    session.add(License(**one_license.dict()))
    response = client.post(
        "/licenses-in-use/",
        json={"license_name": "test_name", "quantity": 9999, "user_name": "user1", "lead_host": "host1"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Not enough licenses available" in response.text


def test_create_license_in_use_dont_exists(client):
    response = client.post(
        "/licenses-in-use/",
        json={"license_name": "test_name", "quantity": 1, "user_name": "user1", "lead_host": "host1"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "doesn't exist" in response.text


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_create_license_in_use_duplicate(client, session, one_license):
    session.add(License(**one_license.dict()))
    session.add(
        LicenseInUse(quantity=10, user_name="user1", lead_host="host1", license_name="test_name", id=1)
    )
    session.commit()
    response = client.post(
        "/licenses-in-use/",
        json={"license_name": "test_name", "quantity": 10, "user_name": "user1", "lead_host": "host1"},
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "LicenseInUse already exists" in response.text


def test_delete_license_in_use(client, session, one_license):
    session.add(License(**one_license.dict()))
    session.add(
        LicenseInUse(quantity=10, user_name="user1", lead_host="host1", license_name="test_name", id=1)
    )
    session.add(
        LicenseInUse(quantity=20, user_name="user1", lead_host="host1", license_name="test_name", id=2)
    )
    session.commit()

    response = client.request(
        "DELETE",
        "/licenses-in-use/",
        json={"license_name": "test_name", "quantity": 10, "user_name": "user1", "lead_host": "host1"},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_license_in_use_not_found(client):
    response = client.request(
        "DELETE",
        "/licenses-in-use/",
        json={"license_name": "test_name", "quantity": 10, "user_name": "user1", "lead_host": "host1"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "License not found" in response.text


def test_delete_license(client, session, one_license):
    session.add(License(**one_license.dict()))
    session.commit()

    response = client.delete("/licenses/test_name")
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_license_not_found(client):
    response = client.delete("/licenses/not-a-license")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "License not found" in response.text
