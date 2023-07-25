from lm_test.utils import run
from lm_test.exceptions import JobFailedError


def get_job_info(job_id):
    return run(
        "juju ssh",
        "slurmd/leader",
        "scontrol",
        "show",
        "job",
        job_id,
        "-o"
    )


def submit_job():
    """
    Submit the fake job to the cluster.
    """
    print("Submitting job...")
    job_submission = run(
        "juju ssh",
        "slurmd/leader",
        "sbatch",
        "/tmp/batch.sh",
    )

    assert "Submitted batch job" in job_submission
    job_id = job_submission.split()[-1]
    print("Job submitted.")

    print("Waiting for job to finish...")

    job_info = get_job_info(job_id)
    while "JobState=COMPLETED" not in job_info:
        job_info = get_job_info(job_id)

        JobFailedError.require_condition(
            "JobState=FAILED" not in job_info,
        )

    print("Job finished.")
