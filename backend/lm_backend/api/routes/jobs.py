from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from lm_backend.api.cruds.booking import BookingCRUD
from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models.booking import Booking
from lm_backend.api.models.job import Job
from lm_backend.api.routes.utils import find_feature_id_by_name_and_client_id
from lm_backend.api.schemas.booking import BookingCreateSchema, BookingUpdateSchema
from lm_backend.api.schemas.job import JobCreateSchema, JobSchema, JobUpdateSchema, JobWithBookingCreateSchema
from lm_backend.database import SecureSession, secure_session
from lm_backend.permissions import Permissions

router = APIRouter()


crud_job = GenericCRUD(Job, JobCreateSchema, JobUpdateSchema)
crud_booking = BookingCRUD(Booking, BookingCreateSchema, BookingUpdateSchema)


@router.post(
    "",
    response_model=JobSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
    job: JobWithBookingCreateSchema,
    secure_session: SecureSession = Depends(secure_session(Permissions.JOB_EDIT)),
):
    """Create a new job."""
    client_id = secure_session.identity_payload.client_id

    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("Couldn't find a valid client_id in the access token."),
        )

    if job.cluster_client_id is None:
        job.cluster_client_id = client_id

    job_created: Job = await crud_job.create(
        db_session=secure_session.session, obj=JobCreateSchema(**job.dict(exclude={"bookings"}))
    )

    if job.bookings:
        try:
            for booking in job.bookings:
                product, feature = booking.product_feature.split(".")
                feature_id = await find_feature_id_by_name_and_client_id(
                    db_session=secure_session.session, client_id=client_id, feature_name=feature
                )
                if not feature_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=("Couldn't find the feature to book."),
                    )
                obj = {
                    "job_id": job_created.id,
                    "feature_id": feature_id,
                    "quantity": booking.quantity,
                }
                await crud_booking.create(db_session=secure_session.session, obj=BookingCreateSchema(**obj))
        except HTTPException:
            await crud_job.delete(db_session=secure_session.session, id=job_created.id)
            raise

    return await crud_job.read(db_session=secure_session.session, id=job_created.id, force_refresh=True)


@router.get(
    "/by_client_id",
    response_model=List[JobSchema],
    status_code=status.HTTP_200_OK,
)
async def read_jobs_by_client_id(
    secure_session: SecureSession = Depends(secure_session(Permissions.JOB_VIEW)),
):
    """Return the jobs with the specified OIDC client_id retrieved from the request."""
    client_id = secure_session.identity_payload.client_id

    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("Couldn't find a valid client_id in the access token."),
        )

    return await crud_job.filter(
        db_session=secure_session.session, filter_expressions=[Job.cluster_client_id == client_id]
    )


@router.get(
    "",
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
        db_session=secure_session.session,
        search=search,
        sort_field=sort_field,
        sort_ascending=sort_ascending,
        force_refresh=True,
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
    return await crud_job.read(db_session=secure_session.session, id=job_id, force_refresh=True)


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_job(
    job_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.JOB_EDIT)),
):
    """Delete a job from the database and associated bookings."""
    return await crud_job.delete(db_session=secure_session.session, id=job_id)


@router.delete(
    "/slurm_job_id/{slurm_job_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_job_by_slurm_id(
    slurm_job_id: str,
    secure_session: SecureSession = Depends(secure_session(Permissions.JOB_EDIT)),
):
    """
    Delete a job from the database and associated bookings.

    Uses the slurm_job_id and the cluster client_id to filter the job.

    Since the slurm_job_id can be the same across clusters, we need the cluster client_id to validate.
    """
    client_id = secure_session.identity_payload.client_id

    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("Couldn't find a valid client_id in the access token."),
        )

    jobs: List[Job] = await crud_job.filter(
        db_session=secure_session.session,
        filter_expressions=[Job.slurm_job_id == slurm_job_id, Job.cluster_client_id == client_id],
    )

    for job in jobs:
        return await crud_job.delete(db_session=secure_session.session, id=job.id)

    raise HTTPException(status_code=404, detail="The job doesn't exist in this cluster.")


@router.get(
    "/slurm_job_id/{slurm_job_id}",
    response_model=JobSchema,
    status_code=status.HTTP_200_OK,
)
async def read_job_by_slurm_id(
    slurm_job_id: str,
    secure_session: SecureSession = Depends(secure_session(Permissions.JOB_VIEW)),
):
    """
    Read a job from the database and associated bookings.

    Uses the slurm_job_id and the cluster client_id to filter the job.

    Since the slurm_job_id can be the same across clusters, we need the cluster client_id to validate.
    """
    client_id = secure_session.identity_payload.client_id

    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("Couldn't find a valid client_id in the access token."),
        )

    jobs: List[Job] = await crud_job.filter(
        db_session=secure_session.session,
        filter_expressions=[Job.slurm_job_id == slurm_job_id, Job.cluster_client_id == client_id],
    )

    for job in jobs:
        return job

    raise HTTPException(status_code=404, detail="The job doesn't exist in this cluster.")
