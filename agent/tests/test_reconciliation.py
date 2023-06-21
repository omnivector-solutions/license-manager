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
    clean_jobs,
    clean_jobs_by_grace_time,
    create_or_update_reservation,
    get_bookings_sum_per_cluster,
    get_greatest_grace_time_for_job,
    reconcile,
    update_inventories,
)


def test__get_greatest_grace_time_for_job(parsed_clusters):
    """
    Test if the function really returns the greatest value for the grace_time.
    """
    grace_times = {
        1: 10,
        2: 20,
    }

    job_bookings = parsed_clusters[0].jobs[0].bookings

    expected_result = 20

    result = get_greatest_grace_time_for_job(grace_times, job_bookings)
    assert result == expected_result


@pytest.mark.asyncio
@mock.patch("lm_agent.reconciliation.return_formatted_squeue_out")
@mock.patch("lm_agent.reconciliation.get_grace_times")
@mock.patch("lm_agent.reconciliation.get_bookings_for_job_id")
@mock.patch("lm_agent.reconciliation.remove_job_by_slurm_job_id")
@mock.patch("lm_agent.reconciliation.get_jobs_from_backend")
@mock.patch("lm_agent.reconciliation.clean_jobs")
async def test__clean_jobs_by_grace_time__on_delete(
    clean_jobs_mock,
    get_jobs_from_backend_mock,
    remove_job_by_slurm_job_id_mock,
    get_bookings_for_job_id_mock,
    get_grace_times_mock,
    return_formatted_squeue_out_mock,
    parsed_clusters,
):
    """
    Test for cleaning jobs when running time is greater than grace_time.
    """
    slurm_job_id = 1
    formatted_squeue_out = "1|5:00|RUNNING"
    grace_times = {1: 10, 2: 20}
    job_bookings = parsed_clusters[0].jobs[0].bookings

    get_jobs_from_backend_mock.return_value = parsed_clusters[0].jobs
    get_bookings_for_job_id_mock.return_value = job_bookings
    remove_job_by_slurm_job_id_mock.return_value = True
    return_formatted_squeue_out_mock.return_value = formatted_squeue_out
    get_grace_times_mock.return_value = grace_times

    await clean_jobs_by_grace_time(parsed_clusters[0])

    remove_job_by_slurm_job_id_mock.assert_awaited_once_with(slurm_job_id)
    get_bookings_for_job_id_mock.assert_awaited_once_with(slurm_job_id)
    get_grace_times_mock.assert_called_once_with(parsed_clusters[0])


@pytest.mark.asyncio
@mock.patch("lm_agent.reconciliation.return_formatted_squeue_out")
@mock.patch("lm_agent.reconciliation.get_grace_times")
@mock.patch("lm_agent.reconciliation.get_bookings_for_job_id")
@mock.patch("lm_agent.reconciliation.remove_job_by_slurm_job_id")
@mock.patch("lm_agent.reconciliation.get_jobs_from_backend")
@mock.patch("lm_agent.reconciliation.clean_jobs")
async def test__clean_jobs_by_grace_time__dont_delete(
    clean_jobs_mock,
    get_jobs_from_backend_mock,
    remove_job_by_slurm_job_id_mock,
    get_bookings_for_job_id_mock,
    get_grace_times_mock,
    return_formatted_squeue_out_mock,
    parsed_clusters,
):
    """
    Test for when the running time is smaller than the grace_time, then don't delete the booking.
    """
    slurm_job_id = 1
    formatted_squeue_out = "1|5:00|RUNNING"
    grace_times = {1: 1000, 2: 3000}
    job_bookings = parsed_clusters[0].jobs[0].bookings

    get_jobs_from_backend_mock.return_value = parsed_clusters[0].jobs
    get_bookings_for_job_id_mock.return_value = job_bookings
    return_formatted_squeue_out_mock.return_value = formatted_squeue_out
    get_grace_times_mock.return_value = grace_times

    await clean_jobs_by_grace_time(parsed_clusters[0])

    remove_job_by_slurm_job_id_mock.assert_not_awaited()
    get_bookings_for_job_id_mock.assert_awaited_once_with(slurm_job_id)
    get_grace_times_mock.assert_called_once_with(parsed_clusters[0])


