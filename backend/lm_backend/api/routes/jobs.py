from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from lm_backend.api.cruds.booking import BookingCRUD
from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models.booking import Booking
from lm_backend.api.models.job import Job
from lm_backend.api.schemas.booking import BookingCreateSchema, BookingUpdateSchema
from lm_backend.api.schemas.job import JobCreateSchema, JobSchema, JobUpdateSchema, JobWithBookingCreateSchema
from lm_backend.database import SecureSession, secure_session
from lm_backend.permissions import Permissions

router = APIRouter()


crud_job = GenericCRUD(Job, JobCreateSchema, JobUpdateSchema)
crud_booking = BookingCRUD(Booking, BookingCreateSchema, BookingUpdateSchema)


@router.post(
    "/",
    response_model=JobSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
    job: JobWithBookingCreateSchema,
    secure_session: SecureSession = Depends(secure_session(Permissions.JOB_EDIT)),
):
    """Create a new job."""
    job_created: Job = await crud_job.create(
        db_session=secure_session.session, obj=JobCreateSchema(**job.dict(exclude={"bookings"}))
    )

    if job.bookings:
        try:
            for booking in job.bookings:
                obj = {
                    "job_id": job_created.id,
                    "feature_id": booking.feature_id,
                    "quantity": booking.quantity,
                }
                await crud_booking.create(db_session=secure_session.session, obj=BookingCreateSchema(**obj))
        except HTTPException:
            await crud_job.delete(db_session=secure_session.session, id=job_created.id)
            raise

    return await crud_job.read(db_session=secure_session.session, id=job_created.id)


@router.get(
    "/",
    response_model=List[JobSchema],
    status_code=status.HTTP_200_OK,
)
async def read_all_jobs(
    search: Optional[str] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_ascending: bool = Query(True),
    secure_session: SecureSession = Depends(secure_session(Permissions.JOB_VIEW)),
):
    """Return all jobs."""
    return await crud_job.read_all(
        db_session=secure_session.session, search=search, sort_field=sort_field, sort_ascending=sort_ascending
    )


@router.get(
    "/{job_id}",
    response_model=JobSchema,
    status_code=status.HTTP_200_OK,
)
async def read_job(
    job_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.JOB_VIEW)),
):
    """Return a job with associated bookings with the given id."""
    return await crud_job.read(db_session=secure_session.session, id=job_id)


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_job(
    job_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.JOB_EDIT)),
):
    """Delete a job from the database and associated bookings."""
    await crud_job.delete(db_session=secure_session.session, id=job_id)
    return {"message": "Job deleted successfully"}


@router.delete(
    "/slurm_job_id/{slurm_job_id}/cluster/{cluster_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_job_by_slurm_id(
    slurm_job_id: str,
    cluster_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.JOB_EDIT)),
):
    """
    Delete a job from the database and associated bookings.

    Uses the slurm_job_id and the cluster_id to filter the job.

    Since the slurm_job_id can be the same across clusters, we need the cluster_id to validate.
    """
    jobs: List[Job] = await crud_job.read_all(db_session=secure_session.session, search=slurm_job_id)

    for job in jobs:
        if job.cluster_id == cluster_id:
            return await crud_job.delete(db_session=secure_session.session, id=job.id)

    raise HTTPException(status_code=404, detail="The job doesn't exist in this cluster.")


@router.get(
    "/slurm_job_id/{slurm_job_id}/cluster/{cluster_id}",
    response_model=JobSchema,
    status_code=status.HTTP_200_OK,
)
async def read_job_by_slurm_id(
    slurm_job_id: str,
    cluster_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.JOB_VIEW)),
):
    """
    Read a job from the database and associated bookings.

    Uses the slurm_job_id and the cluster_id to filter the job.

    Since the slurm_job_id can be the same across clusters, we need the cluster_id to validate.
    """
    jobs: List[Job] = await crud_job.read_all(db_session=secure_session.session, search=slurm_job_id)

    for job in jobs:
        if job.cluster_id == cluster_id:
            return job

    raise HTTPException(status_code=404, detail="The job doesn't exist in this cluster.")
