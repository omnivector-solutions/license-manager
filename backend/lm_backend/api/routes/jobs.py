from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models import Job
from lm_backend.api.schemas import JobCreateSchema, JobSchema, JobUpdateSchema
from lm_backend.database import get_session

router = APIRouter()


crud_job = GenericCRUD(Job, JobCreateSchema, JobUpdateSchema)


@router.post(
    "/",
    response_model=JobSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
    job: JobCreateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Create a new job."""
    return await crud_job.create(db_session=db_session, obj=job)


@router.get("/", response_model=List[JobSchema], status_code=status.HTTP_200_OK)
async def read_all_jobs(db_session: AsyncSession = Depends(get_session)):
    """Return all jobs."""
    return await crud_job.read_all(db_session=db_session)


@router.get("/{job_id}", response_model=JobSchema, status_code=status.HTTP_200_OK)
async def read_job(job_id: int, db_session: AsyncSession = Depends(get_session)):
    """Return a job with associated bookings with the given id."""
    return await crud_job.read(db_session=db_session, id=job_id)


@router.delete("/{job_id}", status_code=status.HTTP_200_OK)
async def delete_job(job_id: int, db_session: AsyncSession = Depends(get_session)):
    """Delete a job from the database and associated bookings."""
    await crud_job.delete(db_session=db_session, id=job_id)
    return {"message": "Job deleted successfully"}


@router.get("/cluster/{cluster_id}", response_model=List[JobSchema], status_code=status.HTTP_200_OK)
async def read_jobs_by_cluster(cluster_id: int, db_session: AsyncSession = Depends(get_session)):
    """Return all jobs from a cluster."""
    return await crud_job.read_by_cluster(db_session=db_session, cluster_id=cluster_id)
