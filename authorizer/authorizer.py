"""
A custom (lambda) authorizer for API gateway
"""
from fnmatch import fnmatch
import logging
import os
import re
from typing import Optional

import boto3
from botocore.exceptions import ClientError
import jwt


logger = logging.getLogger("authorizer")
logger.setLevel(logging.DEBUG)


JWT_ALGO = ("HS256",)

APP_SHORT_NAME = os.environ["AUTHORIZER_APP_SHORT_NAME"]
STAGE = os.environ["AUTHORIZER_STAGE"]
REGION = os.environ["AUTHORIZER_REGION"]
# by default, allow any sub claim; security, in that case, is based on the token secret alone.
ALLOWED_SUBS = os.getenv("AUTHORIZER_ALLOWED_SUBS", "*").split()

SECRET_NAME = f"/{APP_SHORT_NAME}/{STAGE}/token-secret"
ALLOWED_ISSUER = f"{APP_SHORT_NAME}::{STAGE}::{REGION}"


def _check_sub(sub) -> bool:
    """
    T/F; does a token's `sub' claim match this authorizer's allowed list

    This uses glob-style matching so that, for example:

    - given: AUTHORIZER_ALLOWED_SUBS="myuser myuser::*"
    - this will permit a sub claim of "myuser::myorg" as well as just "myuser" by itself
    """
    return any(fnmatch(sub, item) for item in ALLOWED_SUBS)


def _check_iss(iss) -> bool:
    """
    T/F; does a token's `iss' claim match the deployed app we are the authorizer for
    """
    return iss == ALLOWED_ISSUER


def check_claims(payload: dict) -> bool:
    """
    T/F do all the claims in the token match the required claims we have configured
    """
    ret = True
    sub = payload["sub"]
    iss = payload["iss"]

    if not _check_sub(sub):
        logger.error(f"payload sub not allowed: {sub!r} not in {ALLOWED_SUBS}")
        ret = False

    if not _check_iss(iss):
        logger.error(f"payload iss does not match: {iss!r} != {ALLOWED_ISSUER!r}")
        ret = False

    return ret


def get_token_secret() -> Optional[str]:
    """
    Fetch the token secret value from its storage in aws secretsmanager
    """
    client = boto3.client("secretsmanager")
    try:
        sec = client.get_secret_value(SecretId=SECRET_NAME)["SecretString"]
    except ClientError as e:
        error = e.response["Error"]
        logger.error(
            f"** ERROR FETCHING {SECRET_NAME} in {client.meta.region_name}: ({error['Code']}) {error['Message']}"
        )
        sec = None

    return sec


def _fix_method_arn(methodArn: str):
    """
    From a methodArn, replace the full path to an API GW resource w/ a wildcard path

    When we return a permissions policy we would *prefer* to send back
    "Allow" for only the exact method being requested. But authorizers seem
    to cache return values no matter what the cache setting, which means
    requests after the first one get the wrong permission UNLESS we send back
    a wildcard to all resources.
    """
    l, r = methodArn.rsplit(":", 1)
    id, stage, method, path = r.split("/", 3)
    return f"{l}:{id}/{stage}/*"


def handler(event: dict, context: dict) -> dict:
    """
    Check the Authorization JWT; permit API Gateway access if the token is valid

    This also checks the sub and iss claims before granting permission.
    """
    if not event.get("methodArn"):
        logger.info("☁️ ☁️ ☁️ cloudwatch keep-warm ping ☁️ ☁️ ☁️")
        return {}

    for k in event:
        logger.info(f"{k}: {event[k]}")

    arn = _fix_method_arn(event["methodArn"])

    sec = get_token_secret()
    if not sec:
        return deny(arn)

    if not re.match(r"bearer .+\..+\..+$", event["authorizationToken"], re.I):
        logger.error(f"invalid authorization header: {event['authorizationToken']}")
        return deny(arn)
    token = event["authorizationToken"][7:]

    payload = validate_token(token, sec)
    if not payload or not check_claims(payload):
        return deny(arn)

    return allow(arn)


def deny(arn):
    logger.error(f"❌ denied for: {arn}")
    return policy(arn, permitted=False)


def allow(arn):
    logger.info(f"✔️ permitted for: {arn}")
    return policy(arn, permitted=True)


def policy(arn: str, permitted: bool = False) -> dict:
    return {
        "principalId": "user",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow" if permitted else "Deny",
                    "Resource": arn,
                }
            ],
        },
    }


def validate_token(token: str, secret: str, **kwargs) -> Optional[dict]:
    """
    Check a token signature and claims, and return the userid string (`sub` claim) or the supplied default
    If no default is passed in, this raises any exceptions that occur during token decode
    """
    kwargs.setdefault("algorithms", [JWT_ALGO[0]])
    try:
        payload = jwt.decode(token, secret, **kwargs)
    except jwt.PyJWTError as e:
        logger.error(f"** Token error: {e}")
        return None

    return payload
