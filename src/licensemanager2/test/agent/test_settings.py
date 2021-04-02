"""
Test the environment parser the creates SETTINGS
"""
import os
from unittest.mock import patch

from pytest import fixture, raises

from licensemanager2.agent import settings


@fixture
def good_env():
    """
    A parseable environment
    """
    env = {"LM2_AGENT_BACKEND_BASE_URL": "http://hello/"}
    with patch.dict(os.environ, env) as e:
        yield e


@fixture
def bad_env():
    """
    An unparseable environment
    """
    env = {"LM2_AGENT_BACKEND_BASE_URL": "ftp://hello/"}
    with patch.dict(os.environ, env) as e:
        yield e


def test_init_settings(good_env):
    """
    Do we build a settings object from good input?
    """
    good = settings.init_settings()
    assert good.BACKEND_BASE_URL == good_env["LM2_AGENT_BACKEND_BASE_URL"]


def test_init_settings_bad(bad_env, caplog):
    """
    Do we bail out when bad settings?
    """
    with raises(SystemExit):
        settings.init_settings()
    assert (
        len(caplog.messages) == 1
        and "value_error.str.regex; pattern=http" in caplog.text
    )
