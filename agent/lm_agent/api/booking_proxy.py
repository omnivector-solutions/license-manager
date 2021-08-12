from fastapi import APIRouter, Depends

from lm_agent.forward import ForwardOperation

router = APIRouter()


@router.get("/all")
async def all_forward(forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a GET /all request to the backend and return the response
    """
    return await forward()


@router.get("/job/{slug}")
async def job_forward(slug: str, forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a /job/{job_id} request to the backend and return the response
    """
    return await forward()


@router.put("/book")
async def booking_put_forward(forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a /book[PUT] request to the backend and return the response
    """
    return await forward()


@router.delete("/book/{slug}")
async def booking_delete_forward(slug: str, forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a /book/{job_id}[DELETE] request to the backend and return the response
    """
    return await forward()
