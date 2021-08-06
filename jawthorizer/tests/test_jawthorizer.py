"""
Test the authorizer lambda that checks api gateway tokens
"""
from unittest.mock import patch

from botocore.exceptions import ClientError
from pytest import fixture, mark

import jawthorizer


@fixture
def some_method_arn():
    """
    A handy method ARN
    """
    return "arn:aws:us-west-2:asdfasdfasdf:idc:/testy/PATCH/lots/of/path"


@fixture
def patched_settings():
    """
    Set up a specific Settings object for these tests
    """
    env = {
        "JAWTHORIZER_APP_SHORT_NAME": "unit-testing",
        "JAWTHORIZER_STAGE": "edgy",
        "JAWTHORIZER_REGION": "us-west-19",
        "JAWTHORIZER_ALLOWED_SUBS": "roland roland::*",
    }
    stngs = jawthorizer.Settings(env)
    with patch.object(jawthorizer, "SETTINGS", stngs) as s:
        yield s


@fixture
def token_from_settings():
    """
    A token based on these settings
    """
    return (
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9."
        "eyJzdWIiOiJyb2xhbmQ6Om9mLWdpbGVhZCIsImlzcyI6InVuaXQtdGVzdGluZzo6ZWRneTo6dXMtd2VzdC0xOSJ9."
        "BdBScGFX9qGTXYvsFIuERSO9kh0kenPROJCHtKUer_g"
    )


@fixture
def token_from_settings_bad():
    """
    A token based on these settings, but bad
    """
    return (
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9."
        "eyJzdWIiOiJ0aGUtbWFuLWluLWJsYWNrIiwiaXNzIjoidW5pdC10ZXN0aW5nOjplZGd5Ojp1cy13ZXN0LTE5In0."
        "jkRmG717OiUBVhLGLN-nkWpydP4Cdv01ak7WvPp5mac"
    )


@fixture
def patched_botoclient():
    """
    Sub out the boto3 client for secretsmanager
    """
    with patch.object(jawthorizer.boto3, "client", autospec=True) as cli:
        cli.return_value.get_secret_value.return_value = {
            "SecretString": "asdfasdfasdf"
        }
        yield cli


@fixture
def patched_botoclient_bad():
    """
    Sub out the boto3 client for secretsmanager and raise ClientError
    """
    with patch.object(jawthorizer.boto3, "client", autospec=True) as cli:
        err_response = {"Error": {"Code": "oopsies", "Message": "oopsies woopsies"}}
        err = ClientError(err_response, "GetSecretValue")
        cli.return_value.get_secret_value.side_effect = err
        yield cli


def test_get_token_secret(patched_botoclient):
    """
    Do we get a secret?
    """
    sec = jawthorizer.get_token_secret()
    assert sec == "asdfasdfasdf"


def test_get_secret_error(patched_botoclient_bad):
    """
    Do we correctly handle a failure to get a secret?
    """
    assert jawthorizer.get_token_secret() is None


@mark.parametrize(
    "sub,iss,expected",
    [
        ("evil", "evil::issuer", False),
        ("roland", "evil::issuer", False),
        ("evil", "unit-testing::edgy::us-west-19", False),
        ("roland::deschain", "unit-testing::edgy::us-west-19", True),
    ],
)
def test_check_claims(sub, iss, expected, patched_settings):
    """
    Do I pass a good JWT payload and fail a bad one?
    """
    actual = jawthorizer.check_claims(dict(sub=sub, iss=iss))
    assert actual == expected


def test_fix_method_arn(some_method_arn):
    """
    Do I correct a specific method to permit a generic method?
    """
    assert (
        jawthorizer._fix_method_arn(some_method_arn)
        == "arn:aws:us-west-2:asdfasdfasdf:idc:/testy/*"
    )


def test_handler(
    patched_settings,
    some_method_arn,
    token_from_settings,
    token_from_settings_bad,
    patched_botoclient,
):
    """
    Does it handle?
    """
    fixed = "arn:aws:us-west-2:asdfasdfasdf:idc:/testy/*"
    OK = jawthorizer.policy(fixed, True)
    BAD = jawthorizer.policy(fixed, False)
    context = {}

    # cloudwatch ping
    event = {"hello": 1}
    assert jawthorizer.handler(event, context) == {}

    # invalid authorization header
    event = {
        "methodArn": some_method_arn,
        "authorizationToken": "bear rawr",
    }
    assert jawthorizer.handler(event, context) == BAD

    # invalid token
    event = {
        "methodArn": some_method_arn,
        "authorizationToken": "bearer asdfasdf.asdf.asdf",
    }
    assert jawthorizer.handler(event, context) == BAD

    # bad claims
    event = {
        "methodArn": some_method_arn,
        "authorizationToken": f"bearer {token_from_settings_bad}",
    }
    assert jawthorizer.handler(event, context) == BAD

    # good
    event = {
        "methodArn": some_method_arn,
        "authorizationToken": f"bearer {token_from_settings}",
    }
    assert jawthorizer.handler(event, context) == OK


def test_handler_missing_secret(
    patched_settings, some_method_arn, patched_botoclient_bad
):
    """
    Confirm a failure, when the problem is the secret is missing
    """
    fixed = "arn:aws:us-west-2:asdfasdfasdf:idc:/testy/*"
    event = {
        "methodArn": some_method_arn,
        "authorizationToken": "bear rawr",
    }
    BAD = jawthorizer.policy(fixed, False)

    assert jawthorizer.handler(event, {}) == BAD
