from fastapi import HTTPException

from app.config import settings


def debug():
    """
    Enforce debug mode
    """
    if not settings.DEBUG:
        raise HTTPException(status_code=403)
