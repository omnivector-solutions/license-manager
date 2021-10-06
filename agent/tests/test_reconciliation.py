from unittest import mock

import pytest
from fastapi import HTTPException, status
from httpx import Response

from lm_agent.reconciliation import (
    clean_booked_grace_time,
    clean_bookings,
    get_all_grace_times,
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
    respx_mock.get("/api/v1/config/all").mock(
        return_value=Response(
            status_code=status.HTTP_200_OK,
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
    with pytest.raises(HTTPException):
        await update_report()


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
@mock.patch("lm_agent.reconciliation.report")
@mock.patch("lm_agent.reconciliation.clean_booked_grace_time")
async def test_reconcile(clean_booked_grace_time_mock, report_mock, respx_mock):
    """
    Check if reconcile does a patch to /license/reconcile and await for clean_booked_grace_time.
    """
    respx_mock.patch("/api/v1/license/reconcile").mock(
        return_value=Response(
            status_code=status.HTTP_200_OK,
        )
    )
    respx_mock.get("/api/v1/license/cluster_update").mock(
        return_value=Response(
            status_code=status.HTTP_200_OK,
            json=[
                {
                    "product_feature": "product.feature",
                    "bookings_sum": 100,
                    "license_total": 1000,
                    "license_used": 200,
                },
            ],
        )
    )
    report_mock.return_value = [{"foo": "bar"}]
    await reconcile()
    clean_booked_grace_time_mock.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
@mock.patch("lm_agent.reconciliation.report")
@mock.patch("lm_agent.reconciliation.clean_booked_grace_time")
async def test_reconcile_patch_failed(clean_booked_grace_time_mock, report_mock, respx_mock):
    """
    Check that when patch to /license/reconcile response status_code is not 200, should raise exception.
    """
    respx_mock.patch("/api/v1/license/reconcile").mock(
        return_value=Response(
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    )
    report_mock.return_value = [{"foo": "bar"}]
    with pytest.raises(HTTPException):
        await reconcile()
        clean_booked_grace_time_mock.assert_awaited_once()


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
