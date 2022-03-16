"""
Common utilities for slurm commands.
"""
import os

from lm_agent.logs import logger

SCONTROL_PATH = "/usr/bin/scontrol"
SACCTMGR_PATH = "/usr/bin/sacctmgr"
SQUEUE_PATH = "/usr/bin/squeue"
CMD_TIMEOUT = 5
ENCODING = "UTF8"


def get_job_context():
    """Get and return variables from the job environment."""
    ctxt = dict()
    try:
        ctxt = {
            "cluster_name": os.environ["SLURM_CLUSTER_NAME"],
            "job_id": os.environ["SLURM_JOB_ID"],
            "lead_host": os.environ["SLURM_JOB_NODELIST"].split(",")[0],
            "user_name": os.environ["SLURM_JOB_USER"],
            "job_licenses": os.environ.get("SLURM_JOB_LICENSES", ""),
        }
    except KeyError as e:
        # If not all keys could be assigned, then return non 0 exit status
        logger.error(
            f"All required environment variables were not set, missing: {e}. "
            "Expecting: SLURM_CLUSTER_NAME, SLURM_JOB_ID, SLURM_JOB_NODELIST, "
            "SLURM_JOB_USER, SLURM_JOB_LICENSES"
        )

    return ctxt
