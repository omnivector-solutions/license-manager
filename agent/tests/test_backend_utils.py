import respx
from httpx import AsyncClient, ConnectError, Response
from pytest import fixture, mark

from lm_agent.backend_utils import get_config_from_backend


@mark.asyncio
async def test_get_config_from_backend__omits_invalid_config_rows(
    caplog,
):
    with respx.mock:
        respx.get("http://backend/api/v1/config/all").mock(
            return_value=Response(
                200,
                json=[
                    # Valid conig row
                    dict(
                        product="SomeProduct",
                        features=["A", "list", "of", "features"],
                        license_servers=["A", "list", "of", "license", "servers"],
                        license_server_type="O-Negative",
                        grace_time=13,
                    ),
                    # Invalid config row
                    dict(bad="Data. Should NOT work"),
                    # Another valid conig row
                    dict(
                        product="AnotherProduct",
                        features=["A", "collection", "of", "features"],
                        license_servers=["A", "collection", "of", "license", "servers"],
                        license_server_type="AB-Positive",
                        grace_time=21,
                    ),
                ],
            ),
        )
        configs = await get_config_from_backend()
    assert [c.product for c in configs] == ["SomeProduct", "AnotherProduct"]
    assert "Could not validate config entry at row 1" in caplog.text


@mark.asyncio
async def test_get_config_from_backend__returns_empty_list_on_connect_error(
    caplog,
):
    with respx.mock:
        respx.get("http://backend/api/v1/config/all").mock(
            side_effect=ConnectError("BOOM"),
        )
        configs = await get_config_from_backend()
    assert configs == []
    assert "Connection failed to backend" in caplog.text
