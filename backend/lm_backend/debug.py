from fastapi import HTTPException

from lm_backend.config import settings


def debug():
    """
    Enforce debug mode
    """
    if not settings.DEBUG:
        raise HTTPException(status_code=403)
