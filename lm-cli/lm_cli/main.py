"""
Entry point for the License Manager CLI App.
"""

from typing import Optional

import httpx
import importlib_metadata
import jose
import typer

from lm_cli.auth import clear_token_cache, fetch_auth_tokens, init_persona, load_tokens_from_cache
from lm_cli.config import settings
from lm_cli.exceptions import Abort, handle_abort
from lm_cli.logs import init_logs
from lm_cli.render import render_json, terminal_message
from lm_cli.schemas import LicenseManagerContext, Persona, TokenSet
from lm_cli.subapps.bookings import app as bookings_app
from lm_cli.subapps.configurations import app as configurations_app
from lm_cli.subapps.licenses import app as licenses_app
from lm_cli.text_tools import conjoin, copy_to_clipboard


app = typer.Typer()

app.add_typer(licenses_app, name="licenses")
app.add_typer(bookings_app, name="bookings")
app.add_typer(configurations_app, name="configurations")


@app.callback(invoke_without_command=True)
@handle_abort
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, help="Enable verbose logging to the terminal"),
    version: bool = typer.Option(False, help="Print the version of lm-cli and exit"),
):
    """
    Welcome to the License Manager CLI!

    More information can be shown for each command listed below by running it with the --help option.
    """
    if version:
        typer.echo(importlib_metadata.version("lm-cli"))
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        terminal_message(
            conjoin(
                "No command provided. Please check the [bold magenta]usage[/bold magenta] and add a command",
                "",
                f"[yellow]{ctx.get_help()}[/yellow]",
            ),
            subject="Need a License Manager CLI command.",
        )
        raise typer.Exit()

    init_logs(verbose=verbose)
    persona = None

    client = httpx.Client(
        base_url=f"https://{settings.OIDC_LOGIN_DOMAIN}",
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    context = LicenseManagerContext(persona=None, client=client)

    if ctx.invoked_subcommand not in ("login", "logout"):
        persona = init_persona(context)
        context.client = httpx.Client(
            base_url=settings.LM_API_ENDPOINT,
            headers=dict(Authorization=f"Bearer {persona.token_set.access_token}"),
        )
        context.persona = persona

    ctx.obj = context


@app.command()
@handle_abort
def login(ctx: typer.Context):
    """
    Log in to the lm-cli by storing the supplied token argument in the cache.
    """
    token_set: TokenSet = fetch_auth_tokens(ctx.obj)
    persona: Persona = init_persona(ctx.obj, token_set)
    terminal_message(
        f"User was logged in with email '{persona.identity_data.user_email}'",
        subject="Logged in!",
    )


@app.command()
@handle_abort
def logout():
    """
    Log out of the lm-cli.
    """
    clear_token_cache()
    terminal_message(
        "User was logged out.",
        subject="Logged out.",
    )


@app.command()
@handle_abort
def show_token(
    plain: bool = typer.Option(
        False,
        help="Show the token in plain text.",
    ),
    refresh: bool = typer.Option(
        False,
        help="Show the refresh token instead of the access token.",
    ),
    show_prefix: bool = typer.Option(
        False,
        "--prefix",
        help="Include the 'Bearer' prefix in the output.",
    ),
    show_header: bool = typer.Option(
        False,
        "--header",
        help="Show the token as it would appear in a request header.",
    ),
    decode: bool = typer.Option(
        False,
        "--decode",
        help="Show the content of the decoded access token.",
    ),
):
    """
    Show the token for the logged in user.

    Token output is automatically copied to your clipboard.
    """
    token_set: TokenSet = load_tokens_from_cache()
    token: Optional[str]
    if not refresh:
        token = token_set.access_token
        subject = "Access Token"
        Abort.require_condition(
            token is not None,
            "User is not logged in. Please log in first.",
            raise_kwargs=dict(
                subject="Not logged in.",
            ),
        )
    else:
        token = token_set.refresh_token
        subject = "Refresh Token."
        Abort.require_condition(
            token is not None,
            "User is not logged in or does not have a refresh token. Please try loggin in again.",
            raise_kwargs=dict(
                subject="No refresh token.",
            ),
        )

    if decode:
        # Decode the token with ALL verification turned off (we just want to unpack it)
        content = jose.jwt.decode(
            token,
            "secret-will-be-ignored",
            options=dict(
                verify_signature=False,
                verify_aud=False,
                verify_iat=False,
                verify_exp=False,
                verify_nbf=False,
                verify_iss=False,
                verify_sub=False,
                verify_jti=False,
                verify_at_hash=False,
            ),
        )
        render_json(content)
        return

    if show_header:
        token_text = f"""{{ "Authorization": "Bearer {token}" }}"""
    else:
        prefix = "Bearer " if show_prefix else ""
        token_text = f"{prefix}{token}"

    on_clipboard = copy_to_clipboard(token_text)

    if plain:
        print(token_text)
    else:
        kwargs = dict(subject=subject, indent=False)
        if on_clipboard:
            kwargs["footer"] = "The output was copied to your clipboard."

        terminal_message(token_text, **kwargs)
