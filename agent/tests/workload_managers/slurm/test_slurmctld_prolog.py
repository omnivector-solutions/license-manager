"""
Test Prolog script.
"""
from unittest import mock

import pytest

from lm_agent.workload_managers.slurm.slurmctld_prolog import prolog as main


@pytest.mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.sys")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.get_job_context")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.get_required_licenses_for_job")
async def test_main_error_in_get_required_licenses_for_job(
    get_required_licenses_for_job_mock,
    get_job_context_mock,
    sys_mock,
):
    get_job_context_mock.return_value = {
        "job_id": "1",
        "user_name": "user1",
        "lead_host": "host1",
        "job_licenses": "",
    }
    get_required_licenses_for_job_mock.side_effect = Exception

    with pytest.raises(Exception):
        await main()


@pytest.mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.sys")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.get_job_context")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.get_required_licenses_for_job")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.get_config_from_backend")
async def test_main_error_in_get_config_from_backend(
    get_config_from_backend_mock,
    get_required_licenses_for_job_mock,
    get_job_context_mock,
    sys_mock,
):
    get_job_context_mock.return_value = {
        "job_id": "1",
        "user_name": "user1",
        "lead_host": "host1",
        "job_licenses": "test.feature@flexlm:10",
    }
    bookings_mock = mock.MagicMock()
    bookings_mock.product_feature = "test.feature"
    bookings_mock.license_server_type = "flexlm"
    bookings_mock.tokens = 10
    get_required_licenses_for_job_mock.return_value = [bookings_mock]
    get_config_from_backend_mock.side_effect = Exception

    with pytest.raises(Exception):
        await main()
    get_required_licenses_for_job_mock.assert_called_once_with("test.feature@flexlm:10")


@pytest.mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.get_job_context")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.get_required_licenses_for_job")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.get_config_from_backend")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.update_report")
async def test_main_error_in_reconcile(
    update_report_mock,
    get_config_from_backend_mock,
    get_required_licenses_for_job_mock,
    get_job_context_mock,
):
    get_job_context_mock.return_value = {
        "job_id": "1",
        "user_name": "user1",
        "lead_host": "host1",
        "job_licenses": "test.feature@flexlm:10",
    }
    bookings_mock = mock.MagicMock()
    bookings_mock.product_feature = "test.feature"
    bookings_mock.license_server_type = "flexlm"
    bookings_mock.tokens = 10
    get_required_licenses_for_job_mock.return_value = [bookings_mock]

    backend_return_mock = mock.MagicMock()
    backend_return_mock.product = "test"
    backend_return_mock.features = ["feature"]
    get_config_from_backend_mock.return_value = [backend_return_mock]

    update_report_mock.side_effect = Exception

    with pytest.raises(Exception):
        await main()

    get_required_licenses_for_job_mock.assert_called_once_with("test.feature@flexlm:10")
    get_config_from_backend_mock.assert_awaited_once()


@pytest.mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.sys")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.get_job_context")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.get_required_licenses_for_job")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.get_config_from_backend")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.update_report")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.make_booking_request")
async def test_main(
    make_booking_request_mock,
    update_report_mock,
    get_config_from_backend_mock,
    get_required_licenses_for_job_mock,
    get_job_context_mock,
    sys_mock,
):
    get_job_context_mock.return_value = {
        "job_id": "1",
        "user_name": "user1",
        "lead_host": "host1",
        "cluster_name": "cluster1",
        "job_licenses": "test.feature@flexlm:10",
    }
    bookings_mock = mock.MagicMock()
    bookings_mock.product_feature = "test.feature"
    bookings_mock.license_server_type = "flexlm"
    bookings_mock.tokens = 10
    get_required_licenses_for_job_mock.return_value = [bookings_mock]

    backend_return_mock = mock.MagicMock()
    backend_return_mock.product = "test"
    backend_return_mock.features = ["feature"]
    get_config_from_backend_mock.return_value = [backend_return_mock]

    await main()

    get_config_from_backend_mock.assert_awaited_once()
    get_required_licenses_for_job_mock.assert_called_once_with("test.feature@flexlm:10")
    update_report_mock.assert_awaited_once()
    make_booking_request_mock.assert_awaited_once()


@pytest.mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.sys")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.settings")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.get_job_context")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.get_required_licenses_for_job")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.get_config_from_backend")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.update_report")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_prolog.make_booking_request")
async def test_main_without_triggering_reconciliation(
    make_booking_request_mock,
    update_report_mock,
    get_config_from_backend_mock,
    get_required_licenses_for_job_mock,
    get_job_context_mock,
    settings_mock,
    sys_mock,
):
    get_job_context_mock.return_value = {
        "job_id": "1",
        "user_name": "user1",
        "lead_host": "host1",
        "cluster_name": "cluster1",
        "job_licenses": "test.feature@flexlm:10",
    }

    bookings_mock = mock.MagicMock()
    bookings_mock.product_feature = "test.feature"
    bookings_mock.license_server_type = "flexlm"
    bookings_mock.tokens = 10
    get_required_licenses_for_job_mock.return_value = [bookings_mock]

    backend_return_mock = mock.MagicMock()
    backend_return_mock.product = "test"
    backend_return_mock.features = ["feature"]
    get_config_from_backend_mock.return_value = [backend_return_mock]

    settings_mock.USE_RECONCILE_IN_PROLOG_EPILOG = False

    await main()

    get_config_from_backend_mock.assert_awaited_once()
    get_required_licenses_for_job_mock.assert_called_once_with("test.feature@flexlm:10")
    make_booking_request_mock.assert_awaited_once()

    update_report_mock.assert_not_called()
