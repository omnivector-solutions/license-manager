"""
Common utilities for slurm commands.
"""
import os

from licensemanager2.workload_managers.slurm.settings import SETTINGS
from licensemanager2.workload_managers.slurm.command_logger import log


LM2_AGENT_HEADERS = {
    "authorization": f"Bearer {SETTINGS.AGENT_JWT_TOKEN}",
    "content-type": "application/json"
}


def get_job_context():
    """Get and return variables from the job environment."""
    ctxt = dict()
    try:
        ctxt = {
            'cluster_name': os.environ['SLURM_CLUSTER_NAME'],
            'job_id': os.environ['SLURM_JOB_ID'],
            'compute_host': os.environ['SLURM_JOB_NODELIST'].split(',')[0],
            'user': os.environ['SLURM_JOB_USER'],
        }
    except KeyError as e:
        # If not all keys could be assigned, then return non 0 exit status
        log.error(
            f"All required environment variables were not set, missing: {e}. "
            "Expecting: SLURM_CLUSTER_NAME, SLURM_JOB_ID, SLURM_JOB_NODELIST, "
            "SLURM_JOB_USER"
        )

    return ctxt
