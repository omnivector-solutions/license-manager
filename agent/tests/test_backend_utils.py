import stat
from datetime import datetime, timezone

import jwt
import pytest
import respx
from httpx import ConnectError, Response
from pytest import mark, raises

from lm_agent.backend_utils import (
    TOKEN_FILE_NAME,
    _load_token_from_cache,
    _write_token_to_cache,
    acquire_token,
    check_backend_health,
    get_all_grace_times,
    get_bookings_sum_per_cluster,
    get_config_from_backend,
)
from lm_agent.config import settings
from lm_agent.exceptions import LicenseManagerBackendConnectionError


def test__write_token_to_cache__caches_a_token(mock_cache_dir):
    """
    Verifies that the auth token can be saved in the cache directory.
    """
    mock_cache_dir.mkdir()
    _write_token_to_cache("dummy-token")
    token_path = mock_cache_dir / TOKEN_FILE_NAME
    assert token_path.exists()
    assert token_path.read_text() == "dummy-token"

    # Assert that the permissions for the file are read/write only for the current user
    assert token_path.stat().st_mode & (stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO) == 0o600


def test__write_token_to_cache__warns_if_cache_dir_does_not_exist(caplog, mock_cache_dir):
    """
    Verifies that a warning is logged if the cache dire does not exists and that a token file is not created.
    """
    _write_token_to_cache("dummy-token")
    assert "Couldn't create missing cache directory" not in caplog.text

    token_path = mock_cache_dir / TOKEN_FILE_NAME
    assert not token_path.exists()


def test__write_token_to_cache__warns_if_token_cannot_be_created(caplog, mock_cache_dir):
    """
    Verifies that a warning is logged if the token file cannot be written.
    """
    mock_cache_dir.mkdir()
    token_path = mock_cache_dir / TOKEN_FILE_NAME
    token_path.write_text("pre-existing data")
    # Make file inaccessible permission-wise
    token_path.chmod(0o000)

    _write_token_to_cache("dummy-token")

    # Make file read/write again
    token_path.chmod(0o600)
    assert token_path.exists()
    assert token_path.read_text() == "pre-existing data"
    assert "Couldn't save token" in caplog.text


def test__load_token_from_cache__loads_token_data_from_the_cache(mock_cache_dir):
    """
    Verifies that a token can be retrieved from the cache.
    """
    mock_cache_dir.mkdir()
    token_path = mock_cache_dir / TOKEN_FILE_NAME
    one_minute_from_now = int(datetime.now(tz=timezone.utc).timestamp()) + 60
    created_token = jwt.encode(
        dict(exp=one_minute_from_now),
        key="dummy-key",
        algorithm="HS256",
    )
    token_path.write_text(created_token)
    retrieved_token = _load_token_from_cache()
    assert retrieved_token == created_token


def test__load_token_from_cache__returns_none_if_cached_token_does_not_exist():
    """
    Verifies that None is returned if the cached token does not exist.
    """
    retrieved_token = _load_token_from_cache()
    assert retrieved_token is None


def test__load_token_from_cache__returns_none_and_warns_if_cached_token_cannot_be_read(
    caplog, mock_cache_dir
):
    """
    Verifies that None is returned if the token cannot be read. Also checks that a warning is logged.
    """
    mock_cache_dir.mkdir()
    token_path = mock_cache_dir / TOKEN_FILE_NAME
    one_minute_from_now = int(datetime.now(tz=timezone.utc).timestamp()) + 60
    created_token = jwt.encode(
        dict(exp=one_minute_from_now),
        key="dummy-key",
        algorithm="HS256",
    )
    token_path.write_text(created_token)
    token_path.chmod(0o000)

    retrieved_token = _load_token_from_cache()
    assert retrieved_token is None
    assert "Couldn't load token" in caplog.text


def test__load_token_from_cache__returns_none_and_warns_if_cached_token_is_expired(caplog, mock_cache_dir):
    """
    Verifies that None is returned if the token is expired. Also checks that a warning is logged.
    """
    mock_cache_dir.mkdir()
    token_path = mock_cache_dir / TOKEN_FILE_NAME
    one_second_ago = int(datetime.now(tz=timezone.utc).timestamp()) - 1
    expired_token = jwt.encode(dict(exp=one_second_ago), key="dummy-key", algorithm="HS256")
    token_path.write_text(expired_token)

    retrieved_token = _load_token_from_cache()
    assert retrieved_token is None
    assert "Cached token is expired" in caplog.text


