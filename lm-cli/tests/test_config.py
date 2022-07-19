import os

import pytest

from lm_cli.config import build_settings


def test_Validation_error__when_parameter_is_missing():
    """
    Test if settings raise a validation error when a parameter is missing.
    """
    original_value = os.environ.get("OICD_DOMAIN")
    try:
        if "OICD_DOMAIN" in os.environ:
            del os.environ["OICD_DOMAIN"]

        with pytest.raises(SystemExit) as e:
            build_settings(_env_file=None)

        assert e.value.code == 1
    finally:
        if original_value is not None:
            os.environ["OICD_DOMAIN"] = original_value
