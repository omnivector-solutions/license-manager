from unittest import mock

from fastapi import HTTPException
from httpx import AsyncClient
from pytest import mark
from sqlalchemy import select

from lm_api.api.models.configuration import Configuration
from lm_api.permissions import Permissions


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_CREATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_add_configuration__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    read_object,
):
    data = {
        "name": "Abaqus",
        "cluster_client_id": "dummy",
        "grace_time": 60,
        "features": [],
        "license_servers": [],
        "type": "flexlm",
    }

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.post("/lm/configurations", json=data)
    assert response.status_code == 201

    stmt = select(Configuration).where(Configuration.name == "Abaqus")
    fetched = await read_object(stmt)

    assert fetched.name == "Abaqus"
    assert fetched.cluster_client_id == "dummy"
    assert fetched.grace_time == 60
    assert fetched.type == "flexlm"


@mark.parametrize(
    "invalid_payload,expected_status_code,permission",
    [
        (
            {
                "name": "Abaqus",
                "cluster_client_id": None,  # bad cluster_client_id
                "grace_time": 60,
                "features": [],
                "license_servers": [],
                "type": "flexlm",
            },
            422,
            Permissions.CONFIG_CREATE,
        ),
        (
            {
                "name": "Abaqus",
                "cluster_client_id": None,  # bad cluster_client_id
                "grace_time": 60,
                "features": [],
                "license_servers": [],
                "type": "flexlm",
            },
            422,
            Permissions.ADMIN,
        ),
        (
            {
                "name": "Abaqus",
                "cluster_client_id": "dummy",
                "grace_time": -1,  # bad grace time
                "features": [],
                "license_servers": [],
                "type": "flexlm",
            },
            422,
            Permissions.CONFIG_CREATE,
        ),
        (
            {
                "name": "Abaqus",
                "cluster_client_id": "dummy",
                "grace_time": 60,
                "features": [],
                "license_servers": [],
                "type": "bla",  # bad license server type
            },
            422,
            Permissions.CONFIG_CREATE,
        ),
        (
            {
                "name": "Abaqus",
                "cluster_client_id": "dummy",
                "grace_time": 60,
                "features": [],
                "license_servers": [
                    {
                        "host": "licserv0001",
                        "port": -1,  # bad license server port
                    }
                ],
                "type": "flexlm",
            },
            422,
            Permissions.CONFIG_CREATE,
        ),
        (
            {
                "name": "Abaqus",
                "cluster_client_id": "dummy",
                "grace_time": 60,
                "features": [],
                "license_servers": [
                    {
                        "host": "licserv0001",
                        "port": 700000000,  # bad license server port
                    }
                ],
                "type": "flexlm",
            },
            422,
            Permissions.CONFIG_CREATE,
        ),
        (
            {
                "name": "Abaqus",
                "cluster_client_id": "dummy",
                "grace_time": 60,
                "features": [],
                "license_servers": [
                    {
                        "host": "not a valid host name",  # bad license server host
                        "port": 1234,
                    }
                ],
                "type": "flexlm",
            },
            422,
            Permissions.CONFIG_CREATE,
        ),
    ],
)
@mark.asyncio
async def test_add_configuration__fail_with_bad_payload(
    invalid_payload,
    expected_status_code,
    permission,
    backend_client: AsyncClient,
    inject_security_header,
):
    inject_security_header("owner1@test.com", permission)
    response = await backend_client.post("/lm/configurations", json=invalid_payload)
    assert response.status_code == expected_status_code


