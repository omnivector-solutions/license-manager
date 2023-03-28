"""CRUD operations for jobs."""
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from lm_backend.api.schemas.job import JobCreateSchema, JobSchema, JobUpdateSchema
from lm_backend.models.job import Job


class JobCRUD:
    """
    CRUD operations for jobs.
    """

    async def create(self, db_session: AsyncSession, job: JobCreateSchema) -> JobSchema:
        """
        Add a new job to the database.
        Returns the newly created job.
        """
        new_job = Job(**job.dict())
        try:
            await db_session.add(new_job)
            await db_session.commit()
        except Exception as e:
            print(e)
            raise HTTPException(status_code=400, detail="Job could not be created")
        return JobSchema.from_orm(new_job)

    async def read(self, db_session: AsyncSession, job_id: int) -> Optional[JobSchema]:
        """
        Read a job with the given id.
        Returns the job.
        """
        query = await db_session.execute(select(Job).filter(Job.id == job_id))
        db_job = query.scalars().one_or_none()

        if db_job is None:
            raise HTTPException(status_code=404, detail="Job not found")

        return JobSchema.from_orm(db_job.scalar_one_or_none())

    async def read_all(self, db_session: AsyncSession) -> List[JobSchema]:
        """
        Read all jobs.
        Returns a list of jobs.
        """
        query = await db_session.execute(select(Job))
        db_jobs = query.scalars().all()
        return [JobSchema.from_orm(db_job) for db_job in db_jobs]

    async def update(
        self, db_session: AsyncSession, job_id: int, job_update: JobUpdateSchema
    ) -> Optional[JobSchema]:
        """
        Update a job in the database.
        Returns the updated job.
        """
        query = await db_session.execute(select(Job).filter(Job.id == job_id))
        db_job = query.scalar_one_or_none()

        if db_job is None:
            raise HTTPException(status_code=404, detail="Job not found")

        for field, value in job_update:
            setattr(db_job, field, value)

        await db_session.commit()
        await db_session.refresh(db_job)
        return JobSchema.from_orm(db_job)

    async def delete(self, db_session: AsyncSession, job_id: int) -> bool:
        """
        Delete a job from the database.
        """
        query = await db_session.execute(select(Job).filter(Job.id == job_id))
        db_job = query.scalars().one_or_none()

        if db_job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        try:
            db_session.delete(db_job)
            await db_session.flush()
        except Exception:
            raise HTTPException(status_code=400, detail="Job could not be deleted")
