"""
Exceptions and custom handlers for the CLI.
"""

from functools import wraps

import buzz
import typer
from loguru import logger
from rich import traceback
from rich.console import Console
from rich.panel import Panel

from lm_cli.config import OV_CONTACT
from lm_cli.text_tools import dedent, unwrap


# Enables prettified traceback printing via rich
traceback.install()


class LicenseManagerCliError(buzz.Buzz):
    """
    A generic exception base class to use in License Manager CLI.
    """


class Abort(LicenseManagerCliError):
    """
    A special exception used to abort the License Manager CLI.

    Collects information provided for use in the ``handle_abort`` context manager.
    """

    def __init__(
        self,
        message,
        *args,
        subject=None,
        support=False,
        log_message=None,
        original_error=None,
        warn_only=False,
        **kwargs,
    ):
        """
        Initialize the Abort errror.
        """
        self.subject = subject
        self.support = support
        self.log_message = log_message
        self.original_error = original_error
        self.warn_only = warn_only
        super().__init__(message, *args, **kwargs)


def handle_abort(func):
    """
    Apply a decorator to gracefully handle any Abort errors that happen within the context.

    Will log the error, show a helpful message to the user about the error, and exit.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Abort as err:
            if not err.warn_only:
                if err.log_message is not None:
                    logger.error(err.log_message)

                if err.original_error is not None:
                    logger.error(f"Original exception: {err.original_error}")

            panel_kwargs = dict()
            if err.subject is not None:
                panel_kwargs["title"] = f"[red]{err.subject}"
            message = dedent(err.message)
            if err.support:
                support_message = unwrap(
                    f"""
                    [yellow]If the problem persists,
                    please contact [bold]{OV_CONTACT}[/bold]
                    for support and trouble-shooting
                    """
                )
                message = f"{message}\n\n{support_message}"

            console = Console()
            console.print()
            console.print(Panel(message, **panel_kwargs))
            console.print()
            raise typer.Exit(code=1)

    return wrapper