@mock.patch("lm_api.api.routes.configurations.crud_configuration.create")
@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_CREATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_add_configuration__fail(
    mock_create,
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    read_object,
):
    mock_create.side_effect = HTTPException(status_code=400, detail="Configuration could not be created")

    data = {
        "name": "Abaqus",
        "cluster_client_id": "dummy",
        "grace_time": 60,
        "features": [],
        "license_servers": [],
        "type": "flexlm",
    }

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.post("/lm/configurations", json=data)
    assert response.status_code == 400


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_CREATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_add_configuration__with__features(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    read_object,
    create_one_product,
):
    product_id = create_one_product[0].id

    data = {
        "name": "Abaqus",
        "cluster_client_id": "dummy",
        "grace_time": 60,
        "features": [
            {
                "name": "abaqus1",
                "product_id": product_id,
                "reserved": 0,
            },
            {
                "name": "abaqus2",
                "product_id": product_id,
                "reserved": 0,
            },
        ],
        "license_servers": [],
        "type": "flexlm",
    }

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.post("/lm/configurations", json=data)
    assert response.status_code == 201

    stmt = select(Configuration).where(Configuration.name == "Abaqus")
    fetched = await read_object(stmt)

    assert fetched.name == "Abaqus"
    assert len(fetched.features) == 2
    assert fetched.features[0].name == "abaqus1"
    assert fetched.features[0].product.name == "Abaqus"
    assert fetched.features[1].name == "abaqus2"
    assert fetched.features[1].product.name == "Abaqus"


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_CREATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_add_configuration__with_features__fail_with_bad_reserved(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    read_object,
    create_one_product,
):
    product_id = create_one_product[0].id

    data = {
        "name": "Abaqus",
        "cluster_client_id": "dummy",
        "grace_time": 60,
        "features": [
            {
                "name": "abaqus1",
                "product_id": product_id,
                "reserved": -1,
            }
        ],
        "license_servers": [],
        "type": "flexlm",
    }

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.post("/lm/configurations", json=data)
    assert response.status_code == 422


@mock.patch("lm_api.api.routes.configurations.crud_feature.create")
@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_CREATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_add_configuration__with__features__fail(
    mock_create_feature,
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_product,
    read_object,
):
    product_id = create_one_product[0].id

    mock_create_feature.side_effect = HTTPException(400, "Feature could not be created")

    data = {
        "name": "Abaqus",
        "cluster_client_id": "dummy",
        "grace_time": 60,
        "features": [
            {
                "name": "abaqus1",
                "product_id": product_id,
                "reserved": 0,
            },
        ],
        "license_servers": [],
        "type": "flexlm",
    }

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.post("/lm/configurations", json=data)

    assert response.status_code == 400
    assert await read_object(select(Configuration).where(Configuration.name == "Abaqus")) is None


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_CREATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_add_configuration__with__license_servers(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    read_object,
):
    data = {
        "name": "Abaqus",
        "cluster_client_id": "dummy",
        "grace_time": 60,
        "features": [],
        "license_servers": [
            {
                "host": "licserv0001",
                "port": 1234,
            },
            {
                "host": "licserv0002",
                "port": 2345,
            },
        ],
        "type": "flexlm",
    }

    inject_security_header("owner1@test.com", permission)

    response = await backend_client.post("/lm/configurations", json=data)
    assert response.status_code == 201

    stmt = select(Configuration).where(Configuration.name == "Abaqus")
    fetched = await read_object(stmt)

    assert fetched.name == "Abaqus"
    assert len(fetched.license_servers) == 2
    assert fetched.license_servers[0].host == "licserv0001"
    assert fetched.license_servers[0].port == 1234
    assert fetched.license_servers[1].host == "licserv0002"
    assert fetched.license_servers[1].port == 2345


