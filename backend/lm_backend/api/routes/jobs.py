from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models import Job
from lm_backend.api.schemas import JobCreateSchema, JobSchema, JobUpdateSchema
from lm_backend.database import get_session
from lm_backend.permissions import Permissions
from lm_backend.security import guard

router = APIRouter()


crud_job = GenericCRUD(Job, JobCreateSchema, JobUpdateSchema)


@router.post(
    "/",
    response_model=JobSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(guard.lockdown(Permissions.JOB_EDIT))],
)
async def create_job(
    job: JobCreateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Create a new job."""
    return await crud_job.create(db_session=db_session, obj=job)


@router.get(
    "/",
    response_model=List[JobSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.JOB_VIEW))],
)
async def read_all_jobs(
    search: Optional[str] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_ascending: bool = Query(True),
    db_session: AsyncSession = Depends(get_session),
):
    """Return all jobs."""
    return await crud_job.read_all(
        db_session=db_session, search=search, sort_field=sort_field, sort_ascending=sort_ascending
    )


@router.get(
    "/{job_id}",
    response_model=JobSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.JOB_VIEW))],
)
async def read_job(job_id: int, db_session: AsyncSession = Depends(get_session)):
    """Return a job with associated bookings with the given id."""
    return await crud_job.read(db_session=db_session, id=job_id)


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.JOB_EDIT))],
)
async def delete_job(job_id: int, db_session: AsyncSession = Depends(get_session)):
    """Delete a job from the database and associated bookings."""
    await crud_job.delete(db_session=db_session, id=job_id)
    return {"message": "Job deleted successfully"}


@router.delete(
    "/slurm_job_id/{slurm_job_id}/cluster/{cluster_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.JOB_EDIT))],
)
async def delete_job_by_slurm_id(
    slurm_job_id: str, cluster_id: int, db_session: AsyncSession = Depends(get_session)
):
    """
    Delete a job from the database and associated bookings.
    Uses the slurm_job_id and the cluster_id to filter the job.

    Since the slurm_job_id can be the same across clusters, we need the cluster_id to validate.
    """
    jobs = await crud_job.read_all(db_session=db_session, search=slurm_job_id)

    for job in jobs:
        if job.cluster_id == cluster_id:
            await crud_job.delete(db_session=db_session, id=job.id)
            return {"message": "Job deleted successfully"}

    raise HTTPException(status_code=404, detail="The job doesn't exist in this cluster.")


@router.get(
    "/slurm_job_id/{slurm_job_id}/cluster/{cluster_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.JOB_VIEW))],
)
async def read_job_by_slurm_id(
    slurm_job_id: str, cluster_id: int, db_session: AsyncSession = Depends(get_session)
):
    """
    Read a job from the database and associated bookings.
    Uses the slurm_job_id and the cluster_id to filter the job.

    Since the slurm_job_id can be the same across clusters, we need the cluster_id to validate.
    """
    jobs = await crud_job.read_all(db_session=db_session, search=slurm_job_id)

    for job in jobs:
        if job.cluster_id == cluster_id:
            return job

    raise HTTPException(status_code=404, detail="The job doesn't exist in this cluster.")
