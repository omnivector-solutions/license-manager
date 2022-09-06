"""
Utilities for handling auth in lm-cli.
"""

from time import sleep
from typing import Dict, Optional, cast

import pydantic
from jose import jwt
from jose.exceptions import ExpiredSignatureError
from loguru import logger

from lm_cli.config import settings
from lm_cli.exceptions import Abort, LicenseManagerCliError
from lm_cli.render import terminal_message
from lm_cli.requests import make_request
from lm_cli.schemas import DeviceCodeData, IdentityData, LicenseManagerContext, Persona, TokenSet
from lm_cli.text_tools import unwrap
from lm_cli.time_loop import TimeLoop


def validate_token_and_extract_identity(token_set: TokenSet) -> IdentityData:
    """
    Validate the access_token from a TokenSet and extract the identity data.

    Validations:
        * Checks if access_token is not empty.
        * Checks timestamp on the access token.
        * Checks for identity data.
        * Checks that all identity elements are present.

    Reports an error in the logs and to the user if there is an issue with the access_token.
    """
    logger.debug("Validating access token.")

    token_file_is_empty = not token_set.access_token
    if token_file_is_empty:
        logger.debug("Access token file exists but it is empty")
        raise Abort(
            """
            Access token file exists but it is empty.

            Please try logging in again.
            """,
            subject="Empty access token file.",
            support=True,
            log_message="Empty access token file.",
        )

    try:
        token_data = jwt.decode(
            token_set.access_token,
            None,
            options=dict(
                verify_signature=False,
                verify_aud=False,
                verify_exp=True,
            ),
        )
    except ExpiredSignatureError:
        raise  # Will be handled in calling context
    except Exception as err:
        raise Abort(
            """
            There was an unknown error while validating the access token.

            Please try logging in again.
            """,
            subject="Invalid access token.",
            support=True,
            log_message=f"Unknown error while validating access access token: {err}.",
            original_error=err,
        )

    logger.debug("Extracting identity data from the access token.")
    user_email = token_data.get(settings.IDENTITY_CLAIMS_KEY)
    identity_claims = {"user_email": user_email}

    Abort.require_condition(
        identity_claims,
        "No identity data found in access token data.",
        raise_kwargs=dict(
            subject="No identity found.",
            support=True,
        ),
    )
    try:
        return IdentityData.parse_obj(identity_claims)
    except pydantic.ValidationError as err:
        raise Abort(
            """
            The identity data in the access token is malformed or incomplete.

            Please try logging in again.
            """,
            subject="Invalid identity data.",
            support=True,
            log_message=f"Identity data is incomplete: {err}.",
        )


def load_tokens_from_cache() -> TokenSet:
    """
    Load an access token (and a refresh token if one exists) from the cache.
    """

    # Make static type checkers happy
    assert settings.LM_API_ACCESS_TOKEN_PATH is not None
    assert settings.LM_API_REFRESH_TOKEN_PATH is not None

    Abort.require_condition(
        settings.LM_API_ACCESS_TOKEN_PATH.exists(),
        "Please login with your auth token first using the `lm-cli login` command.",
        raise_kwargs=dict(subject="You need to login."),
    )

    logger.debug("Retrieving access token from cache.")
    token_set = TokenSet(access_token=settings.LM_API_ACCESS_TOKEN_PATH.read_text())

    if settings.LM_API_REFRESH_TOKEN_PATH.exists():
        logger.debug("Retrieving refresh token from cache.")
        token_set.refresh_token = settings.LM_API_REFRESH_TOKEN_PATH.read_text()

    return token_set


def save_tokens_to_cache(token_set: TokenSet):
    """
    Save tokens from a token_set to the cache.
    """

    # Make static type checkers happy
    assert settings.LM_API_ACCESS_TOKEN_PATH is not None
    assert settings.LM_API_REFRESH_TOKEN_PATH is not None

    logger.debug(f"Caching access token at {settings.LM_API_ACCESS_TOKEN_PATH}")
    settings.LM_API_ACCESS_TOKEN_PATH.write_text(token_set.access_token)

    if token_set.refresh_token is not None:
        logger.debug(f"Caching refresh token at {settings.LM_API_REFRESH_TOKEN_PATH}")
        settings.LM_API_REFRESH_TOKEN_PATH.write_text(token_set.refresh_token)


def clear_token_cache():
    """
    Clears the token cache.
    """
    logger.debug("Clearing cached tokens")

    logger.debug(f"Removing access token at {settings.LM_API_ACCESS_TOKEN_PATH}")
    if settings.LM_API_ACCESS_TOKEN_PATH.exists():
        settings.LM_API_ACCESS_TOKEN_PATH.unlink()

    logger.debug(f"Removing refresh token at {settings.LM_API_REFRESH_TOKEN_PATH}")
    if settings.LM_API_REFRESH_TOKEN_PATH.exists():
        settings.LM_API_REFRESH_TOKEN_PATH.unlink()


