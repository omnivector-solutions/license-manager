from httpx import AsyncClient
from pytest import mark
from sqlalchemy import select

from lm_api.api.models.license_server import LicenseServer
from lm_api.permissions import Permissions


@mark.parametrize(
    "permission",
    [
        Permissions.LICENSE_SERVER_CREATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_add_license_server__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    read_object,
    create_one_configuration,
):
    configuration_id = create_one_configuration[0].id

    data = {
        "config_id": configuration_id,
        "host": "licserv0001.com",
        "port": 1234,
    }

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.post("/lm/license_servers", json=data)
    assert response.status_code == 201

    stmt = select(LicenseServer).where(LicenseServer.host == data["host"])
    fetched = await read_object(stmt)

    assert fetched.config_id == configuration_id
    assert fetched.host == data["host"]
    assert fetched.port == data["port"]


@mark.parametrize(
    "permission",
    [
        Permissions.LICENSE_SERVER_READ,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_get_all_license_servers__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_license_servers,
):
    inject_security_header("owner1@test.com", permission)
    response = await backend_client.get("/lm/license_servers")

    assert response.status_code == 200

    response_license_servers = response.json()
    assert response_license_servers[0]["host"] == create_license_servers[0].host
    assert response_license_servers[0]["port"] == create_license_servers[0].port

    assert response_license_servers[1]["host"] == create_license_servers[1].host
    assert response_license_servers[1]["port"] == create_license_servers[1].port


@mark.parametrize(
    "permission",
    [
        Permissions.LICENSE_SERVER_READ,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_get_all_license_servers__with_search(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_license_servers,
):
    inject_security_header("owner1@test.com", permission)
    response = await backend_client.get(f"/lm/license_servers?search={create_license_servers[0].host}")

    assert response.status_code == 200

    response_license_servers = response.json()
    assert response_license_servers[0]["host"] == create_license_servers[0].host
    assert response_license_servers[0]["port"] == create_license_servers[0].port


@mark.parametrize(
    "permission",
    [
        Permissions.LICENSE_SERVER_READ,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_get_all_license_servers__with_sort(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_license_servers,
):
    inject_security_header("owner1@test.com", permission)
    response = await backend_client.get("/lm/license_servers?sort_field=host&sort_ascending=false")

    assert response.status_code == 200

    response_license_servers = response.json()
    assert response_license_servers[0]["host"] == create_license_servers[1].host
    assert response_license_servers[0]["port"] == create_license_servers[1].port

    assert response_license_servers[1]["host"] == create_license_servers[0].host
    assert response_license_servers[1]["port"] == create_license_servers[0].port


@mark.parametrize(
    "permission",
    [
        Permissions.LICENSE_SERVER_READ,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_get_license_server__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_license_server,
):
    id = create_one_license_server[0].id

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.get(f"/lm/license_servers/{id}")

    assert response.status_code == 200

    response_license_server = response.json()
    assert response_license_server["host"] == create_one_license_server[0].host
    assert response_license_server["port"] == create_one_license_server[0].port


@mark.parametrize(
    "id,permission",
    [
        (0, Permissions.LICENSE_SERVER_READ),
        (-1, Permissions.LICENSE_SERVER_READ),
        (999999999, Permissions.LICENSE_SERVER_READ),
        (0, Permissions.ADMIN),
        (-1, Permissions.ADMIN),
        (999999999, Permissions.ADMIN),
    ],
)
@mark.asyncio
async def test_get_license_server__fail_with_bad_parameter(
    id,
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_license_server,
):
    inject_security_header("owner1@test.com", permission)
    response = await backend_client.get(f"/lm/license_servers/{id}")

    assert response.status_code == 404


@mark.parametrize(
    "permission",
    [
        Permissions.LICENSE_SERVER_UPDATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_update_license_server__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_license_server,
    read_object,
):
    new_license_server = {"host": "licserv9999.com"}

    id = create_one_license_server[0].id

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.put(f"/lm/license_servers/{id}", json=new_license_server)

    assert response.status_code == 200

    stmt = select(LicenseServer).where(LicenseServer.id == id)
    fetch_license_server = await read_object(stmt)

    assert fetch_license_server.host == new_license_server["host"]


@mark.parametrize(
    "id,permission",
    [
        (0, Permissions.LICENSE_SERVER_UPDATE),
        (-1, Permissions.LICENSE_SERVER_UPDATE),
        (999999999, Permissions.LICENSE_SERVER_UPDATE),
        (0, Permissions.ADMIN),
        (-1, Permissions.ADMIN),
        (999999999, Permissions.ADMIN),
    ],
)
@mark.asyncio
async def test_update_license_server__fail_with_bad_parameter(
    id,
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_license_server,
    read_object,
):
    new_license_server = {"host": "licserv9999.com"}

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.put(f"/lm/license_servers/{id}", json=new_license_server)

    assert response.status_code == 404


@mark.parametrize(
    "permission",
    [
        Permissions.LICENSE_SERVER_UPDATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_update_license_server__fail_with_bad_data(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_license_server,
    read_object,
):
    new_license_server = {"bla": "bla"}

    id = create_one_license_server[0].id

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.put(f"/lm/license_servers/{id}", json=new_license_server)

    assert response.status_code == 400


@mark.parametrize(
    "permission",
    [
        Permissions.LICENSE_SERVER_DELETE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_delete_license_server__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_license_server,
    read_object,
):
    id = create_one_license_server[0].id

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.delete(f"/lm/license_servers/{id}")

    assert response.status_code == 200
    stmt = select(LicenseServer).where(LicenseServer.id == id)
    fetch_license_server = await read_object(stmt)

    assert fetch_license_server is None


@mark.parametrize(
    "id,permission",
    [
        (0, Permissions.LICENSE_SERVER_DELETE),
        (-1, Permissions.LICENSE_SERVER_DELETE),
        (999999999, Permissions.LICENSE_SERVER_DELETE),
        (0, Permissions.ADMIN),
        (-1, Permissions.ADMIN),
        (999999999, Permissions.ADMIN),
    ],
)
@mark.asyncio
async def test_delete_license_server__fail_with_bad_parameter(
    id,
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_license_server,
):
    inject_security_header("owner1@test.com", permission)
    response = await backend_client.delete(f"/lm/license_servers/{id}")

    assert response.status_code == 404
