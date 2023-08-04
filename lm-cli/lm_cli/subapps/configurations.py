"""
A ``typer`` app that can interact with Configurations data in a cruddy manner.
"""

from typing import Dict, List, Optional, cast

import typer

from lm_cli.constants import LicenseServerType, SortOrder
from lm_cli.exceptions import handle_abort
from lm_cli.render import StyleMapper, render_list_results, render_single_result, terminal_message
from lm_cli.requests import make_request, parse_query_params
from lm_cli.schemas import ConfigurationCreateSchema, LicenseManagerContext


style_mapper = StyleMapper(
    id="blue",
    name="green",
    cluster_client_id="cyan",
    features="red",
    license_servers="white",
    grace_time="magenta",
    type="yellow",
)


app = typer.Typer(help="Commands to interact with configurations.")


def format_data(data):
    """Return data in the correct format for printing."""
    formatted_data = []

    for configuration in data:
        new_data = {}

        new_data["id"] = configuration["id"]
        new_data["name"] = configuration["name"]
        new_data["cluster_client_id"] = configuration["cluster_client_id"]
        new_data["features"] = ", ".join([feature["name"] for feature in configuration["features"]])
        new_data["license_servers"] = ", ".join(
            [
                f"{license_server['host']}:{license_server['port']}"
                for license_server in configuration["license_servers"]
            ]
        )
        new_data["grace_time"] = f"{configuration['grace_time']} (seconds)"
        new_data["type"] = configuration["type"]

        formatted_data.append(new_data)

    return formatted_data


@app.command("list")
@handle_abort
def list_all(
    ctx: typer.Context,
    search: Optional[str] = typer.Option(None, help="Apply a search term to results."),
    sort_order: SortOrder = typer.Option(SortOrder.UNSORTED, help="Specify sort order."),
    sort_field: Optional[str] = typer.Option(None, help="The field by which results should be sorted."),
):
    """
    Show configuration information.
    """
    lm_ctx: LicenseManagerContext = ctx.obj

    # Make static type checkers happy
    assert lm_ctx is not None
    assert lm_ctx.client is not None

    params = parse_query_params(search=search, sort_order=sort_order, sort_field=sort_field)

    data = cast(
        List,
        make_request(
            lm_ctx.client,
            "/lm/configurations",
            "GET",
            expected_status=200,
            abort_message="Couldn't retrieve configuration list from API",
            support=True,
            params=params,
        ),
    )

    formatted_data = format_data(data)

    render_list_results(
        formatted_data,
        title="Configurations List",
        style_mapper=style_mapper,
    )


@app.command("get-one")
@handle_abort
def get_one(
    ctx: typer.Context,
    id: int = typer.Option(int, help="The specific id of the configuration."),
):
    """
    Get a single configuration by id.
    """
    lm_ctx: LicenseManagerContext = ctx.obj

    # Make static type checkers happy
    assert lm_ctx is not None
    assert lm_ctx.client is not None

    result = cast(
        Dict,
        make_request(
            lm_ctx.client,
            f"/lm/configurations/{id}",
            "GET",
            expected_status=200,
            abort_message="Couldn't get the configuration from the API",
            support=True,
        ),
    )

    formatted_result = format_data([result])

    render_single_result(
        formatted_result[0],
        title=f"Configuration id {id}",
    )


@app.command()
@handle_abort
def create(
    ctx: typer.Context,
    name: str = typer.Option(
        ...,
        help="The name of configuration to create.",
    ),
    cluster_client_id: str = typer.Option(
        ...,
        help="The cluster OIDC client_id of the cluster where the configuration is being added.",
    ),
    grace_time: int = typer.Option(
        ...,
        help="The grace time for jobs using the license. Must be in seconds.",
    ),
    license_server_type: LicenseServerType = typer.Option(..., help="The license server type."),
):
    """
    Create a new configuration.
    """
    lm_ctx: LicenseManagerContext = ctx.obj

    # Make static type checkers happy
    assert lm_ctx is not None
    assert lm_ctx.client is not None

    request_data = ConfigurationCreateSchema(
        name=name,
        cluster_client_id=cluster_client_id,
        grace_time=grace_time,
        type=license_server_type,
    )

    make_request(
        lm_ctx.client,
        "/lm/configurations",
        "POST",
        expected_status=201,
        abort_message="Configuration creation failed",
        support=True,
        request_model=request_data,
    )

    terminal_message(
        "The configuration was created successfully.",
        subject="Configuration creation succeeded.",
    )


@app.command()
@handle_abort
def delete(
    ctx: typer.Context,
    id: int = typer.Option(
        ...,
        help="The id of the configuration to delete.",
    ),
):
    """
    Delete an existing configuration.
    """
    lm_ctx: LicenseManagerContext = ctx.obj

    # Make static type checkers happy
    assert lm_ctx is not None
    assert lm_ctx.client is not None

    make_request(
        lm_ctx.client,
        f"/lm/configurations/{id}",
        "DELETE",
        expected_status=200,
        abort_message="Request to delete configuration was not accepted by the API",
        support=True,
    )
    terminal_message(
        "The configuration was deleted successfully.",
        subject="Configuration delete succeeded",
    )