def init_persona(ctx: LicenseManagerContext, token_set: Optional[TokenSet] = None):
    """
    Initializes the "persona" which contains the tokens and identity data for a user.

    Retrieves the access token for the user from the cache.

    Token is retrieved from the cache, validated, and identity data is extracted.

    If the access token is expired, a new one will be acquired via the cached refresh token (if there is one).

    Saves token_set to cache.

    Returns the persona.
    """
    if token_set is None:
        token_set = load_tokens_from_cache()

    try:
        identity_data = validate_token_and_extract_identity(token_set)
    except ExpiredSignatureError:
        Abort.require_condition(
            token_set.refresh_token is not None,
            "The auth token is expired. Please retrieve a new and log in again.",
            raise_kwargs=dict(
                subject="Expired access token.",
                support=True,
            ),
        )

        logger.debug("The access token is expired. Attempting to refresh token.")
        refresh_access_token(ctx, token_set)
        identity_data = validate_token_and_extract_identity(token_set)

    logger.debug(f"Persona created with identity data: {identity_data}.")

    save_tokens_to_cache(token_set)

    return Persona(
        token_set=token_set,
        identity_data=identity_data,
    )


def refresh_access_token(ctx: LicenseManagerContext, token_set: TokenSet):
    """
    Attempt to fetch a new access token given a refresh token in a token_set.

    Sets the access token in-place.

    If refresh fails, notify the user that they need to log in again.
    """
    url = f"https://{settings.OIDC_DOMAIN}/protocol/openid-connect/token"
    logger.debug(f"Requesting refreshed access token from {url}")

    LicenseManagerCliError.require_condition(
        ctx.client is not None,
        "Attempted to refresh with a null client. This should not happen.",
    )

    # Make static type-checkers happy
    assert ctx.client is not None

    refreshed_token_set = cast(
        TokenSet,
        make_request(
            ctx.client,
            "/protocol/openid-connect/token",
            "POST",
            abort_message="The auth token could not be refreshed. Please try logging in again.",
            abort_subject="EXPIRED ACCESS TOKEN.",
            support=True,
            response_model_cls=TokenSet,
            data=dict(
                client_id=settings.OIDC_CLIENT_ID,
                audience=settings.OIDC_AUDIENCE,
                grant_type="refresh_token",
                refresh_token=token_set.refresh_token,
            ),
        ),
    )

    token_set.access_token = refreshed_token_set.access_token


def fetch_auth_tokens(ctx: LicenseManagerContext) -> TokenSet:
    """
    Fetch an access token (and possibly a refresh token) from OIDC provider.

    Prints out a URL for the user to use to authenticate and polls the token endpoint to fetch it when
    the browser-based process finishes.
    """
    # Make static type-checkers happy
    assert ctx.client is not None

    device_code_data = cast(
        DeviceCodeData,
        make_request(
            ctx.client,
            "/protocol/openid-connect/auth/device",
            "POST",
            expected_status=200,
            abort_message="There was a problem retrieving a device verification code from the auth provider",
            abort_subject="COULD NOT RETRIEVE TOKEN.",
            support=True,
            response_model_cls=DeviceCodeData,
            data=dict(
                client_id=settings.OIDC_CLIENT_ID,
                grant_type="client_credentials",
                audience=settings.OIDC_AUDIENCE,
                client_secret=settings.OIDC_CLIENT_SECRET,
            ),
        ),
    )

    terminal_message(
        f"""
        To complete login, please open the following link in a browser:

          {device_code_data.verification_uri_complete}

        Waiting up to {settings.OIDC_MAX_POLL_TIME / 60} minutes for you to complete the process...
        """,
        subject="Waiting for login",
    )

    for tick in TimeLoop(
        settings.OIDC_MAX_POLL_TIME,
        message="Waiting for web login.",
    ):

        response_data = cast(
            Dict,
            make_request(
                ctx.client,
                "/protocol/openid-connect/token",
                "POST",
                abort_message="There was a problem retrieving a device verification code from the auth provider",
                abort_subject="COULD NOT FETCH ACCESS TOKEN.",
                support=True,
                data=dict(
                    grant_type="urn:ietf:params:oauth:grant-type:device_code",
                    device_code=device_code_data.device_code,
                    client_id=settings.OIDC_CLIENT_ID,
                    client_secret=settings.OIDC_CLIENT_SECRET,
                ),
            ),
        )
        if "error" in response_data:
            if response_data["error"] == "authorization_pending":
                logger.debug(f"Token fetch attempt #{tick.counter} failed.")
                sleep(device_code_data.interval)
            else:
                # TODO: Test this failure condition
                raise Abort(
                    unwrap(
                        """
                        There was a problem retrieving a device verification code from the auth provider:
                        Unexpected failure retrieving access token.
                        """
                    ),
                    subject="Unexpected error",
                    support=True,
                    log_message=f"Unexpected error response: {response_data}",
                )
        else:
            return TokenSet(**response_data)

    raise Abort(
        "Login process was not completed in time. Please try again.",
        subject="Timed out.",
        log_message="Timed out while waiting for user to complete login.",
    )
