"""
Utilities useful to any backend namespace
"""
from fastapi import HTTPException

from licensemanager2.backend.settings import SETTINGS


def debug():
    """
    Enforce debug mode
    """
    if not SETTINGS.DEBUG:
        raise HTTPException(status_code=403)