@mock.patch("lm_api.api.routes.configurations.crud_license_server.create")
@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_CREATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_add_configuration__with__license_servers__fail(
    mock_create_license_server,
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    read_object,
):
    mock_create_license_server.side_effect = HTTPException(400, "License server could not be created")

    data = {
        "name": "Abaqus",
        "cluster_client_id": "dummy",
        "grace_time": 60,
        "features": [],
        "license_servers": [
            {
                "host": "licserv0001",
                "port": 1234,
            },
        ],
        "type": "flexlm",
    }

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.post("/lm/configurations", json=data)

    assert response.status_code == 400
    assert await read_object(select(Configuration).where(Configuration.name == "Abaqus")) is None


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_CREATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_add_configuration__with__features_and_license_servers(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    read_object,
    create_one_product,
):
    product_id = create_one_product[0].id

    data = {
        "name": "Abaqus",
        "cluster_client_id": "dummy",
        "grace_time": 60,
        "features": [
            {
                "name": "abaqus1",
                "product_id": product_id,
                "reserved": 0,
            },
            {
                "name": "abaqus2",
                "product_id": product_id,
                "reserved": 0,
            },
        ],
        "license_servers": [
            {
                "host": "licserv0001",
                "port": 1234,
            },
            {
                "host": "licserv0002",
                "port": 2345,
            },
        ],
        "type": "flexlm",
    }

    inject_security_header("owner1@test.com", permission)

    response = await backend_client.post("/lm/configurations", json=data)
    assert response.status_code == 201

    stmt = select(Configuration).where(Configuration.name == "Abaqus")
    fetched = await read_object(stmt)

    assert fetched.name == "Abaqus"
    assert len(fetched.features) == 2
    assert fetched.features[0].name == "abaqus1"
    assert fetched.features[0].product.name == "Abaqus"
    assert fetched.features[1].name == "abaqus2"
    assert fetched.features[1].product.name == "Abaqus"
    assert len(fetched.license_servers) == 2
    assert fetched.license_servers[0].host == "licserv0001"
    assert fetched.license_servers[0].port == 1234
    assert fetched.license_servers[1].host == "licserv0002"
    assert fetched.license_servers[1].port == 2345


@mock.patch("lm_api.api.routes.configurations.crud_license_server.create")
@mock.patch("lm_api.api.routes.configurations.crud_feature.create")
@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_CREATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_add_configuration__with__features_and_license_servers__fail(
    mock_create_feature,
    mock_create_license_server,
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    read_object,
    create_one_product,
):
    mock_create_feature.side_effect = HTTPException(400, "Feature could not be created")
    mock_create_license_server.side_effect = HTTPException(400, "License server could not be created")

    product_id = create_one_product[0].id

    data = {
        "name": "Abaqus",
        "cluster_client_id": "dummy",
        "grace_time": 60,
        "features": [
            {
                "name": "abaqus1",
                "product_id": product_id,
                "reserved": 0,
            },
            {
                "name": "abaqus2",
                "product_id": product_id,
                "reserved": 0,
            },
        ],
        "license_servers": [
            {
                "host": "licserv0001",
                "port": 1234,
            },
        ],
        "type": "flexlm",
    }

    inject_security_header("owner1@test.com", permission)

    response = await backend_client.post("/lm/configurations", json=data)
    assert response.status_code == 400

    stmt = select(Configuration).where(Configuration.name == "Abaqus")
    fetched = await read_object(stmt)

    assert fetched is None


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_READ,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_get_all_configurations__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_configurations,
):
    inject_security_header("owner1@test.com", permission)
    response = await backend_client.get("/lm/configurations")

    assert response.status_code == 200

    response_configurations = response.json()
    assert response_configurations[0]["name"] == create_configurations[0].name
    assert response_configurations[0]["cluster_client_id"] == create_configurations[0].cluster_client_id
    assert response_configurations[0]["grace_time"] == create_configurations[0].grace_time
    assert response_configurations[0]["type"] == create_configurations[0].type

    assert response_configurations[1]["name"] == create_configurations[1].name
    assert response_configurations[1]["cluster_client_id"] == create_configurations[1].cluster_client_id
    assert response_configurations[1]["grace_time"] == create_configurations[1].grace_time
    assert response_configurations[1]["type"] == create_configurations[1].type


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_READ,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_get_all_configurations__with_search(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_configurations,
):
    inject_security_header("owner1@test.com", permission)
    response = await backend_client.get(f"/lm/configurations?search={create_configurations[0].name}")

    assert response.status_code == 200

    response_configuration = response.json()
    assert response_configuration[0]["name"] == create_configurations[0].name
    assert response_configuration[0]["cluster_client_id"] == create_configurations[0].cluster_client_id
    assert response_configuration[0]["grace_time"] == create_configurations[0].grace_time
    assert response_configuration[0]["type"] == create_configurations[0].type


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_READ,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_get_all_configurations__with_sort(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_configurations,
):
    inject_security_header("owner1@test.com", permission)
    response = await backend_client.get("/lm/configurations?sort_field=name&sort_ascending=false")

    assert response.status_code == 200

    response_configurations = response.json()
    assert response_configurations[0]["name"] == create_configurations[1].name
    assert response_configurations[0]["cluster_client_id"] == create_configurations[1].cluster_client_id
    assert response_configurations[0]["grace_time"] == create_configurations[1].grace_time
    assert response_configurations[0]["type"] == create_configurations[1].type

    assert response_configurations[1]["name"] == create_configurations[0].name
    assert response_configurations[1]["cluster_client_id"] == create_configurations[0].cluster_client_id
    assert response_configurations[1]["grace_time"] == create_configurations[0].grace_time
    assert response_configurations[1]["type"] == create_configurations[0].type


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_READ,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_get_configuration__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_configuration,
):
    id = create_one_configuration[0].id

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.get(f"/lm/configurations/{id}")

    assert response.status_code == 200

    response_configuration = response.json()
    assert response_configuration["name"] == create_one_configuration[0].name
    assert response_configuration["cluster_client_id"] == create_one_configuration[0].cluster_client_id
    assert response_configuration["grace_time"] == create_one_configuration[0].grace_time
    assert response_configuration["type"] == create_one_configuration[0].type


