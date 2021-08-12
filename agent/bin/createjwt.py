import typing
import click

from lm_agent.token import get_secret, create_timed_token


# TODO: Convert this to a typer cli
@click.command()
@click.option(
    "--subject",
    "--sub",
    help="Name of the subject this token identifies",
    required=True,
)
@click.option(
    "--sub2",
    help="(optional) more specific identifier such as cluster name or org unit",
)
@click.option("--app-short-name", help="e.g. license-manager", required=True)
@click.option("--stage", help="e.g. prod, staging, edge, or custom", required=True)
@click.option("--region", help="e.g. us-west-2", required=True)
@click.option(
    "--duration",
    help="(optional) Duration in seconds; no expiration if unspecified",
    type=int,
)
def main(
    subject: str,
    sub2: typing.Optional[str],
    app_short_name: str,
    stage: str,
    region: str,
    duration: typing.Optional[int],
):
    sec = get_secret(app_short_name, stage, region)
    sub = f"{subject}::{sub2}" if sub2 else subject
    iss = f"{app_short_name}::{stage}::{region}"
    token = create_timed_token(sub=sub, iss=iss, secret=sec, duration=duration)
    click.echo(token)
