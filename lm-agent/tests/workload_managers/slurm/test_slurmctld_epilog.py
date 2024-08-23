"""
Test Epilog script.
"""
from unittest import mock

import pytest

from lm_agent.workload_managers.slurm.slurmctld_epilog import epilog


@pytest.mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_job_context")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.reconcile")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_required_licenses_for_job")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.remove_job_by_slurm_job_id")
async def test_epilog(
    remove_job_by_slurm_job_id_mock,
    get_required_licenses_for_job_mock,
    reconcile_mock,
    get_job_context_mock,
):
    bookings_mock = mock.MagicMock()
    bookings_mock.product_feature = "test.feature"
    bookings_mock.quantity = 10
    get_required_licenses_for_job_mock.return_value = [bookings_mock]

    get_job_context_mock.return_value = {
        "job_id": "1",
        "user_name": "user1",
        "lead_host": "host1",
        "cluster_name": "cluster1",
        "job_licenses": "test.feature@flexlm:10",
    }
    await epilog()
    reconcile_mock.assert_awaited_once()
    get_required_licenses_for_job_mock.assert_called_once_with("test.feature@flexlm:10")
    remove_job_by_slurm_job_id_mock.assert_awaited_once_with("1")


@pytest.mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.settings")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_job_context")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.reconcile")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_required_licenses_for_job")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.remove_job_by_slurm_job_id")
async def test_epilog_without_triggering_reconcile(
    remove_job_by_slurm_job_id_mock,
    get_required_licenses_for_job_mock,
    reconcile_mock,
    get_job_context_mock,
    settings_mock,
):
    bookings_mock = mock.MagicMock()
    bookings_mock.product_feature = "test.feature"
    bookings_mock.quantity = 10
    get_required_licenses_for_job_mock.return_value = [bookings_mock]

    get_job_context_mock.return_value = {
        "job_id": "1",
        "user_name": "user1",
        "lead_host": "host1",
        "cluster_name": "cluster1",
        "job_licenses": "test.feature@flexlm:10",
    }

    settings_mock.USE_RECONCILE_IN_PROLOG_EPILOG = False

    await epilog()
    reconcile_mock.assert_not_called()
    get_required_licenses_for_job_mock.assert_called_once_with("test.feature@flexlm:10")
    remove_job_by_slurm_job_id_mock.assert_awaited_once_with("1")
