"""
Test the environment parser the creates SETTINGS
"""
import os
from unittest.mock import patch

from pytest import fixture, raises

from lm_agent.config import init_settings


@fixture
def good_env():
    """
    A parseable environment
    """
    env = {"LM_AGENT_BACKEND_BASE_URL": "http://hello/"}
    with patch.dict(os.environ, env) as e:
        yield e


@fixture
def bad_env():
    """
    An unparseable environment
    """
    env = {"LM_AGENT_BACKEND_BASE_URL": "not-a-url"}
    with patch.dict(os.environ, env) as e:
        yield e


def test_init_settings(good_env):
    """
    Do we build a settings object from good input?
    """
    good = init_settings()
    assert str(good.BACKEND_BASE_URL) == good_env["LM_AGENT_BACKEND_BASE_URL"]


def test_init_settings_bad(bad_env, caplog):
    """
    Do we bail out when bad settings?
    """
    with raises(SystemExit):
        init_settings()
    assert (
        len(caplog.messages) == 1
        and "Input should be a valid URL, relative URL without a base [type=url_parsing, input_value='not-a-url', input_type=str]"
        in caplog.text
    )
