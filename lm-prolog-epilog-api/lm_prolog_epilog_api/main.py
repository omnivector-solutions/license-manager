"""FastAPI application for Slurm prolog/epilog license management hooks."""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from lm_prolog_epilog_api import __version__
from lm_prolog_epilog_api.schemas import JobHookRequest, JobHookResponse

app = FastAPI(
    title="License Manager Prolog/Epilog API",
    version=__version__,
    description="API for Slurm prolog/epilog hooks to communicate job lifecycle events",
    contact={
        "name": "Omnivector Solutions",
        "url": "https://www.omnivector.solutions/",
        "email": "info@omnivector.solutions",
    },
    license_info={
        "name": "MIT License",
        "url": "https://github.com/omnivector-solutions/license-manager/blob/main/LICENSE",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", status_code=status.HTTP_204_NO_CONTENT)
async def health():
    """Health check endpoint."""
    return None


@app.post(
    "/prolog",
    status_code=status.HTTP_200_OK,
    response_model=JobHookResponse,
)
async def prolog(request: JobHookRequest) -> JobHookResponse:
    """
    Prolog endpoint - called when a Slurm job starts.

    This endpoint receives job information from the slurmctld prolog script
    and calls the license-manager-agent prolog function to handle license booking.
    """
    # Lazy import to defer settings loading until runtime
    from lm_agent.workload_managers.slurm.slurmctld_prolog import prolog as agent_prolog
    
    job_context = {
        "cluster_name": request.cluster_name,
        "job_id": request.job_id,
        "lead_host": request.lead_host,
        "user_name": request.user_name,
        "job_licenses": request.job_licenses,
    }
    
    try:
        await agent_prolog(job_context=job_context, skip_reconcile=True)
    except SystemExit as e:
        pass
        if e.code != 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Prolog failed for job {request.job_id}",
            )
    return JobHookResponse(
        status="ok",
        message=f"Prolog completed for job {request.job_id} on cluster {request.cluster_name}",
    )


@app.post(
    "/epilog",
    status_code=status.HTTP_200_OK,
    response_model=JobHookResponse,
)
async def epilog(request: JobHookRequest) -> JobHookResponse:
    """
    Epilog endpoint - called when a Slurm job ends.

    This endpoint receives job information from the slurmctld epilog script
    and calls the license-manager-agent epilog function to handle license release.
    """
    # Lazy import to defer settings loading until runtime
    from lm_agent.workload_managers.slurm.slurmctld_epilog import epilog as agent_epilog
    
    job_context = {
        "cluster_name": request.cluster_name,
        "job_id": request.job_id,
        "lead_host": request.lead_host,
        "user_name": request.user_name,
        "job_licenses": request.job_licenses,
    }
    
    try:
        await agent_epilog(job_context=job_context, skip_reconcile=True)
        return JobHookResponse(
            status="ok",
            message=f"Epilog completed for job {request.job_id} on cluster {request.cluster_name}",
        )
    except SystemExit as e:
        if e.code != 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Epilog failed for job {request.job_id}",
            )
        return JobHookResponse(
            status="ok",
            message=f"Epilog completed for job {request.job_id} on cluster {request.cluster_name}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Epilog error for job {request.job_id}: {str(e)}",
        )
