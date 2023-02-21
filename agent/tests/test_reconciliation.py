from unittest import mock

import pytest
from httpx import Response
from pytest import mark, raises

from lm_agent.exceptions import (
    LicenseManagerBackendConnectionError,
    LicenseManagerEmptyReportError,
    LicenseManagerFeatureConfigurationIncorrect,
)
from lm_agent.reconciliation import (
    clean_booked_grace_time,
    clean_bookings,
    filter_cluster_update_licenses,
    get_all_grace_times,
    get_bookings_sum_per_cluster,
    get_greatest_grace_time,
    reconcile,
    update_report,
)


@pytest.fixture
def booking_rows_json():
    return [
        {
            "job_id": "1",
            "config_id": 1,
        },
        {
            "job_id": "2",
            "config_id": 2,
        },
        {
            "job_id": "1",
            "config_id": 2,
        },
        {
            "job_id": "1",
            "config_id": 3,
        },
    ]


def test_get_greatest_grace_time(booking_rows_json):
    """
    Test if the function really returns the greatest value for the grace_time.
    """
    grace_times = {
        1: 100,
        2: 20,
        3: 400,
    }
    greatest_grace_time = get_greatest_grace_time("1", grace_times, [booking_rows_json])
    assert greatest_grace_time == 400
    greatest_grace_time = get_greatest_grace_time("2", grace_times, [booking_rows_json])
    assert greatest_grace_time == 20


@pytest.mark.asyncio
@mock.patch("lm_agent.reconciliation.return_formatted_squeue_out")
@mock.patch("lm_agent.reconciliation.get_all_grace_times")
@mock.patch("lm_agent.reconciliation.get_booked_for_job_id")
@mock.patch("lm_agent.reconciliation.remove_booked_for_job_id")
async def test_clean_booked_grace_time(
    remove_booked_for_job_id_mock,
    get_booked_for_job_id_mock,
    get_all_grace_times_mock,
    return_formatted_squeue_out_mock,
    booking_rows_json,
):
    """
    Test for when the running time is greater than the grace_time, then delete the booking.
    """
    get_booked_for_job_id_mock.return_value = booking_rows_json
    return_formatted_squeue_out_mock.return_value = "1|5:00|RUNNING"
    get_all_grace_times_mock.return_value = {1: 100, 2: 30, 3: 10}
    await clean_booked_grace_time()
    remove_booked_for_job_id_mock.assert_awaited_once_with(1)
    get_all_grace_times_mock.assert_awaited_once()


@pytest.mark.asyncio
@mock.patch("lm_agent.reconciliation.return_formatted_squeue_out")
@mock.patch("lm_agent.reconciliation.get_all_grace_times")
@mock.patch("lm_agent.reconciliation.get_booked_for_job_id")
@mock.patch("lm_agent.reconciliation.remove_booked_for_job_id")
async def test_clean_booked_grace_time_dont_delete(
    remove_booked_for_job_id_mock,
    get_booked_for_job_id_mock,
    get_all_grace_times_mock,
    return_formatted_squeue_out_mock,
    booking_rows_json,
):
    """
    Test for when the running time is smaller than the grace_time, then don't delete the booking.
    """
    get_booked_for_job_id_mock.return_value = booking_rows_json
    return_formatted_squeue_out_mock.return_value = "1|5:00|RUNNING"
    get_all_grace_times_mock.return_value = {1: 1000, 2: 3000, 3: 1000}
    await clean_booked_grace_time()
    remove_booked_for_job_id_mock.assert_not_awaited()
    get_all_grace_times_mock.assert_awaited_once()


@pytest.mark.asyncio
@mock.patch("lm_agent.reconciliation.return_formatted_squeue_out")
@mock.patch("lm_agent.reconciliation.get_all_grace_times")
@mock.patch("lm_agent.reconciliation.get_booked_for_job_id")
@mock.patch("lm_agent.reconciliation.remove_booked_for_job_id")
async def test_clean_booked_grace_time_dont_delete_if_grace_time_invalid(
    remove_booked_for_job_id_mock,
    get_booked_for_job_id_mock,
    get_all_grace_times_mock,
    return_formatted_squeue_out_mock,
):
    """
    Test for when the remove_booked_for_job_id raises an exception.
    """
    get_booked_for_job_id_mock.return_value = []
    return_formatted_squeue_out_mock.return_value = "1|5:00|RUNNING"
    get_all_grace_times_mock.return_value = {1: 100, 2: 100, 3: 100}
    await clean_booked_grace_time()
    remove_booked_for_job_id_mock.assert_not_awaited()
    get_all_grace_times_mock.assert_awaited_once()


