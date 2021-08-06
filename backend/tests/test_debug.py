from unittest.mock import patch

from fastapi.exceptions import HTTPException
from pytest import raises

from app import debug


def test_debug():
    """
    Does the debug dependency raise an exception when the app is *not* in debug mode?
    """
    with patch.object(debug.settings, "DEBUG", False):
        with raises(HTTPException):
            debug.debug()

    with patch.object(debug.settings, "DEBUG", True):
        debug.debug()