@pytest.mark.asyncio
@mock.patch("lm_agent.reconciliation.return_formatted_squeue_out")
@mock.patch("lm_agent.reconciliation.get_grace_times")
@mock.patch("lm_agent.reconciliation.get_bookings_for_job_id")
@mock.patch("lm_agent.reconciliation.remove_job_by_slurm_job_id")
@mock.patch("lm_agent.reconciliation.get_jobs_from_backend")
@mock.patch("lm_agent.reconciliation.clean_jobs")
async def test__clean_jobs_by_grace_time__dont_delete_if_grace_time_invalid(
    clean_jobs_mock,
    get_jobs_from_backend_mock,
    remove_job_by_slurm_job_id_mock,
    get_bookings_for_job_id_mock,
    get_grace_times_mock,
    return_formatted_squeue_out_mock,
    parsed_clusters,
):
    """
    Test for when the grace_time is invalid because there aren't bookings in the job.
    """
    slurm_job_id = 1
    formatted_squeue_out = "1|5:00|RUNNING"
    grace_times = {1: 10, 2: 20}

    get_jobs_from_backend_mock.return_value = parsed_clusters[0].jobs
    get_bookings_for_job_id_mock.return_value = []
    return_formatted_squeue_out_mock.return_value = formatted_squeue_out
    get_grace_times_mock.return_value = grace_times

    await clean_jobs_by_grace_time(parsed_clusters[0])

    remove_job_by_slurm_job_id_mock.assert_not_awaited()
    get_bookings_for_job_id_mock.assert_awaited_once_with(slurm_job_id)
    get_grace_times_mock.assert_called_once_with(parsed_clusters[0])


@pytest.mark.asyncio
@mock.patch("lm_agent.reconciliation.return_formatted_squeue_out")
@mock.patch("lm_agent.reconciliation.get_grace_times")
@mock.patch("lm_agent.reconciliation.get_bookings_for_job_id")
@mock.patch("lm_agent.reconciliation.remove_job_by_slurm_job_id")
@mock.patch("lm_agent.reconciliation.get_jobs_from_backend")
@mock.patch("lm_agent.reconciliation.clean_jobs")
async def test__clean_jobs_by_grace_time__dont_delete_if_no_jobs(
    clean_jobs_mock,
    get_jobs_from_backend_mock,
    remove_job_by_slurm_job_id_mock,
    get_bookings_for_job_id_mock,
    get_grace_times_mock,
    return_formatted_squeue_out_mock,
    parsed_clusters,
):
    """
    Test for when there are no jobs running, don't delete.
    """
    formatted_squeue_out = ""
    grace_times = {1: 10, 2: 20}

    get_jobs_from_backend_mock.return_value = parsed_clusters[0].jobs
    get_bookings_for_job_id_mock.return_value = []
    return_formatted_squeue_out_mock.return_value = formatted_squeue_out
    get_grace_times_mock.return_value = grace_times

    await clean_jobs_by_grace_time(parsed_clusters[0])

    remove_job_by_slurm_job_id_mock.assert_not_awaited()
    get_bookings_for_job_id_mock.assert_not_awaited()
    get_grace_times_mock.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
@mock.patch("lm_agent.reconciliation.create_or_update_reservation")
@mock.patch("lm_agent.reconciliation.get_tokens_for_license")
@mock.patch("lm_agent.reconciliation.get_configs_from_backend")
@mock.patch("lm_agent.reconciliation.get_bookings_sum_per_cluster")
@mock.patch("lm_agent.reconciliation.get_cluster_from_backend")
@mock.patch("lm_agent.reconciliation.update_inventories")
@mock.patch("lm_agent.reconciliation.clean_jobs_by_grace_time")
async def test__reconcile__success(
    clean_jobs_by_grace_time_mock,
    update_inventories_mock,
    get_cluster_from_backend_mock,
    get_bookings_sum_mock,
    get_configs_from_backend_mock,
    get_tokens_mock,
    create_or_update_reservation_mock,
    respx_mock,
    parsed_clusters,
):
    """
    Check if reconcile updates the reservation with the correct value.
    The reservation should block all licenses that are in use.

    License: abaqus.abaqus@flexlm
    Total: 1000

    Cluster: cluster1
    Used in cluster: 23

    Overview of the license:
    ________________________________________________________________________________
    |    200   |    15     |     17    |    71    |     100     ||       597       |
    |   used   |   booked  |   booked  |  booked  |   reserved  ||      free       |
    | Lic serv | cluster 1 | cluster 2 | cluster3 | not to use  ||     to use      |
    --------------------------------------------------------------------------------

    Since we have 303 licenses in use (booked or license server) and 100 that should
    not be used (past the limit), the amount of licenses available is 597.

    This way, we need to block the remaing 403 licenses. But considering that Slurm
    is already "blocking" 23 licenses that are in use in the cluster, the reservation
    should block 380 licenses.
    """
    update_inventories_mock.return_value = [{"product_feature": "abaqus.abaqus", "total": 1000, "used": 200}]
    get_cluster_from_backend_mock.return_value = parsed_clusters[0]
    get_configs_from_backend_mock.return_value = parsed_clusters[0].configurations
    get_bookings_sum_mock.return_value = {
        1: 15,
        2: 17,
        3: 71,
    }
    get_tokens_mock.return_value = 23

    await reconcile()
    create_or_update_reservation_mock.assert_called_with("abaqus.abaqus@flexlm:380")