@pytest.mark.asyncio
@mock.patch("lm_agent.reconciliation.return_formatted_squeue_out")
@mock.patch("lm_agent.reconciliation.get_all_grace_times")
@mock.patch("lm_agent.reconciliation.get_booked_for_job_id")
@mock.patch("lm_agent.reconciliation.remove_booked_for_job_id")
async def test_clean_booked_grace_time_dont_delete_if_no_jobs(
    remove_booked_for_job_id_mock,
    get_booked_for_job_id_mock,
    get_all_grace_times_mock,
    return_formatted_squeue_out_mock,
    booking_rows_json,
):
    """
    Test for when there are no jobs running, don't delete.
    """
    get_booked_for_job_id_mock.return_value = booking_rows_json
    return_formatted_squeue_out_mock.return_value = ""
    get_all_grace_times_mock.return_value = {1: 10, 2: 10}
    await clean_booked_grace_time()
    remove_booked_for_job_id_mock.assert_not_awaited()
    get_all_grace_times_mock.assert_not_awaited()


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


@pytest.mark.asyncio
@mock.patch("lm_agent.reconciliation.report")
async def test_reconcile_report_empty(report_mock: mock.AsyncMock):
    """
    Check the correct behavior when the report is empty in reconcile.
    """
    report_mock.return_value = []
    with pytest.raises(LicenseManagerEmptyReportError):
        await update_report()


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
@mock.patch("lm_agent.reconciliation.create_or_update_reservation")
@mock.patch("lm_agent.reconciliation.get_tokens_for_license")
@mock.patch("lm_agent.reconciliation.get_config_id_from_backend")
@mock.patch("lm_agent.reconciliation.get_bookings_sum_per_cluster")
@mock.patch("lm_agent.reconciliation.get_cluster_name")
@mock.patch("lm_agent.reconciliation.filter_cluster_update_licenses")
@mock.patch("lm_agent.reconciliation.update_report")
@mock.patch("lm_agent.reconciliation.clean_booked_grace_time")
async def test_reconcile(
    clean_booked_grace_time_mock,
    update_report_mock,
    filter_licenses_mock,
    get_cluster_name_mock,
    get_bookings_sum_mock,
    get_config_id_mock,
    get_tokens_mock,
    create_or_update_reservation_mock,
    respx_mock,
    cluster_update_payload,
    configuration_row,
):
    """
    Check if reconcile updates the reservation with the correct value.
    The reservation should block all licenses that are in use.

    License: product.feature@flexlm
    Total: 1000

    Cluster: cluster1
    Used in cluster: 23

    Overview of the license:
    ________________________________________________________________________________
    |    200   |    15     |     17    |    71    |     100     ||       597       |
    |   used   |   booked  |   booked  |  booked  |    limit    ||      free       |
    | Lic serv | cluster 1 | cluster 2 | cluster3 | not to use  ||     to use      |
    --------------------------------------------------------------------------------

    Since we have 303 licenses in use (booked or license server) and 100 that should
    not be used (past the limit), the amount of licenses available is 597.

    This way, we need to block the remaing 403 licenses. But considering that Slurm
    is already "blocking" 23 licenses that are in use in the cluster, the reservation
    should block 380 licenses.
    """
    respx_mock.get("/lm/api/v1/license/cluster_update").mock(
        return_value=Response(
            status_code=200,
            json=cluster_update_payload,
        )
    )
    filter_licenses_mock.return_value = cluster_update_payload
    get_cluster_name_mock.return_value = "cluster1"
    get_bookings_sum_mock.return_value = {
        "cluster1": 15,
        "cluster2": 17,
        "cluster3": 71,
    }
    get_config_id_mock.return_value = 1
    respx_mock.get("/lm/api/v1/config/1").mock(
        return_value=Response(
            status_code=200,
            json=configuration_row,
        )
    )
    get_tokens_mock.return_value = 23

    await reconcile()
    create_or_update_reservation_mock.assert_called_with("product.feature@flexlm:380")


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
@mock.patch("lm_agent.reconciliation.get_config_id_from_backend")
@mock.patch("lm_agent.reconciliation.get_bookings_sum_per_cluster")
@mock.patch("lm_agent.reconciliation.get_cluster_name")
@mock.patch("lm_agent.reconciliation.filter_cluster_update_licenses")
@mock.patch("lm_agent.reconciliation.update_report")
@mock.patch("lm_agent.reconciliation.clean_booked_grace_time")
async def test_reconcile__raise_exception_incorrect_feature(
    clean_booked_grace_time_mock,
    update_report_mock,
    filter_licenses_mock,
    get_cluster_name_mock,
    get_bookings_sum_mock,
    get_config_id_mock,
    respx_mock,
    invalid_configuration_format,
    cluster_update_payload,
):
    """
    Test that an exception is raised if the features doesn't have the total.
    """
    respx_mock.get("/lm/api/v1/license/cluster_update").mock(
        return_value=Response(
            status_code=200,
            json=cluster_update_payload,
        )
    )

    filter_licenses_mock.return_value = cluster_update_payload

    get_cluster_name_mock.return_value = "cluster1"
    get_bookings_sum_mock.return_value = {
        "cluster1": 15,
        "cluster2": 17,
        "cluster3": 71,
    }

    get_config_id_mock.return_value = 1
    respx_mock.get("/lm/api/v1/config/1").mock(
        return_value=Response(
            status_code=200,
            json=invalid_configuration_format,
        )
    )

    with raises(LicenseManagerFeatureConfigurationIncorrect):
        await reconcile()


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
@mock.patch("lm_agent.reconciliation.create_or_update_reservation")
@mock.patch("lm_agent.reconciliation.get_tokens_for_license")
@mock.patch("lm_agent.reconciliation.get_config_id_from_backend")
@mock.patch("lm_agent.reconciliation.get_bookings_sum_per_cluster")
@mock.patch("lm_agent.reconciliation.get_cluster_name")
@mock.patch("lm_agent.reconciliation.filter_cluster_update_licenses")
@mock.patch("lm_agent.reconciliation.update_report")
@mock.patch("lm_agent.reconciliation.clean_booked_grace_time")
async def test_reconcile__parse_old_feature_format(
    clean_booked_grace_time_mock,
    update_report_mock,
    filter_licenses_mock,
    get_cluster_name_mock,
    get_bookings_sum_mock,
    get_config_id_mock,
    get_tokens_mock,
    create_or_update_reservation_mock,
    respx_mock,
    cluster_update_payload,
    old_configuration_format,
):
    """
    Test that the reconcile can parse a feature with the old format (without the dict with total/limit).
    """
    respx_mock.get("/lm/api/v1/license/cluster_update").mock(
        return_value=Response(
            status_code=200,
            json=cluster_update_payload,
        )
    )

    filter_licenses_mock.return_value = cluster_update_payload

    get_cluster_name_mock.return_value = "cluster1"
    get_bookings_sum_mock.return_value = {
        "cluster1": 15,
        "cluster2": 17,
        "cluster3": 71,
    }

    get_config_id_mock.return_value = 1
    respx_mock.get("/lm/api/v1/config/1").mock(
        return_value=Response(
            status_code=200,
            json=old_configuration_format,
        )
    )
    get_tokens_mock.return_value = 23

    await reconcile()


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
@mock.patch("lm_agent.reconciliation.report")
@mock.patch("lm_agent.reconciliation.clean_booked_grace_time")
async def test_update_report__patch_failed(clean_booked_grace_time_mock, report_mock, respx_mock):
    """
    Check that when patch to /license/reconcile response status_code is not 200, should raise exception.
    """
    respx_mock.patch("/lm/api/v1/license/reconcile").mock(
        return_value=Response(
            status_code=400,
        )
    )
    report_mock.return_value = [{"foo": "bar"}]
    with pytest.raises(LicenseManagerBackendConnectionError):
        await update_report()


