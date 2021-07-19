"""
Tests of Prolog
"""
from typing import List
from pytest import fixture, mark, raises
from unittest import mock
from licensemanager2.workload_managers.slurm.common import ENCODING
from licensemanager2.workload_managers.slurm.cmd_utils import (
    get_licenses_for_job,
    get_required_licenses_for_job,
    ScontrolRetrievalFailure,
)


@fixture
def scontrol_parsed_output_good() -> List[str]:
    return [
        "TESTPRODUCT.TESTFEATURE@flexlm:11",
        "TESTPRODUCT2.TESTFEATURE2@flexlm:22",
        "TESTPRODUCT3.TESTFEATURE3@flexlm:33",
    ]


@fixture
def scontrol_parsed_output_bad() -> List[str]:
    return [
        "TESTFEATURE@flexlm:11",
        "TESTPRODUCT2@22",
        "TESTFEATURE3@flexlm",
    ]


@fixture
def slurm_job_id() -> str:
    return "777"


class MockProcess:

    def __init__(self, result_str: str, returncode: int = 0):
        self.result = result_str.encode(ENCODING)
        self.returncode = returncode

    async def communicate(self, *args, **kwargs):
        return (self.result, None)  # Must be at least a 2-tuple


@mark.asyncio
@mock.patch("asyncio.create_subprocess_shell")
async def test_get_licenses_for_job_good(
    create_process_shell_mock: mock.MagicMock,
):
    """
    Do I properly parse licenses out of `scontrol show` commands?
    """
    create_process_shell_mock.return_value = MockProcess(
        """
        JobId=2 JobName=sleep
           UserId=root(0) GroupId=root(0) MCS_label=N/A
           Priority=4294901759 Nice=0 Account=root QOS=normal
           JobState=CANCELLED Reason=Nodes_required_for_job_are_DOWN,_DRAINED_or_reserved_for_jobs_in_higher_priority_partitions
       Dependency=(null)
           Requeue=1 Restarts=0 BatchFlag=0 Reboot=0 ExitCode=0:0
           RunTime=00:00:00 TimeLimit=UNLIMITED TimeMin=N/A
           SubmitTime=2021-07-19T20:22:45 EligibleTime=2021-07-19T20:22:45
           AccrueTime=2021-07-19T20:22:45
           StartTime=2021-07-19T20:22:49 EndTime=2021-07-19T20:22:49 Deadline=N/A
           SuspendTime=None SecsPreSuspend=0 LastSchedEval=2021-07-19T20:22:46
           Partition=osd-slurmd AllocNode:Sid=juju-fe651b-2:8232
           ReqNodeList=(null) ExcNodeList=(null)
           NodeList=(null)
           NumNodes=1 NumCPUs=8 NumTasks=0 CPUs/Task=1 ReqB:S:C:T=0:0:*:*
           TRES=cpu=8,billing=8
           Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=*
           MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0
           Features=(null) DelayBoot=00:00:00
              OverSubscribe=NO Contiguous=0 Licenses=test_feature.test_product@flexlm:10 Network=(null)
           Command=sleep
           WorkDir=/home/ubuntu
           Power=
           NtasksPerTRES:0
        """,
        returncode=0,
    )
    license_list = await get_licenses_for_job("some-job")
    assert license_list == ["test_feature.test_product@flexlm:10"]


@mark.asyncio
@mock.patch("asyncio.create_subprocess_shell")
async def test_get_licenses_for_job_no_licenses(
    create_process_shell_mock: mock.MagicMock,
):
    """
    Do I return an empty list if the regular expression fails to match any licenses
    """
    create_process_shell_mock.return_value = MockProcess(
        """
        JobId=2 JobName=sleep
           UserId=root(0) GroupId=root(0) MCS_label=N/A
           Priority=4294901759 Nice=0 Account=root QOS=normal
           JobState=CANCELLED Reason=Nodes_required_for_job_are_DOWN,_DRAINED_or_reserved_for_jobs_in_higher_priority_partitions
       Dependency=(null)
           Requeue=1 Restarts=0 BatchFlag=0 Reboot=0 ExitCode=0:0
           RunTime=00:00:00 TimeLimit=UNLIMITED TimeMin=N/A
           SubmitTime=2021-07-19T20:22:45 EligibleTime=2021-07-19T20:22:45
           AccrueTime=2021-07-19T20:22:45
           StartTime=2021-07-19T20:22:49 EndTime=2021-07-19T20:22:49 Deadline=N/A
           SuspendTime=None SecsPreSuspend=0 LastSchedEval=2021-07-19T20:22:46
           Partition=osd-slurmd AllocNode:Sid=juju-fe651b-2:8232
           ReqNodeList=(null) ExcNodeList=(null)
           NodeList=(null)
           NumNodes=1 NumCPUs=8 NumTasks=0 CPUs/Task=1 ReqB:S:C:T=0:0:*:*
           TRES=cpu=8,billing=8
           Socks/Node=* NtasksPerN:B:S:C=0:0:*:* CoreSpec=*
           MinCPUsNode=1 MinMemoryNode=0 MinTmpDiskNode=0
           Features=(null) DelayBoot=00:00:00
              OverSubscribe=NO Contiguous=0 Network=(null)
           Command=sleep
           WorkDir=/home/ubuntu
           Power=
           NtasksPerTRES:0
        """,
        returncode=0,
    )
    license_list = await get_licenses_for_job("some-job")
    assert license_list == []


@mark.asyncio
@mock.patch("asyncio.create_subprocess_shell")
async def test_get_licenses_for_job_error(
    create_process_shell_mock: mock.MagicMock,
):
    """
    Do I raise an ScontrolRetrievalFailure exception if the return value is not 0?
    """
    create_process_shell_mock.return_value = MockProcess(
        "",
        returncode=1,
    )
    with raises(ScontrolRetrievalFailure, match="Could not get SLURM data for job id: some-job"):
        await get_licenses_for_job("some-job")


@mark.asyncio
@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.get_licenses_for_job")
async def test_get_required_licenses_for_job_good(
    get_licenses_for_job_mock: mock.MagicMock,
    slurm_job_id: str, scontrol_parsed_output_good: List[str]
):
    """
    Do I return the correct licenses when the license format matches?
    """
    get_licenses_for_job_mock.return_value = scontrol_parsed_output_good
    license_booking_request = await get_required_licenses_for_job(
        slurm_job_id
    )
    assert len(license_booking_request.bookings) == 3


@mark.asyncio
@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.get_licenses_for_job")
async def test_get_required_licenses_for_job_bad(
    get_licenses_for_job_mock: mock.MagicMock,
    slurm_job_id: str, scontrol_parsed_output_bad: List[str]
):
    """
    Do I return the correct licenses when the license format doesn't match?
    """

    get_licenses_for_job_mock.return_value = scontrol_parsed_output_bad
    license_booking_request = await get_required_licenses_for_job(
        slurm_job_id
    )
    assert len(license_booking_request.bookings) == 0
