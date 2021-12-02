import respx
from httpx import ConnectError, Response
from pytest import mark, raises

from lm_agent.backend_utils import (
    LicenseManagerBackendConnectionError,
    get_config_from_backend,
    get_license_manager_backend_version,
)
from lm_agent.config import settings


@mark.asyncio
async def test_get_license_manager_backend_version__returns_version_on_two_hundred(respx_mock):
    test_backend_version = "2.5.4"
    respx.get(f"{settings.BACKEND_BASE_URL}/lm/version").mock(
        return_value=Response(
            200,
            json=dict(version=test_backend_version),
        ),
    )
    backend_version = await get_license_manager_backend_version()
    assert backend_version == test_backend_version


@mark.asyncio
async def test_get_license_manager_backend_version__raises_exception_on_non_two_hundred(respx_mock):
    respx.get(f"{settings.BACKEND_BASE_URL}/lm/version").mock(return_value=Response(500))
    with raises(LicenseManagerBackendConnectionError):
        await get_license_manager_backend_version()


@mark.asyncio
async def test_get_config_from_backend__omits_invalid_config_rows(
    caplog,
    respx_mock,
):
    respx.get(f"{settings.BACKEND_BASE_URL}/lm/api/v1/config/all").mock(
        return_value=Response(
            200,
            json=[
                # Valid config row
                dict(
                    product="SomeProduct",
                    features={"A": 1, "list": 2, "of": 3, "features": 4},
                    license_servers=["A", "list", "of", "license", "servers"],
                    license_server_type="O-Negative",
                    grace_time=13,
                ),
                # Invalid config row
                dict(bad="Data. Should NOT work"),
                # Another valid conig row
                dict(
                    product="AnotherProduct",
                    features={"A": 1, "colletion": 2, "of": 3, "features": 4},
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
    respx_mock,
):
    respx.get(f"{settings.BACKEND_BASE_URL}/lm/api/v1/config/all").mock(
        side_effect=ConnectError("BOOM"),
    )
    configs = await get_config_from_backend()
    assert configs == []
    assert "Connection failed to backend" in caplog.text
