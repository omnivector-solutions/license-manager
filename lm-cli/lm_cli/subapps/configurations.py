"""
Provide a ``typer`` app that can interact with Configurations data in a cruddy manner.
"""

from typing import Any, Dict, List, Optional, cast

import typer

from lm_cli.constants import SortOrder
from lm_cli.exceptions import handle_abort
from lm_cli.render import StyleMapper, render_list_results, render_single_result, terminal_message
from lm_cli.requests import make_request
from lm_cli.schemas import ConfigurationCreateRequestData, LicenseManagerContext
from lm_cli.text_tools import dedent


style_mapper = StyleMapper(
    id="blue",
    name="green",
    product="cyan",
    features="magenta",
    license_servers="yellow",
    license_server_type="white",
    grace_time="red",
)


app = typer.Typer(help="Commands to interact with configurations")


@app.command("list")
@handle_abort
def list_all(
    ctx: typer.Context,
    search: Optional[str] = typer.Option(None, help="Apply a search term to results"),
    sort_order: SortOrder = typer.Option(SortOrder.UNSORTED, help="Specify sort order"),
    sort_field: Optional[str] = typer.Option(None, help="The field by which results should be sorted"),
):
    """
    Show configuration information
    """
    lm_ctx: LicenseManagerContext = ctx.obj

    # Make static type checkers happy
    assert lm_ctx is not None
    assert lm_ctx.client is not None

    params: Dict[str, Any] = dict()

    if search is not None:
        params["search"] = search
    if sort_order is not SortOrder.UNSORTED:
        params["sort_ascending"] = SortOrder is SortOrder.ASCENDING
    if sort_field is not None:
        params["sort_field"] = sort_field

    data = cast(
        List,
        make_request(
            lm_ctx.client,
            "/config/all",
            "GET",
            expected_status=200,
            abort_message="Couldn't retrieve configuration list from API",
            support=True,
            params=params,
        ),
    )

    render_list_results(
        data,
        title=" Configurations List",
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
            f"/config/{id}",
            "GET",
            expected_status=200,
            abort_message="Couldn't get the configuration from the API",
            support=True,
        ),
    )

    render_single_result(
        result,
        title=f"Configuration id {id}",
    )


@app.command()
@handle_abort
def create(
    ctx: typer.Context,
    id: int = typer.Option(..., help="The id of the configuration to create."),
    name: str = typer.Option(
        ...,
        help="The name of configuration to create.",
    ),
    product: str = typer.Option(
        ...,
        help="The name of the product of the license.",
    ),
    features: str = typer.Option(
        ...,
        help="The features of the license and the quantity. Must be a string with a valid JSON object serialized.",
    ),
    license_servers: str = typer.Option(
        ...,
        help=dedent(
            """
            The list of license servers connection strings, in order of preference.
            Must be in the format <license_server_type>:<hostname>:<port>.
            Use commas to concatenate in case there's more than one entry.
            """
        ),
    ),
    license_server_type: str = typer.Option(..., help="The license server type."),
    grace_time: int = typer.Option(
        ...,
        help="The grace time for jobs using the license. Must be in seconds.",
    ),
):
    """
    Create a new configuration.
    """
    lm_ctx: LicenseManagerContext = ctx.obj

    # Make static type checkers happy
    assert lm_ctx is not None
    assert lm_ctx.client is not None

    request_data = ConfigurationCreateRequestData(
        id=id,
        name=name,
        product=product,
        features=features,
        license_servers=license_servers,
        license_server_type=license_server_type,
        grace_time=grace_time,
    )

    make_request(
        lm_ctx.client,
        "/config/",
        "POST",
        expected_status=200,
        abort_message="Couldn't create configuration",
        support=True,
        request_model=request_data,
    )

    terminal_message(
        "The configuration was created successfully.",
        subject="Configuration creation succeeded",
    )


@app.command()
@handle_abort
def delete(
    ctx: typer.Context,
    id: int = typer.Option(
        ...,
        help="The id of the configuration to delete",
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
        f"/config/{id}",
        "DELETE",
        expected_status=200,
        abort_message="Request to delete configuration was not accepted by the API",
        support=True,
    )
    terminal_message(
        "The configuration was successfully deleted.",
        subject="Configuration delete succeeded",
    )
