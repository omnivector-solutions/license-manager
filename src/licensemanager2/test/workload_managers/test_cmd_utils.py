"""
Tests
"""
import pytest
import asyncio
from httpx import AsyncClient
from pytest import fixture, mark
from unittest import mock

from licensemanager2.backend import booking, schema
from licensemanager2.backend.storage import database
from licensemanager2.workload_managers.slurm.cmd_utils import get_licenses_for_job, ScontrolRetrievalFailure, scontrol_show_lic, ScontrolProcessError


@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.wait_for")
@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.create_subprocess_shell")
@mark.asyncio
async def test_get_licenses_for_job_empty(
    create_subprocess_shell_mock: mock.AsyncMock, wait_for_mock: mock.AsyncMock
):
    """
    Testing if scontrol output returns licences needed for a job.
    """
    create_subprocess_shell_mock.return_value = mock.AsyncMock()
    create_subprocess_shell_mock.communicate.return_value = mock.Mock()
    create_subprocess_shell_mock.return_value.returncode = 0
    
    wait_for_mock.return_value = b"", ""

    assert await get_licenses_for_job("0") == []
    


@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.wait_for")
@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.create_subprocess_shell")
@mark.asyncio
async def test_get_licenses_for_job(
    create_subprocess_shell_mock: mock.AsyncMock, wait_for_mock: mock.AsyncMock
):
    """
    Testing if scontrol output returns licences needed for a job.
    """
    create_subprocess_shell_mock.return_value = mock.AsyncMock()
    create_subprocess_shell_mock.communicate.return_value = mock.Mock()
    create_subprocess_shell_mock.return_value.returncode = 0
    
    wait_for_mock.return_value = b"  Licenses=(123) ", ""

    assert await get_licenses_for_job("0") == ['(123)']


@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.wait_for")
@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.create_subprocess_shell")
@mark.asyncio
async def test_get_licenses_for_job_raises_scontrol_retrieval_failure(
    create_subprocess_shell_mock: mock.AsyncMock, wait_for_mock: mock.AsyncMock
):
    """
    Testing if scontrol output returns licences needed for a job.
    """
    create_subprocess_shell_mock.return_value = mock.AsyncMock()
    create_subprocess_shell_mock.communicate.return_value = mock.Mock()
    create_subprocess_shell_mock.return_value.returncode = 1
    
    wait_for_mock.return_value = b"  Licenses=(123) ", ""

    with pytest.raises(ScontrolRetrievalFailure):
        await get_licenses_for_job("0")


@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.wait_for")
@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.create_subprocess_shell")
@mark.asyncio
async def test_scrontrol_show_lic(
    create_subprocess_shell_mock: mock.AsyncMock, wait_for_mock: mock.AsyncMock
):
    """
    Testing if scontrol output returns licences needed for a job.
    """
    create_subprocess_shell_mock.return_value = mock.AsyncMock()
    create_subprocess_shell_mock.communicate.return_value = mock.Mock()
    create_subprocess_shell_mock.return_value.returncode = 0
    
    wait_for_mock.return_value = b"test_return_value", ""

    assert await scontrol_show_lic() == "test_return_value"

    
@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.wait_for")
@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.create_subprocess_shell")
@mark.asyncio
async def test_scrontrol_show_lic_process_error(
    create_subprocess_shell_mock: mock.AsyncMock, wait_for_mock: mock.AsyncMock
):
    """
    Testing if scontrol output raises an exception when there is a process error
    """
    create_subprocess_shell_mock.return_value = mock.AsyncMock()
    create_subprocess_shell_mock.communicate.return_value = mock.Mock()
    create_subprocess_shell_mock.return_value.returncode = 1
    
    wait_for_mock.return_value = b"test_return_value", ""

    with pytest.raises(ScontrolProcessError):
        await scontrol_show_lic()