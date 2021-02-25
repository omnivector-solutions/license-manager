"""
Test the debug dependency
"""
from unittest.mock import patch

from fastapi.exceptions import HTTPException
from pytest import raises

from licensemanager2.backend import debug


def test_debug():
    """
    Does the debug dependency raise an exception?
    """
    p_log = patch.object(debug.SETTINGS, "DEBUG", False)
    with p_log:
        with raises(HTTPException):
            debug.debug()

    p_log = patch.object(debug.SETTINGS, "DEBUG", True)
    with p_log:
        debug.debug()