@mark.parametrize(
    "id,permission",
    [
        (0, Permissions.CONFIG_READ),
        (-1, Permissions.CONFIG_READ),
        (999999999, Permissions.CONFIG_READ),
        (0, Permissions.ADMIN),
        (-1, Permissions.ADMIN),
        (999999999, Permissions.ADMIN),
    ],
)
@mark.asyncio
async def test_get_configuration__fail_with_bad_parameter(
    id,
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_configuration,
):
    inject_security_header("owner1@test.com", permission)
    response = await backend_client.get(f"/lm/configurations/{id}")

    assert response.status_code == 404


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_UPDATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_update_configuration__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_configuration,
    read_object,
):
    new_configuration = {
        "name": "New Abaqus",
    }

    id = create_one_configuration[0].id

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.put(f"/lm/configurations/{id}", json=new_configuration)

    assert response.status_code == 200

    stmt = select(Configuration).where(Configuration.id == id)
    fetch_configuration = await read_object(stmt)

    assert fetch_configuration.name == new_configuration["name"]


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_UPDATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_update_configuration__with_feature_creation__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_configuration,
    read_object,
    create_one_product,
):
    new_configuration = {
        "name": "New Abaqus",
        "features": [
            {
                "name": "abaqus1",
                "product_id": create_one_product[0].id,
                "reserved": 0,
            },
        ],
    }

    id = create_one_configuration[0].id

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.put(f"/lm/configurations/{id}", json=new_configuration)

    assert response.status_code == 200

    stmt = select(Configuration).where(Configuration.id == id)
    fetch_configuration = await read_object(stmt)

    assert fetch_configuration.name == new_configuration["name"]
    assert len(fetch_configuration.features) == 1
    assert fetch_configuration.features[0].name == "abaqus1"
    assert fetch_configuration.features[0].product.name == "Abaqus"


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_UPDATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_update_configuration__with_feature_update__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_configuration,
    read_object,
    create_one_product,
    create_one_feature,
):
    new_configuration = {
        "name": "New Abaqus",
        "features": [
            {
                "id": create_one_feature[0].id,
                "name": "abaqus1",
                "product_id": create_one_product[0].id,
                "reserved": 0,
            },
        ],
    }

    id = create_one_configuration[0].id

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.put(f"/lm/configurations/{id}", json=new_configuration)

    assert response.status_code == 200

    stmt = select(Configuration).where(Configuration.id == id)
    fetch_configuration = await read_object(stmt)

    assert fetch_configuration.name == new_configuration["name"]
    assert len(fetch_configuration.features) == 1
    assert fetch_configuration.features[0].name == "abaqus1"
    assert fetch_configuration.features[0].product.name == "Abaqus"


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_UPDATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_update_configuration__with_all_feature_deletion__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_configuration,
    read_object,
    create_one_product,
    create_one_feature,
):
    new_configuration = {
        "name": "New Abaqus",
        "features": [],
    }

    id = create_one_configuration[0].id

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.put(f"/lm/configurations/{id}", json=new_configuration)

    assert response.status_code == 200

    stmt = select(Configuration).where(Configuration.id == id)
    fetch_configuration = await read_object(stmt)

    assert fetch_configuration.name == new_configuration["name"]
    assert len(fetch_configuration.features) == 0


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_UPDATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_update_configuration__with_one_feature_deletion__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_configuration,
    read_object,
    create_one_product,
    create_features,
):
    new_configuration = {
        "name": "New Abaqus",
        "features": [{"name": "abaqus1", "product_id": create_one_product[0].id, "reserved": 0}],
    }

    id = create_one_configuration[0].id

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.put(f"/lm/configurations/{id}", json=new_configuration)

    assert response.status_code == 200

    stmt = select(Configuration).where(Configuration.id == id)
    fetch_configuration = await read_object(stmt)

    assert fetch_configuration.name == new_configuration["name"]
    assert len(fetch_configuration.features) == 1
    assert fetch_configuration.features[0].name == "abaqus1"
    assert fetch_configuration.features[0].product.name == "Abaqus"


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_UPDATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_update_configuration__with_license_server_creation__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_configuration,
    read_object,
):
    new_configuration = {
        "name": "New Abaqus",
        "license_servers": [
            {
                "host": "host1",
                "port": 1234,
            },
        ],
    }

    id = create_one_configuration[0].id

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.put(f"/lm/configurations/{id}", json=new_configuration)

    assert response.status_code == 200

    stmt = select(Configuration).where(Configuration.id == id)
    fetch_configuration = await read_object(stmt)

    assert fetch_configuration.name == new_configuration["name"]
    assert len(fetch_configuration.license_servers) == 1
    assert fetch_configuration.license_servers[0].host == "host1"
    assert fetch_configuration.license_servers[0].port == 1234


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_UPDATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_update_configuration__with_license_server_update__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_configuration,
    read_object,
    create_one_license_server,
):
    new_configuration = {
        "name": "New Abaqus",
        "license_servers": [
            {
                "id": create_one_license_server[0].id,
                "host": "host2",
                "port": 2345,
            },
        ],
    }

    id = create_one_configuration[0].id

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.put(f"/lm/configurations/{id}", json=new_configuration)

    assert response.status_code == 200

    stmt = select(Configuration).where(Configuration.id == id)
    fetch_configuration = await read_object(stmt)

    assert fetch_configuration.name == new_configuration["name"]
    assert len(fetch_configuration.license_servers) == 1
    assert fetch_configuration.license_servers[0].host == "host2"
    assert fetch_configuration.license_servers[0].port == 2345


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_UPDATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_update_configuration__with_all_license_server_deletion__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_configuration,
    read_object,
    create_one_product,
    create_one_feature,
):
    new_configuration = {
        "name": "New Abaqus",
        "license_servers": [],
    }

    id = create_one_configuration[0].id

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.put(f"/lm/configurations/{id}", json=new_configuration)

    assert response.status_code == 200

    stmt = select(Configuration).where(Configuration.id == id)
    fetch_configuration = await read_object(stmt)

    assert fetch_configuration.name == new_configuration["name"]
    assert len(fetch_configuration.license_servers) == 0


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_UPDATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_update_configuration__with_one_license_server_deletion__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_configuration,
    read_object,
    create_one_product,
    create_license_servers,
):
    new_configuration = {
        "name": "New Abaqus",
        "license_servers": [
            {
                "host": "host1",
                "port": 1234,
            },
        ],
    }

    id = create_one_configuration[0].id

    inject_security_header("owner1@test.com", permission)

    response = await backend_client.put(f"/lm/configurations/{id}", json=new_configuration)

    assert response.status_code == 200

    stmt = select(Configuration).where(Configuration.id == id)
    fetch_configuration = await read_object(stmt)
    assert fetch_configuration.name == new_configuration["name"]
    assert len(fetch_configuration.license_servers) == 1
    assert fetch_configuration.license_servers[0].host == "host1"
    assert fetch_configuration.license_servers[0].port == 1234


