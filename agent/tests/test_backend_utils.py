import stat
from datetime import datetime, timezone
from unittest import mock

import jwt
import pytest
import respx
from httpx import Response
from pytest import mark, raises

from lm_agent.backend_utils.models import (
    BookingSchema,
    ConfigurationSchema,
    FeatureSchema,
    JobSchema,
    LicenseBooking,
    LicenseBookingRequest,
    LicenseServerSchema,
    LicenseServerType,
    ProductSchema,
)
from lm_agent.backend_utils.utils import (
    TOKEN_FILE_NAME,
    _load_token_from_cache,
    _write_token_to_cache,
    acquire_token,
    check_backend_health,
    get_all_features_bookings_sum,
    get_bookings_for_all_jobs,
    get_cluster_configs_from_backend,
    get_cluster_grace_times,
    get_cluster_jobs_from_backend,
    make_booking_request,
    make_feature_update,
    remove_job_by_slurm_job_id,
)
from lm_agent.config import settings
from lm_agent.exceptions import LicenseManagerBackendConnectionError, LicenseManagerParseError


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
async def test__check_backend_health__success_on_two_hundered(respx_mock):
    respx.get(f"{settings.BACKEND_BASE_URL}/lm/health").mock(return_value=Response(204))
    await check_backend_health()


@mark.asyncio
async def test__get_license_manager_backend_version__raises_exception_on_non_two_hundred(respx_mock):
    respx.get(f"{settings.BACKEND_BASE_URL}/lm/health").mock(return_value=Response(500))
    with raises(LicenseManagerBackendConnectionError, match="Could not connect"):
        await check_backend_health()


@mark.asyncio
@pytest.mark.respx(base_url="http://backend")
async def test__get_cluster_jobs_from_backend(jobs, respx_mock):
    """Test that get_jobs_from_backend parses and returns the jobs from the cluster."""
    respx_mock.get("/lm/jobs/by_client_id").mock(
        return_value=Response(
            status_code=200,
            json=jobs[:2],
        )
    )

    expected_jobs = [
        JobSchema(
            id=1,
            slurm_job_id="123",
            cluster_client_id="dummy",
            username="user1",
            lead_host="host1",
            bookings=[
                BookingSchema(id=1, job_id=1, feature_id=1, quantity=12),
                BookingSchema(id=2, job_id=1, feature_id=2, quantity=50),
            ],
        ),
        JobSchema(
            id=2,
            slurm_job_id="456",
            cluster_client_id="dummy",
            username="user2",
            lead_host="host2",
            bookings=[
                BookingSchema(id=3, job_id=2, feature_id=4, quantity=15),
                BookingSchema(id=4, job_id=2, feature_id=7, quantity=25),
            ],
        ),
    ]

    jobs = await get_cluster_jobs_from_backend()
    assert jobs == expected_jobs


@mark.asyncio
@pytest.mark.respx(base_url="http://backend")
async def test__get_cluster_configs_from_backend(configurations, respx_mock):
    """Test that get_configs_from_backend parses and returns the configurations from the cluster."""
    respx_mock.get("/lm/configurations/by_client_id").mock(
        return_value=Response(
            status_code=200,
            json=configurations,
        )
    )

    expected_configs = [
        ConfigurationSchema(
            id=1,
            name="Abaqus",
            cluster_client_id="dummy",
            features=[
                FeatureSchema(
                    id=1,
                    name="abaqus",
                    product=ProductSchema(id=1, name="abaqus"),
                    config_id=1,
                    reserved=100,
                    total=123,
                    used=12,
                    booked_total=12,
                )
            ],
            license_servers=[
                LicenseServerSchema(id=1, config_id=1, host="licserv0001", port=1234),
                LicenseServerSchema(id=3, config_id=1, host="licserv0003", port=8760),
            ],
            grace_time=60,
            type=LicenseServerType.FLEXLM,
        ),
        ConfigurationSchema(
            id=2,
            name="Converge",
            cluster_client_id="dummy",
            features=[
                FeatureSchema(
                    id=2,
                    name="converge_super",
                    product=ProductSchema(id=2, name="converge"),
                    config_id=2,
                    reserved=0,
                    total=500,
                    used=50,
                    booked_total=50,
                )
            ],
            license_servers=[
                LicenseServerSchema(id=2, config_id=2, host="licserv0002", port=2345),
            ],
            grace_time=123,
            type=LicenseServerType.RLM,
        ),
    ]

    configs = await get_cluster_configs_from_backend()
    assert configs == expected_configs


@pytest.mark.asyncio
@mock.patch("lm_agent.backend_utils.utils.get_cluster_configs_from_backend")
async def test__get_cluster_grace_times(get_cluster_configs_mock, parsed_configurations):
    """Test that get_cluster_grace_times generates a dict with the grace time for each feature_id."""
    get_cluster_configs_mock.return_value = parsed_configurations
    expected_grace_times = {1: 60, 2: 123}

    grace_times = await get_cluster_grace_times()
    assert grace_times == expected_grace_times