def test__load_token_from_cache__returns_none_and_warns_if_cached_token_will_expire_soon(
    caplog, mock_cache_dir
):
    """
    Verifies that None is returned if the token will expired soon. Also checks that a warning is logged.
    """
    mock_cache_dir.mkdir()
    token_path = mock_cache_dir / TOKEN_FILE_NAME
    nine_seconds_from_now = int(datetime.now(tz=timezone.utc).timestamp()) + 9
    expired_token = jwt.encode(dict(exp=nine_seconds_from_now), key="dummy-key", algorithm="HS256")
    token_path.write_text(expired_token)

    retrieved_token = _load_token_from_cache()
    assert retrieved_token is None
    assert "Cached token is expired" in caplog.text


def test_acquire_token__gets_a_token_from_the_cache(mock_cache_dir):
    """
    Verifies that the token is retrieved from the cache if it is found there.
    """
    mock_cache_dir.mkdir()
    token_path = mock_cache_dir / TOKEN_FILE_NAME
    one_minute_from_now = int(datetime.now(tz=timezone.utc).timestamp()) + 60
    created_token = jwt.encode(
        dict(exp=one_minute_from_now),
        key="dummy-key",
        algorithm="HS256",
    )
    token_path.write_text(created_token)
    retrieved_token = acquire_token()
    assert retrieved_token == created_token


def test_acquire_token__gets_a_token_from_auth_0_if_one_is_not_in_the_cache(respx_mock, mock_cache_dir):
    """
    Verifies that a token is pulled from OIDC if it is not found in the cache.
    Also checks to make sure the token is cached.
    """
    mock_cache_dir.mkdir()
    token_path = mock_cache_dir / TOKEN_FILE_NAME
    assert not token_path.exists()

    retrieved_token = acquire_token()
    assert retrieved_token == "dummy-token"

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
    respx.get(f"{settings.BACKEND_BASE_URL}/lm/api/v1/config/agent/all").mock(
        return_value=Response(
            200,
            json=[
                # Valid config row
                dict(
                    product="SomeProduct",
                    features={
                        "A": {"total": 1, "limit": 1},
                        "list": {"total": 2, "limit": 2},
                        "of": {"total": 3, "limit": 3},
                        "features": {"total": 4, "limit": 4},
                    },
                    license_servers=["A", "list", "of", "license", "servers"],
                    license_server_type="O-Negative",
                    grace_time=13,
                    client_id="cluster-staging",
                ),
                # Invalid config row
                dict(bad="Data. Should NOT work"),
                # Another valid conig row
                dict(
                    product="AnotherProduct",
                    features={
                        "A": {"total": 1, "limit": 1},
                        "colletion": {"total": 2, "limit": 2},
                        "of": {"total": 3, "limit": 3},
                        "features": {"total": 4, "limit": 4},
                    },
                    license_servers=["A", "collection", "of", "license", "servers"],
                    license_server_type="AB-Positive",
                    grace_time=21,
                    client_id="cluster-staging",
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
    respx.get(f"{settings.BACKEND_BASE_URL}/lm/api/v1/config/agent/all").mock(
        side_effect=ConnectError("BOOM"),
    )
    configs = await get_config_from_backend()
    assert configs == []
    assert "Connection failed to backend" in caplog.text


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
async def test_get_all_grace_times(respx_mock):
    """
    Check the return value for the get_all_grace_times.
    """
    respx_mock.get("/lm/api/v1/config/all").mock(
        return_value=Response(
            status_code=200,
            json=[
                {"id": 1, "grace_time": 100},
                {"id": 2, "grace_time": 300},
            ],
        )
    )
    grace_times = await get_all_grace_times()
    assert grace_times == {1: 100, 2: 300}


@mark.asyncio
@pytest.mark.respx(base_url="http://backend")
async def test_get_bookings_sum_per_cluster(bookings, respx_mock):
    """Test that get_bookings_sum_per_clusters returns the correct sum of bookings for each clusters."""
    respx_mock.get("/lm/api/v1/booking/all").mock(
        return_value=Response(
            status_code=200,
            json=bookings,
        )
    )
    assert await get_bookings_sum_per_cluster("product.feature") == {
        "cluster1": 15,
        "cluster2": 17,
        "cluster3": 71,
    }
    assert await get_bookings_sum_per_cluster("product2.feature2") == {
        "cluster4": 1,
    }
