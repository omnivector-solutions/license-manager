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
    InventorySchema,
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
    get_all_clusters_from_backend,
    get_bookings_for_job_id,
    get_bookings_sum_per_cluster,
    get_cluster_from_backend,
    get_configs_from_backend,
    get_feature_ids,
    get_grace_times,
    get_jobs_from_backend,
    make_booking_request,
    make_inventory_update,
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
async def test__get_jobs_from_backend(clusters, respx_mock):
    """Test that get_jobs_from_backend parses and returns the jobs from the cluster."""
    respx_mock.get("/lm/clusters/by_client_id").mock(
        return_value=Response(
            status_code=200,
            json=clusters[0],
        )
    )

    expected_jobs = [
        JobSchema(
            id=1,
            slurm_job_id="123",
            cluster_id=1,
            username="string",
            lead_host="string",
            bookings=[
                BookingSchema(id=1, job_id=1, feature_id=1, quantity=12),
                BookingSchema(id=2, job_id=1, feature_id=2, quantity=50),
            ],
        )
    ]

    jobs = await get_jobs_from_backend()
    assert jobs == expected_jobs


@mark.asyncio
@pytest.mark.respx(base_url="http://backend")
async def test__get_configs_from_backend(clusters, respx_mock):
    """Test that get_configs_from_backend parses and returns the configurations from the cluster."""
    respx_mock.get("/lm/clusters/by_client_id").mock(
        return_value=Response(
            status_code=200,
            json=clusters[0],
        )
    )

    expected_configs = [
        ConfigurationSchema(
            id=1,
            name="Abaqus",
            cluster_id=1,
            features=[
                FeatureSchema(
                    id=1,
                    name="abaqus",
                    product=ProductSchema(id=1, name="abaqus"),
                    config_id=1,
                    reserved=100,
                    inventory=InventorySchema(id=1, feature_id=2, total=123, used=12),
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
            cluster_id=1,
            features=[
                FeatureSchema(
                    id=2,
                    name="converge_super",
                    product=ProductSchema(id=2, name="converge"),
                    config_id=2,
                    reserved=0,
                    inventory=InventorySchema(id=2, feature_id=2, total=500, used=50),
                )
            ],
            license_servers=[
                LicenseServerSchema(id=2, config_id=2, host="licserv0002", port=2345),
            ],
            grace_time=123,
            type=LicenseServerType.RLM,
        ),
    ]

    configs = await get_configs_from_backend()
    assert configs == expected_configs


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
async def test__get_all_clusters_from_backend(clusters, parsed_clusters, respx_mock):
    """Test that get_all_clusters_from_backend parses and returns the clusters from the cluster."""
    respx_mock.get("/lm/clusters").mock(
        return_value=Response(
            status_code=200,
            json=clusters,
        )
    )

    expected_clusters = parsed_clusters
    clusters = await get_all_clusters_from_backend()
    assert clusters == expected_clusters


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
async def test__get_all_clusters_from_backend__failure_backend_connection(respx_mock):
    """
    Test that get_all_clusters_from_backend handles failure to connect to the backend.
    """
    respx_mock.get("/lm/clusters").mock(
        return_value=Response(
            status_code=500,
            json={"error": "Internal Server Error"},
        )
    )

    with pytest.raises(LicenseManagerBackendConnectionError):
        await get_all_clusters_from_backend()


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
async def test__get_all_clusters_from_backend__failure_parse_error(respx_mock):
    """
    Test that get_all_clusters_from_backend handles failure to parse the cluster data from the backend.
    """
    respx_mock.get("/lm/clusters").mock(
        return_value=Response(
            status_code=200,
            json={"bla": "bla"},
        )
    )

    with pytest.raises(LicenseManagerParseError):
        await get_all_clusters_from_backend()


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
async def test__get_cluster_from_backend(clusters, parsed_clusters, respx_mock):
    """Test that get_cluster_from_backend parses and returns the cluster from the cluster."""
    respx_mock.get("/lm/clusters/by_client_id").mock(
        return_value=Response(
            status_code=200,
            json=clusters[0],
        )
    )

    expected_clusters = parsed_clusters[0]
    clusters = await get_cluster_from_backend()
    assert clusters == expected_clusters


@pytest.mark.parametrize(
    "cluster_data, index, expected_feature_ids",
    [
        (
            "parsed_clusters",
            0,
            {
                "abaqus.abaqus": 1,
                "converge.converge_super": 2,
            },
        ),
        (
            "parsed_clusters",
            1,
            {
                "Product 3.Feature 3": 4,
                "Product 4.Feature 4": 7,
            },
        ),
    ],
)
def test__get_feature_ids(cluster_data, index, expected_feature_ids, request):
    """Test that get_feature_ids generates a dict with the id for each feature."""
    cluster_data = request.getfixturevalue(cluster_data)
    feature_ids = get_feature_ids(cluster_data[index])
    assert feature_ids == expected_feature_ids


@pytest.mark.parametrize(
    "cluster_data, index, expected_grace_times",
    [
        (
            "parsed_clusters",
            0,
            {
                1: 60,
                2: 123,
            },
        ),
        (
            "parsed_clusters",
            1,
            {
                4: 60,
                7: 60,
            },
        ),
    ],
)
def test__get_grace_times(cluster_data, index, expected_grace_times, request):
    """Test that get_grace_times generates a dict with the grace time for each feature_id."""
    cluster_data = request.getfixturevalue(cluster_data)
    grace_times = get_grace_times(cluster_data[index])
    assert grace_times == expected_grace_times


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "product_feature, expected_booking_sum",
    [
        ("abaqus.abaqus", {1: 12}),
        ("converge.converge_super", {1: 50}),
        ("Product 3.Feature 3", {2: 15}),
        ("Product 4.Feature 4", {2: 25}),
    ],
)
async def test__get_bookings_sum_per_cluster(product_feature, expected_booking_sum, clusters, respx_mock):
    """
    Test that get_bookings_sum_per_cluster returns the booking sum per cluster for a given product_feature.
    """
    respx_mock.get("/lm/clusters").mock(
        return_value=Response(
            status_code=200,
            json=clusters,
        )
    )

    booking_sum = await get_bookings_sum_per_cluster(product_feature)
    assert booking_sum == expected_booking_sum


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
async def test__make_inventory_update__success(respx_mock):
    """
    Test that make_inventory_update updates the inventory for a feature correctly.
    """
    feature_id = 1
    total = 100
    used = 50

    respx_mock.put(f"/lm/features/{feature_id}/update_inventory").mock(return_value=Response(status_code=200))

    result = await make_inventory_update(feature_id, total, used)
    assert result is True


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
async def test__make_inventory_update__raises_exception_on_non_two_hundred(respx_mock):
    """
    Test that make_inventory_update handles a failed inventory update correctly.
    """
    feature_id = 1
    total = 100
    used = 50

    respx_mock.put(f"/lm/features/{feature_id}/update_inventory").mock(return_value=Response(status_code=500))

    with pytest.raises(LicenseManagerBackendConnectionError):
        await make_inventory_update(feature_id, total, used)


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
@mock.patch("lm_agent.backend_utils.utils.get_cluster_from_backend")
async def test__make_booking_request__success(mock_get_cluster, parsed_clusters, respx_mock):
    """
    Test that make_booking_request successfully creates a job and its bookings on the backend.
    """
    lbr = LicenseBookingRequest(
        slurm_job_id="12345",
        user_name="test_user",
        lead_host="test_host",
        bookings=[
            LicenseBooking(product_feature="abaqus.abaqus", quantity=5),
            LicenseBooking(product_feature="converge.converge_super", quantity=10),
        ],
    )

    mock_get_cluster.return_value = parsed_clusters[0]

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
@mock.patch("lm_agent.backend_utils.utils.get_cluster_from_backend")
async def test__make_booking_request_job__returns_false_on_booking_failure(
    mock_get_cluster, parsed_clusters, respx_mock
):
    """
    Test that make_booking_request handles the failure case when booking creation fails.
    """
    lbr = LicenseBookingRequest(
        slurm_job_id="12345",
        user_name="test_user",
        lead_host="test_host",
        bookings=[
            LicenseBooking(product_feature="abaqus.abaqus", quantity=5),
        ],
    )

    mock_get_cluster.return_value = parsed_clusters[0]

    respx_mock.post("/lm/jobs").mock(
        return_value=Response(
            status_code=409,
            json={"message": "Not enough licenses"},
        )
    )

    assert not await make_booking_request(lbr)


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
@mock.patch("lm_agent.backend_utils.utils.get_cluster_from_backend")
async def test__remove_job_by_slurm_job_id__success(mock_get_cluster, parsed_clusters, respx_mock):
    """
    Test that remove_job_by_slurm_job_id successfully removes the job in the cluster.
    """
    slurm_job_id = "12345"

    mock_get_cluster.return_value = parsed_clusters[0]

    respx_mock.delete(f"/lm/jobs/slurm_job_id/{slurm_job_id}/cluster_id/{parsed_clusters[0].id}").mock(
        return_value=Response(
            status_code=200,
            json={"message": "Job removed successfully"},
        )
    )

    result = await remove_job_by_slurm_job_id(slurm_job_id)
    assert result is True


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
@mock.patch("lm_agent.backend_utils.utils.get_cluster_from_backend")
async def test__remove_job_by_slurm_job_id__raises_exception_on_non_two_hundred(
    mock_get_cluster, parsed_clusters, respx_mock
):
    """
    Test that remove_job_by_slurm_job_id raises an exception when the job removal fails.
    """
    slurm_job_id = "12345"

    mock_get_cluster.return_value = parsed_clusters[0]

    respx_mock.delete(f"/lm/jobs/slurm_job_id/{slurm_job_id}/cluster_id/{parsed_clusters[0].id}").mock(
        return_value=Response(
            status_code=500,
            json={"error": "Internal Server Error"},
        )
    )

    with pytest.raises(LicenseManagerBackendConnectionError):
        await remove_job_by_slurm_job_id(slurm_job_id)


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
@mock.patch("lm_agent.backend_utils.utils.get_cluster_from_backend")
async def test__get_bookings_for_job_id__success(mock_get_cluster, clusters, parsed_clusters, respx_mock):
    """
    Test that get_bookings_for_job_id returns the bookings for a given job ID.
    """
    slurm_job_id = "12345"

    mock_get_cluster.return_value = parsed_clusters[0]

    bookings_data = clusters[0]["jobs"][0]["bookings"]

    respx_mock.get(f"/lm/jobs/by_slurm_id/{slurm_job_id}/cluster/{parsed_clusters[0].id}").mock(
        return_value=Response(
            status_code=200,
            json={"bookings": bookings_data},
        )
    )

    bookings = await get_bookings_for_job_id(slurm_job_id)
    assert bookings == bookings_data


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
@mock.patch("lm_agent.backend_utils.utils.get_cluster_from_backend")
async def test__get_bookings_for_job_id__raises_exception_on_non_two_hundred(
    mock_get_cluster, parsed_clusters, respx_mock
):
    """
    Test that get_bookings_for_job_id handles failure to retrieve bookings for a given job ID.
    """
    slurm_job_id = "12345"

    mock_get_cluster.return_value = parsed_clusters[0]

    respx_mock.get(f"/lm/jobs/by_slurm_id/{slurm_job_id}/cluster/{parsed_clusters[0].id}").mock(
        return_value=Response(
            status_code=404,
            json={"error": "Job not found"},
        )
    )

    with pytest.raises(LicenseManagerBackendConnectionError):
        await get_bookings_for_job_id(slurm_job_id)
