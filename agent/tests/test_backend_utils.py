import logging
from datetime import datetime, timezone
from unittest.mock import patch

import jwt
import respx
from httpx import ConnectError, Response
from pytest import fixture, mark, raises

from lm_agent.backend_utils import (
    _load_token_from_cache,
    _write_token_to_cache,
    acquire_token,
    check_backend_health,
    get_config_from_backend,
)
from lm_agent.config import settings
from lm_agent.exceptions import LicenseManagerBackendConnectionError


def test__write_token_to_cache__caches_a_token(mock_cache_dir):
    """
    Verifies that the auth token can be saved in the cache.
    """
    mock_cache_dir.mkdir(parents=True)
    _write_token_to_cache("dummy-token")
    token_path = mock_cache_dir / "auth-token"
    assert token_path.exists()
    assert token_path.read_text() == "dummy-token"


def test__write_token_to_cache__creates_cache_directory_if_does_not_exist(mock_cache_dir):
    """
    Verifies that the cache directory will be created if it does not already exist.
    """
    assert not mock_cache_dir.exists()
    _write_token_to_cache("dummy-token")
    assert mock_cache_dir.exists()


def test__write_token_to_cache__warns_if_token_cannot_be_created(mock_cache_dir, caplog):
    """
    Verifies that a warning is logged if the token file cannot be written.
    """
    mock_cache_dir.mkdir(parents=True)
    token_path = mock_cache_dir / "auth-token"
    token_path.write_text("pre-existing data")
    token_path.chmod(0o000)

    with caplog.at_level(logging.WARNING):
        _write_token_to_cache("dummy-token")

    token_path.chmod(0o600)
    assert token_path.exists()
    assert token_path.read_text() == "pre-existing data"
    assert "Couldn't save token" in caplog.text


def test__load_token_from_cache__loads_token_data_from_the_cache(mock_cache_dir):
    """
    Verifies that a token can be retrieved from the cache.
    """
    mock_cache_dir.mkdir(parents=True)
    token_path = mock_cache_dir / "auth-token"
    one_minute_from_now = int(datetime.now(tz=timezone.utc).timestamp()) + 60
    created_token = jwt.encode(
        dict(exp=one_minute_from_now),
        key="dummy-key",
        algorithm="HS256",
    )
    token_path.write_text(created_token)
    retrieved_token = _load_token_from_cache()
    assert retrieved_token == created_token


def test__load_token_from_cache__returns_none_if_cached_token_does_not_exist(mock_cache_dir):
    """
    Verifies that None is returned if the cached token does not exist.
    """
    mock_cache_dir.mkdir(parents=True)
    retrieved_token = _load_token_from_cache()
    assert retrieved_token is None


def test__load_token_from_cache__returns_none_and_warns_if_cached_token_cannot_be_read(
    mock_cache_dir, caplog
):
    """
    Verifies that None is returned if the token cannot be read. Also checks that a warning is logged.
    """
    mock_cache_dir.mkdir(parents=True)
    token_path = mock_cache_dir / "auth-token"
    token_path.write_text("pre-existing data")
    token_path.chmod(0o000)

    with caplog.at_level(logging.WARNING):
        retrieved_token = _load_token_from_cache()

    assert retrieved_token is None
    assert "Couldn't load token" in caplog.text


def test__load_token_from_cache__returns_none_and_warns_if_cached_token_is_expired(mock_cache_dir, caplog):
    """
    Verifies that None is returned if the token is expired. Also checks that a warning is logged.
    """
    mock_cache_dir.mkdir(parents=True)
    token_path = mock_cache_dir / "auth-token"
    one_second_ago = int(datetime.now(tz=timezone.utc).timestamp()) - 1
    expired_token = jwt.encode(dict(exp=one_second_ago), key="dummy-key", algorithm="HS256")
    token_path.write_text(expired_token)

    with caplog.at_level(logging.WARNING):
        retrieved_token = _load_token_from_cache()

    assert retrieved_token is None
    assert "Cached token is expired" in caplog.text


def test__load_token_from_cache__returns_none_and_warns_if_cached_token_will_expire_soon(
    mock_cache_dir, caplog
):
    """
    Verifies that None is returned if the token will expired soon. Also checks that a warning is logged.
    """
    mock_cache_dir.mkdir(parents=True)
    token_path = mock_cache_dir / "auth-token"
    nine_seconds_from_now = int(datetime.now(tz=timezone.utc).timestamp()) + 9
    expired_token = jwt.encode(dict(exp=nine_seconds_from_now), key="dummy-key", algorithm="HS256")
    token_path.write_text(expired_token)

    with caplog.at_level(logging.WARNING):
        retrieved_token = _load_token_from_cache()

    assert retrieved_token is None
    assert "Cached token is expired" in caplog.text


def test_acquire_token__gets_a_token_from_the_cache(mock_cache_dir):
    """
    Verifies that the token is retrieved from the cache if it is found there.
    """
    mock_cache_dir.mkdir(parents=True)
    token_path = mock_cache_dir / "auth-token"
    one_minute_from_now = int(datetime.now(tz=timezone.utc).timestamp()) + 60
    created_token = jwt.encode(
        dict(exp=one_minute_from_now),
        key="dummy-key",
        algorithm="HS256",
    )
    token_path.write_text(created_token)
    retrieved_token = acquire_token()
    assert retrieved_token == created_token


def test_acquire_token__gets_a_token_from_auth_0_if_one_is_not_in_the_cache(mock_cache_dir, respx_mock):
    """
    Verifies that a token is pulled from auth0 if it is not found in the cache.
    Also checks to make sure the token is cached.
    """
    mock_cache_dir.mkdir(parents=True)
    token_path = mock_cache_dir / "auth-token"
    assert not token_path.exists()

    retrieved_token = acquire_token()
    assert retrieved_token == "dummy-token"

    token_path = mock_cache_dir / "auth-token"
    assert token_path.read_text() == retrieved_token


@mark.asyncio
async def test_check_backend_health__success_on_two_hundered(respx_mock):
    respx.get(f"{settings.BACKEND_BASE_URL}/lm/health").mock(return_value=Response(204))
    await check_backend_health()


@mark.asyncio
async def test_get_license_manager_backend_version__raises_exception_on_non_two_hundred(respx_mock):
    respx.get(f"{settings.BACKEND_BASE_URL}/lm/health").mock(return_value=Response(500))
    with raises(LicenseManagerBackendConnectionError, match="Could not connect"):
        await check_backend_health()


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
