"""
Confirmation of the permitting API
"""
from datetime import datetime
from unittest.mock import patch

from botocore.exceptions import ClientError
from click import ClickException
from click.testing import CliRunner
import jwt
from pytest import fixture, mark, raises

from licensemanager2.backend import createjwt


SECRET = "q354809hreuinjvm "


@fixture
def runner():
    """
    A runner for the click-based command-line
    """
    return CliRunner()


@mark.freeze_time("2021-03-12T17:33Z")
def test_create_timed_token():
    """
    Do I generate a sensible output or error for various calls
    """
    # no duration
    tok1 = createjwt.create_timed_token(
        sub="myuser", iss="xxx::xxxx", secret=SECRET, duration=None
    )
    assert jwt.decode(tok1, SECRET, algorithms=createjwt.JWT_ALGO) == {
        "iss": "xxx::xxxx",
        "sub": "myuser",
    }

    # default duration
    tok2 = createjwt.create_timed_token(
        sub="myuser", iss="xxx::xxxx", secret=SECRET, duration=600
    )
    assert jwt.decode(tok2, SECRET, algorithms=createjwt.JWT_ALGO) == {
        "iss": "xxx::xxxx",
        "sub": "myuser",
        "exp": 1615570980,
    }

    # different algorithm
    tok3 = createjwt.create_timed_token(
        sub="myuser", iss="xxx::xxxx", secret=SECRET, algorithm="HS512", duration=600
    )
    assert jwt.decode(tok3, SECRET, algorithms=["HS512"]) == {
        "iss": "xxx::xxxx",
        "sub": "myuser",
        "exp": 1615570980,
    }

    # missing SECRET
    with raises(TypeError):
        createjwt.create_timed_token(sub="myuser", iss="xxx::xxxx", secret="")

    # missing sub
    with raises(TypeError):
        createjwt.create_timed_token(sub="", iss="xxx::xxxx", secret=SECRET)


def test_validate_token():
    """
    Do valid tokens pass our validator function? Also invalid tokens, not pass
    """
    sub = "myuser"

    # token without an expiration, so it should validate
    tok1 = b"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJteXVzZXIifQ.4agU_-BTje86l4JtbRdvLwTI9cHgKJ0Asg-hftuZUEM"
    assert createjwt.validate_token(tok1, iss="xxx:xxxx", secret=SECRET)["sub"] == sub

    # token we created, with expiration of 10 minutes
    tok2 = createjwt.create_timed_token(
        sub, iss="xxx:xxxx", secret=SECRET, duration=600
    )
    payload2 = createjwt.validate_token(tok2, iss="xxx:xxxx", secret=SECRET)
    assert payload2["sub"] == sub
    assert "exp" in payload2

    # expired token (no default, raise an exception)
    tok3 = jwt.encode(
        {"sub": sub, "exp": datetime(year=1970, month=1, day=1)},
        SECRET,
        algorithm="HS256",
    )
    with raises(jwt.exceptions.ExpiredSignatureError):
        createjwt.validate_token(tok3, SECRET)

    _my_default = object()

    # correct token, incorrect secret
    secretx = SECRET[:-2]
    assert createjwt.validate_token(tok2, secretx, _my_default) is _my_default

    # token is None
    assert createjwt.validate_token(None, SECRET, _my_default) is _my_default


@fixture
def patched_botoclient():
    """
    Sub out the boto3 client for secretsmanager
    """
    with patch.object(createjwt.boto3, "client", autospec=True) as cli:
        cli.return_value.get_secret_value.return_value = {
            "SecretString": "asdfasdfasdf"
        }
        yield cli


@fixture
def patched_botoclient_bad():
    """
    Sub out the boto3 client for secretsmanager and raise ClientError
    """
    with patch.object(createjwt.boto3, "client", autospec=True) as cli:
        err_response = {"Error": {"Code": "oopsies", "Message": "oopsies woopsies"}}
        err = ClientError(err_response, "GetSecretValue")
        cli.return_value.get_secret_value.side_effect = err
        yield cli


def test_get_secret(patched_botoclient):
    """
    Do we get a secret?
    """
    sec = createjwt.get_secret("hello-world", "tester", "us-west-2")
    assert sec == "asdfasdfasdf"


def test_get_secret_error(patched_botoclient_bad):
    """
    Do we correctly handle a failure to get a secret?
    """
    with raises(ClickException):
        createjwt.get_secret("hello-world", "tester", "us-west-2")


def test_main(runner: CliRunner, patched_botoclient):
    """
    Does the command line parse args correctly and generate the token we expect
    """
    result = runner.invoke(
        createjwt.main,
        "--sub hello "
        "--sub2 world "
        "--app-short-name helloworld "
        "--stage tester "
        "--region us-west-2",
    )
    expected_token = (
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"
        ".eyJzdWIiOiJoZWxsbzo6d29ybGQiLCJpc3MiOiJoZWxsb3dvcmxkOjp0ZXN0ZXI6OnVzLXdlc3QtMiJ9"
        ".6pq9yaJZ5Lw-WQDfEe17yOMR7Dv5B1O8Culjaqr6kuM"
    )
    assert result.output.strip() == expected_token, result.output