@pytest.mark.asyncio
@mock.patch("lm_agent.reconciliation.get_bookings_from_backend")
@mock.patch("lm_agent.reconciliation.remove_booked_for_job_id")
async def test_clean_bookings(remove_booked_for_job_id_mock, get_bookings_from_backend_mock):
    squeue_parsed = [
        {"job_id": 1, "state": "RUNNING"},
        {"job_id": 2, "state": "PENDING"},
        {"job_id": 3, "state": "PENDING"},
    ]
    booking_mock_2 = mock.Mock()
    booking_mock_2.job_id = 2
    booking_mock_3 = mock.Mock()
    booking_mock_3.job_id = 3
    get_bookings_from_backend_mock.return_value = [booking_mock_2, booking_mock_3]
    await clean_bookings(squeue_parsed, "test_cluster_name")

    remove_booked_for_job_id_mock.call_count == 2


@pytest.mark.asyncio
@mock.patch("lm_agent.reconciliation.get_bookings_from_backend")
@mock.patch("lm_agent.reconciliation.remove_booked_for_job_id")
async def test_clean_bookings_not_in_squeue(remove_booked_for_job_id_mock, get_bookings_from_backend_mock):
    squeue_parsed = [{"job_id": 1, "state": "RUNNING"}]
    booking_mock_1 = mock.Mock()
    booking_mock_1.job_id = 1
    booking_mock_2 = mock.Mock()
    booking_mock_2.job_id = 2
    get_bookings_from_backend_mock.return_value = [booking_mock_1, booking_mock_2]
    await clean_bookings(squeue_parsed, "test_cluster_name")

    remove_booked_for_job_id_mock.call_count == 1


@mark.asyncio
@mock.patch("lm_agent.reconciliation.get_all_product_features_from_cluster")
async def test_filter_cluster_update_licenses(get_product_feature_from_cluster_mock: mock.MagicMock):
    licenses_to_update = [
        {
            "product_feature": "product1.feature1",
            "bookings_sum": 0,
            "license_total": 100,
            "license_used": 50,
        },
        {
            "product_feature": "product2.feature2",
            "bookings_sum": 0,
            "license_total": 200,
            "license_used": 120,
        },
        {
            "product_feature": "product3.feature3",
            "bookings_sum": 0,
            "license_total": 30,
            "license_used": 10,
        },
    ]

    get_product_feature_from_cluster_mock.return_value = ["product1.feature1", "product3.feature3"]

    assert await filter_cluster_update_licenses(licenses_to_update) == [
        {
            "product_feature": "product1.feature1",
            "bookings_sum": 0,
            "license_total": 100,
            "license_used": 50,
        },
        {
            "product_feature": "product3.feature3",
            "bookings_sum": 0,
            "license_total": 30,
            "license_used": 10,
        },
    ]


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
