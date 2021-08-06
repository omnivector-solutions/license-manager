from fastapi import APIRouter, Depends

from app.forward import ForwardOperation

router = APIRouter()


@router.get("/all")
async def all_forward(forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a GET /all request to the backend and return the response
    """
    return await forward()


@router.get("/use/{slug}")
async def use_forward(slug: str, forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a /use request to the backend and return the response
    """
    return await forward()