@pytest.mark.asyncio
@mock.patch("lm_agent.backend_utils.utils.get_all_features_from_backend")
async def test__get_all_features_bookings_sum(get_all_features_mock, parsed_features):
    """
    Test that get_bookings_sum_per_cluster returns the booking sum per cluster for a given product_feature.
    """
    get_all_features_mock.return_value = parsed_features
    bookings_sum = await get_all_features_bookings_sum()
    assert bookings_sum["abaqus.abaqus"] == 62


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
async def test__make_feature_update__success(respx_mock):
    """
    Test that make_feature_update updates the features correctly.
    """
    features_to_update = [
        {
            "product_name": "abaqus",
            "feature_name": "abaqus",
            "total": 500,
            "used": 50,
        },
        {
            "product_name": "converge",
            "feature_name": "converge_super",
            "total": 100,
            "used": 10,
        },
    ]

    respx_mock.put("/lm/features/bulk").mock(return_value=Response(status_code=200))

    try:
        await make_feature_update(features_to_update)
    except Exception as e:
        assert False, f"Exception was raised: {e}"


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
async def test__make_feature_update__raises_exception_on_non_two_hundred(respx_mock):
    """
    Test that make_feature_update handles a failed feature update correctly.
    """
    features_to_update = [
        {
            "product_name": "abaqus",
            "feature_name": "abaqus",
            "total": 500,
            "used": 50,
        },
        {
            "product_name": "converge",
            "feature_name": "converge_super",
            "total": 100,
            "used": 10,
        },
    ]

    respx_mock.put("/lm/features/bulk").mock(return_value=Response(status_code=500))

    with pytest.raises(LicenseManagerBackendConnectionError):
        await make_feature_update(features_to_update)


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
async def test__make_booking_request__success(respx_mock):
    """
    Test that make_booking_request successfully creates a job and its bookings on the backend.
    """
    lbr = LicenseBookingRequest(
        slurm_job_id="12345",
        username="test_user",
        lead_host="test_host",
        bookings=[
            LicenseBooking(product_feature="abaqus.abaqus", quantity=5),
            LicenseBooking(product_feature="converge.converge_super", quantity=10),
        ],
    )

    respx_mock.post("/lm/jobs").mock(
        return_value=Response(
            status_code=201,
            json={"id": 1},
        )
    )

    result = await make_booking_request(lbr)
    assert result is True


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
async def test__make_booking_request_job__returns_false_on_booking_failure(respx_mock):
    """
    Test that make_booking_request handles the failure case when booking creation fails.
    """
    lbr = LicenseBookingRequest(
        slurm_job_id="12345",
        username="test_user",
        lead_host="test_host",
        bookings=[
            LicenseBooking(product_feature="abaqus.abaqus", quantity=5),
        ],
    )

    respx_mock.post("/lm/jobs").mock(
        return_value=Response(
            status_code=409,
            json={"message": "Not enough licenses"},
        )
    )

    assert not await make_booking_request(lbr)


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
async def test__remove_job_by_slurm_job_id__success(respx_mock):
    """
    Test that remove_job_by_slurm_job_id successfully removes the job in the cluster.
    """
    slurm_job_id = "12345"

    respx_mock.delete(f"/lm/jobs/slurm_job_id/{slurm_job_id}").mock(
        return_value=Response(
            status_code=200,
            json={"message": "Job removed successfully"},
        )
    )

    try:
        await remove_job_by_slurm_job_id(slurm_job_id)
    except Exception as e:
        assert False, f"Exception was raised: {e}"


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
async def test__remove_job_by_slurm_job_id__raises_exception_on_non_two_hundred(respx_mock):
    """
    Test that remove_job_by_slurm_job_id raises an exception when the job removal fails.
    """
    slurm_job_id = "12345"

    respx_mock.delete(f"/lm/jobs/slurm_job_id/{slurm_job_id}").mock(
        return_value=Response(
            status_code=500,
            json={"error": "Internal Server Error"},
        )
    )

    with pytest.raises(LicenseManagerBackendConnectionError):
        await remove_job_by_slurm_job_id(slurm_job_id)


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
async def test__get_bookings_for_all_jobs__success(jobs, respx_mock):
    """
    Test that get_bookings_for_all_jobs returns the a dict with the
    slurm_job_id as key and the bookings as value.
    """
    respx_mock.get("/lm/jobs/by_client_id").mock(return_value=Response(status_code=200, json=jobs))

    all_bookings = await get_bookings_for_all_jobs()

    assert all_bookings == {
        "123": [
            BookingSchema(id=1, job_id=1, feature_id=1, quantity=12),
            BookingSchema(id=2, job_id=1, feature_id=2, quantity=50),
        ],
        "456": [
            BookingSchema(id=3, job_id=2, feature_id=4, quantity=15),
            BookingSchema(id=4, job_id=2, feature_id=7, quantity=25),
        ],
        "789": [
            BookingSchema(id=14, job_id=6, feature_id=4, quantity=5),
            BookingSchema(id=15, job_id=6, feature_id=7, quantity=17),
        ],
    }
