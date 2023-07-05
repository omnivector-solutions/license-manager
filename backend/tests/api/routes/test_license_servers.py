from httpx import AsyncClient
from pytest import mark
from sqlalchemy import select

from lm_backend.api.models.license_server import LicenseServer
from lm_backend.permissions import Permissions


@mark.asyncio
async def test_add_license_server__success(
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

    inject_security_header("owner1", Permissions.LICENSE_SERVER_EDIT)
    response = await backend_client.post("/lm/license_servers", json=data)
    assert response.status_code == 201

    stmt = select(LicenseServer).where(LicenseServer.host == data["host"])
    fetched = await read_object(stmt)

    assert fetched.config_id == configuration_id
    assert fetched.host == data["host"]
    assert fetched.port == data["port"]


@mark.asyncio
async def test_get_all_license_servers__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_license_servers,
):
    inject_security_header("owner1", Permissions.LICENSE_SERVER_VIEW)
    response = await backend_client.get("/lm/license_servers")

    assert response.status_code == 200

    response_license_servers = response.json()
    assert response_license_servers[0]["host"] == create_license_servers[0].host
    assert response_license_servers[0]["port"] == create_license_servers[0].port

    assert response_license_servers[1]["host"] == create_license_servers[1].host
    assert response_license_servers[1]["port"] == create_license_servers[1].port


@mark.asyncio
async def test_get_all_license_servers__with_search(
    backend_client: AsyncClient,
    inject_security_header,
    create_license_servers,
):
    inject_security_header("owner1", Permissions.LICENSE_SERVER_VIEW)
    response = await backend_client.get(f"/lm/license_servers/?search={create_license_servers[0].host}")

    assert response.status_code == 200

    response_license_servers = response.json()
    assert response_license_servers[0]["host"] == create_license_servers[0].host
    assert response_license_servers[0]["port"] == create_license_servers[0].port


@mark.asyncio
async def test_get_all_license_servers__with_sort(
    backend_client: AsyncClient,
    inject_security_header,
    create_license_servers,
):

    inject_security_header("owner1", Permissions.LICENSE_SERVER_VIEW)
    response = await backend_client.get("/lm/license_servers/?sort_field=host&sort_ascending=false")

    assert response.status_code == 200

    response_license_servers = response.json()
    assert response_license_servers[0]["host"] == create_license_servers[1].host
    assert response_license_servers[0]["port"] == create_license_servers[1].port

    assert response_license_servers[1]["host"] == create_license_servers[0].host
    assert response_license_servers[1]["port"] == create_license_servers[0].port


@mark.asyncio
async def test_get_license_server__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_license_server,
):
    id = create_one_license_server[0].id

    inject_security_header("owner1", Permissions.LICENSE_SERVER_VIEW)
    response = await backend_client.get(f"/lm/license_servers/{id}")

    assert response.status_code == 200

    response_license_server = response.json()
    assert response_license_server["host"] == create_one_license_server[0].host
    assert response_license_server["port"] == create_one_license_server[0].port


@mark.parametrize(
    "id",
    [
        0,
        -1,
        999999999,
    ],
)
@mark.asyncio
async def test_get_license_server__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_license_server,
    id,
):
    inject_security_header("owner1", Permissions.LICENSE_SERVER_VIEW)
    response = await backend_client.get(f"/lm/license_servers/{id}")

    assert response.status_code == 404


@mark.asyncio
async def test_update_license_server__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_license_server,
    read_object,
):
    new_license_server = {"host": "licserv9999.com"}

    id = create_one_license_server[0].id

    inject_security_header("owner1", Permissions.LICENSE_SERVER_EDIT)
    response = await backend_client.put(f"/lm/license_servers/{id}", json=new_license_server)

    assert response.status_code == 200

    stmt = select(LicenseServer).where(LicenseServer.id == id)
    fetch_license_server = await read_object(stmt)

    assert fetch_license_server.host == new_license_server["host"]


@mark.parametrize(
    "id",
    [
        0,
        -1,
        999999999,
    ],
)
@mark.asyncio
async def test_update_license_server__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_license_server,
    read_object,
    id,
):
    new_license_server = {"host": "licserv9999.com"}

    inject_security_header("owner1", Permissions.LICENSE_SERVER_EDIT)
    response = await backend_client.put(f"/lm/license_servers/{id}", json=new_license_server)

    assert response.status_code == 404


@mark.asyncio
async def test_update_license_server__fail_with_bad_data(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_license_server,
    read_object,
):
    new_license_server = {"bla": "bla"}

    id = create_one_license_server[0].id

    inject_security_header("owner1", Permissions.LICENSE_SERVER_EDIT)
    response = await backend_client.put(f"/lm/license_servers/{id}", json=new_license_server)

    assert response.status_code == 400


@mark.asyncio
async def test_delete_license_server__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_license_server,
    read_object,
):
    id = create_one_license_server[0].id

    inject_security_header("owner1", Permissions.LICENSE_SERVER_EDIT)
    response = await backend_client.delete(f"/lm/license_servers/{id}")

    assert response.status_code == 200
    stmt = select(LicenseServer).where(LicenseServer.id == id)
    fetch_license_server = await read_object(stmt)

    assert fetch_license_server is None


@mark.parametrize(
    "id",
    [
        0,
        -1,
        999999999,
    ],
)
@mark.asyncio
async def test_delete_license_server__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_license_server,
    id,
):
    inject_security_header("owner1", Permissions.LICENSE_SERVER_EDIT)
    response = await backend_client.delete(f"/lm/license_servers/{id}")

    assert response.status_code == 404
