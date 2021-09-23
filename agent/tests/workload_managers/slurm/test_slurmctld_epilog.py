from unittest import mock

import pytest

from lm_agent.workload_managers.slurm.slurmctld_epilog import epilog as main


@pytest.mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.sys")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_required_licenses_for_job")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_job_context")
async def test_main_error_in_get_required_licenses_for_job(
    get_job_context_mock, get_required_licenses_for_job_mock, sys_mock
):
    get_required_licenses_for_job_mock.side_effect = Exception
    get_job_context_mock.return_value = {"job_id": "1", "user_name": "user1", "lead_host": "host1"}

    with pytest.raises(Exception):
        await main()


@pytest.mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.sys")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_required_licenses_for_job")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_job_context")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_config_from_backend")
async def test_main_error_in_get_config_from_backend(
    get_config_from_backend_mock, get_job_context_mock, get_required_licenses_for_job_mock, sys_mock
):
    get_job_context_mock.return_value = {"job_id": "1", "user_name": "user1", "lead_host": "host1"}
    bookings_mock = mock.MagicMock()
    bookings_mock.product_feature = "test.feature"
    bookings_mock.license_server_type = "flexlm"
    bookings_mock.tokens = 10
    get_required_licenses_for_job_mock.return_value = [bookings_mock]
    get_config_from_backend_mock.side_effect = Exception

    with pytest.raises(Exception):
        await main()

    get_required_licenses_for_job_mock.assert_awaited_once_with("1")


@pytest.mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.sys")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_required_licenses_for_job")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_job_context")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_config_from_backend")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_tokens_for_license")
async def test_main_error_in_get_tokens_for_license(
    get_tokens_for_license_mock,
    get_config_from_backend_mock,
    get_job_context_mock,
    get_required_licenses_for_job_mock,
    sys_mock,
):
    get_job_context_mock.return_value = {"job_id": "1", "user_name": "user1", "lead_host": "host1"}
    bookings_mock = mock.MagicMock()
    bookings_mock.product_feature = "test.feature"
    bookings_mock.license_server_type = "flexlm"
    bookings_mock.tokens = 10
    get_required_licenses_for_job_mock.return_value = [bookings_mock]
    backend_return_mock = mock.MagicMock()
    backend_return_mock.product = "test"
    backend_return_mock.features = ["feature"]
    get_config_from_backend_mock.return_value = [backend_return_mock]
    get_tokens_for_license_mock.side_effect = Exception

    with pytest.raises(Exception):
        await main()

    get_required_licenses_for_job_mock.assert_awaited_once_with("1")
    get_config_from_backend_mock.assert_awaited_once()


@pytest.mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.sys")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_job_context")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_required_licenses_for_job")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_config_from_backend")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_tokens_for_license")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.sacctmgr_modify_resource")
async def test_main(
    sacctmgr_modify_resource_mock,
    get_tokens_for_license_mock,
    get_config_from_backend_mock,
    get_required_licenses_for_job_mock,
    get_job_context_mock,
    sys_mock,
    caplog,
):
    get_job_context_mock.return_value = {"job_id": "1", "user_name": "user1", "lead_host": "host1"}
    bookings_mock = mock.MagicMock()
    bookings_mock.product_feature = "test.feature"
    bookings_mock.license_server_type = "flexlm"
    bookings_mock.tokens = 10
    get_required_licenses_for_job_mock.return_value = [bookings_mock]

    backend_return_mock = mock.MagicMock()
    backend_return_mock.product = "test"
    backend_return_mock.features = ["feature"]
    get_config_from_backend_mock.return_value = [backend_return_mock]

    get_tokens_for_license_mock.return_value = 100

    await main()

    get_required_licenses_for_job_mock.assert_awaited_once_with("1")
    get_config_from_backend_mock.assert_awaited_once()
    get_tokens_for_license_mock.assert_awaited_once_with("test.feature@flexlm", "Total")
    sacctmgr_modify_resource_mock.assert_awaited_once_with("test", "feature", 90)

    assert "Slurmdbd updated successfully." in caplog.text