@pytest.mark.asyncio
@mock.patch("lm_agent.reconciliation.report")
async def test__update_inventories__report_empty(report_mock):
    """
    Check the correct behavior when the report is empty in reconcile.
    """
    report_mock.return_value = []
    with pytest.raises(LicenseManagerEmptyReportError):
        await update_inventories()


@pytest.mark.asyncio
@pytest.mark.respx(base_url="http://backend")
@mock.patch("lm_agent.reconciliation.report")
@mock.patch("lm_agent.reconciliation.get_feature_ids")
@mock.patch("lm_agent.reconciliation.get_cluster_from_backend")
async def test__update_inventories__put_failed(
    get_cluster_from_backend_mock, get_feature_ids_mock, report_mock, respx_mock, parsed_clusters
):
    """
    Check that when put /features/update_inventorys status_code is not 200, should raise exception.
    """
    get_cluster_from_backend_mock.return_value = parsed_clusters[0]
    get_feature_ids_mock.return_value = {
        "abaqus.abaqus": 1,
        "converge.converge_super": 2,
    }
    report_mock.return_value = [{"product_feature": "abaqus.abaqus", "total": 1000, "used": 200}]

    respx_mock.put("/lm/features/1/update_inventory").mock(return_value=Response(status_code=400))

    with pytest.raises(LicenseManagerBackendConnectionError):
        await update_inventories()


@pytest.mark.asyncio
@mock.patch("lm_agent.reconciliation.get_jobs_from_backend")
@mock.patch("lm_agent.reconciliation.remove_job_by_slurm_job_id")
async def test__clean_jobs(remove_job_by_slurm_job_id_mock, get_jobs_from_backend_mock):
    """
    Check that the jobs that aren't running are cleaned.
    """
    squeue_parsed = [
        {"job_id": 1, "state": "RUNNING"},
        {"job_id": 2, "state": "COMPLETED"},
        {"job_id": 3, "state": "SUSPENDED"},
    ]
    booking_mock_2 = mock.Mock()
    booking_mock_2.job_id = 2
    booking_mock_3 = mock.Mock()
    booking_mock_3.job_id = 3
    get_jobs_from_backend_mock.return_value = [booking_mock_2, booking_mock_3]
    await clean_jobs(squeue_parsed)

    remove_job_by_slurm_job_id_mock.call_count == 2


@pytest.mark.asyncio
@mock.patch("lm_agent.reconciliation.get_jobs_from_backend")
@mock.patch("lm_agent.reconciliation.remove_job_by_slurm_job_id")
async def test__clean_jobs__not_in_squeue(remove_job_by_slurm_job_id_mock, get_jobs_from_backend_mock):
    """
    Check that jobs that aren't in squeue are cleaned.
    """
    squeue_parsed = [{"job_id": 1, "state": "RUNNING"}]
    booking_mock_1 = mock.Mock()
    booking_mock_1.job_id = 1
    booking_mock_2 = mock.Mock()
    booking_mock_2.job_id = 2
    get_jobs_from_backend_mock.return_value = [booking_mock_1, booking_mock_2]
    await clean_jobs(squeue_parsed)

    remove_job_by_slurm_job_id_mock.call_count == 1


@mark.asyncio
@mock.patch("lm_agent.reconciliation.scontrol_create_reservation")
@mock.patch("lm_agent.reconciliation.scontrol_show_reservation")
@mock.patch("lm_agent.reconciliation.scontrol_update_reservation")
@mock.patch("lm_agent.reconciliation.scontrol_delete_reservation")
async def test_create_or_update_reservation(delete_mock, update_mock, show_mock, create_mock):
    """
    Test that create_or_update_reservation:
    - update the reservation if it exists
    - delete the reservation if it can't update
    - create the reservation if doesn't exist
    """
    # Update reservation if it exists
    show_mock.return_value = "reservation_data"
    await create_or_update_reservation("reservation_info")
    update_mock.assert_called_once()

    # Delete reservation if it can't update
    show_mock.return_value = "reservation_data"
    update_mock.return_value = False
    await create_or_update_reservation("reservation_info")
    delete_mock.assert_called()

    # Create reservation if it doesn't exist
    show_mock.return_value = False
    await create_or_update_reservation("reservation_info")
    create_mock.assert_called()
