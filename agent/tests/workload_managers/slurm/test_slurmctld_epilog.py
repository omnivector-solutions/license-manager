from unittest import mock

import pytest

from lm_agent.workload_managers.slurm.slurmctld_epilog import epilog


@pytest.mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.get_job_context")
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.reconcile")
async def test_epilog(reconcile_mock, get_job_context_mock):
    get_job_context_mock.return_value = {
        "job_id": "1",
        "user_name": "user1",
        "lead_host": "host1",
        "cluster_name": "cluster1",
    }
    await epilog()
    reconcile_mock.assert_awaited_once()