@mark.parametrize(
    "id,permission",
    [
        (0, Permissions.CONFIG_UPDATE),
        (-1, Permissions.CONFIG_UPDATE),
        (999999999, Permissions.CONFIG_UPDATE),
        (0, Permissions.ADMIN),
        (-1, Permissions.ADMIN),
        (999999999, Permissions.ADMIN),
    ],
)
@mark.asyncio
async def test_update_configuration__fail_with_bad_parameter(
    id,
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_configuration,
    read_object,
):
    new_configuration = {
        "name": "New Abaqus",
    }

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.put(f"/lm/configurations/{id}", json=new_configuration)

    assert response.status_code == 404


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_UPDATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_update_configuration__fail_with_bad_data(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_configuration,
    read_object,
):
    new_configuration = {
        "bla": "bla",
    }

    id = create_one_configuration[0].id

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.put(f"/lm/configurations/{id}", json=new_configuration)

    assert response.status_code == 400


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_DELETE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_delete_configuration__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_configuration,
    read_object,
):
    id = create_one_configuration[0].id

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.delete(f"/lm/configurations/{id}")

    assert response.status_code == 200
    stmt = select(Configuration).where(Configuration.id == id)
    fetch_configuration = await read_object(stmt)

    assert fetch_configuration is None


@mark.parametrize(
    "id,permission",
    [
        (0, Permissions.CONFIG_DELETE),
        (-1, Permissions.CONFIG_DELETE),
        (999999999, Permissions.CONFIG_DELETE),
        (0, Permissions.ADMIN),
        (-1, Permissions.ADMIN),
        (999999999, Permissions.ADMIN),
    ],
)
@mark.asyncio
async def test_delete_configuration__fail_with_bad_parameter(
    id,
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_configuration,
):
    inject_security_header("owner1@test.com", permission)
    response = await backend_client.delete(f"/lm/configurations/{id}")

    assert response.status_code == 404


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_READ,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_get_configurations_by_client_id__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_configuration,
):
    id = create_one_configuration[0].id
    cluster_client_id = create_one_configuration[0].cluster_client_id

    inject_security_header("owner@test1.com", permission, client_id="not-the-correct-client-id")
    response = await backend_client.get("/lm/configurations/by_client_id")

    assert response.status_code == 200
    assert response.json() == []

    inject_security_header("owner@test1.com", permission, client_id=cluster_client_id)
    response = await backend_client.get("/lm/configurations/by_client_id")

    response_configurations = response.json()

    assert response.status_code == 200
    assert response_configurations[0]["id"] == id
    assert response_configurations[0]["name"] == create_one_configuration[0].name
    assert response_configurations[0]["cluster_client_id"] == create_one_configuration[0].cluster_client_id
    assert response_configurations[0]["grace_time"] == create_one_configuration[0].grace_time
    assert response_configurations[0]["type"] == create_one_configuration[0].type


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_READ,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_get_configurations_by_client_id__fail_with_bad_client_id(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
):
    inject_security_header("owner1@test.com", permission, client_id=None)

    response = await backend_client.get("/lm/configurations/by_client_id")

    assert response.status_code == 400
