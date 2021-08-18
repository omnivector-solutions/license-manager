from unittest import mock

import pytest
from httpx import Response

from lm_agent.reconciliation import (
    clean_booked_grace_time,
    get_all_grace_times,
    get_booked_for_job_id,
    get_greatest_grace_time,
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
@pytest.mark.respx(base_url="https://foo.bar")
async def test_get_all_grace_times(respx_mock):
    """
    Check the return value for the get_all_grace_times.
    """
    respx_mock.get("/api/v1/config/all").mock(
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
