from unittest import mock

import pytest

from lm_agent.workload_managers.slurm.slurmctld_epilog import epilog


@pytest.mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.slurmctld_epilog.reconcile")
async def test_epilog(reconcile_mock):
    await epilog()
    reconcile_mock.assert_awaited_once()
