"""
Test Epilog script.
"""
from unittest import mock

import pytest

from lm_agent.workload_managers.slurm.slurmctld_epilog import epilog


@pytest.mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_job_context")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.update_report")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_required_licenses_for_job")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog._remove_booking_for_job")
async def test_epilog(
    remove_booking_for_job_mock,
    get_required_licenses_for_job_mock,
    update_report_mock,
    get_job_context_mock,
):
    bookings_mock = mock.MagicMock()
    bookings_mock.product_feature = "test.feature"
    bookings_mock.license_server_type = "flexlm"
    bookings_mock.tokens = 10
    get_required_licenses_for_job_mock.return_value = [bookings_mock]

    get_job_context_mock.return_value = {
        "job_id": "1",
        "user_name": "user1",
        "lead_host": "host1",
        "cluster_name": "cluster1",
        "job_licenses": "test.feature@flexlm:10",
    }
    await epilog()
    update_report_mock.assert_awaited_once()
    get_required_licenses_for_job_mock.assert_called_once_with("test.feature@flexlm:10")
    remove_booking_for_job_mock.assert_awaited_once_with("1")
