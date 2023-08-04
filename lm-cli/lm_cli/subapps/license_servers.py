"""
A ``typer`` app that can interact with License Servers data in a cruddy manner.
"""

from typing import Dict, List, Optional, cast

import typer

from lm_cli.constants import SortOrder
from lm_cli.exceptions import handle_abort
from lm_cli.render import StyleMapper, render_list_results, render_single_result, terminal_message
from lm_cli.requests import make_request, parse_query_params
from lm_cli.schemas import LicenseManagerContext, LicenseServerCreateSchema


style_mapper = StyleMapper(
    id="blue",
    config_id="green",
    host="cyan",
    port="magenta",
)

app = typer.Typer(help="Commands to interact with license servers.")


@app.command("list")
@handle_abort
def list_all(
    ctx: typer.Context,
    search: Optional[str] = typer.Option(None, help="Apply a search term to results."),
    sort_order: SortOrder = typer.Option(SortOrder.UNSORTED, help="Specify sort order."),
    sort_field: Optional[str] = typer.Option(None, help="The field by which results should be sorted."),
):
    """
    Show license server information.
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
            "/lm/license_servers",
            "GET",
            expected_status=200,
            abort_message="Couldn't retrieve license servers list from API",
            support=True,
            params=params,
        ),
    )

    render_list_results(
        data,
        title="License Servers List",
        style_mapper=style_mapper,
    )


@app.command("get-one")
@handle_abort
def get_one(
    ctx: typer.Context,
    id: int = typer.Option(int, help="The specific id of the license server."),
):
    """
    Get a single license server by id.
    """
    lm_ctx: LicenseManagerContext = ctx.obj

    # Make static type checkers happy
    assert lm_ctx is not None
    assert lm_ctx.client is not None

    result = cast(
        Dict,
        make_request(
            lm_ctx.client,
            f"/lm/license_servers/{id}",
            "GET",
            expected_status=200,
            abort_message="Couldn't get the license server from the API",
            support=True,
        ),
    )

    render_single_result(
        result,
        title=f"License Server id {id}",
    )


@app.command("create")
@handle_abort
def create(
    ctx: typer.Context,
    config_id: int = typer.Option(
        ...,
        help="The config_id of the license server.",
    ),
    host: str = typer.Option(
        ...,
        help="The hostname of the license server.",
    ),
    port: int = typer.Option(
        ...,
        help="The port of the license server.",
    ),
):
    """
    Create a new license server.
    """
    lm_ctx: LicenseManagerContext = ctx.obj

    # Make static type checkers happy
    assert lm_ctx is not None
    assert lm_ctx.client is not None

    request_data = LicenseServerCreateSchema(
        config_id=config_id,
        host=host,
        port=port,
    )

    make_request(
        lm_ctx.client,
        "/lm/license_servers",
        "POST",
        expected_status=201,
        abort_message="License server creation failed",
        support=True,
        request_model=request_data,
    )

    terminal_message(
        "The license server was created successfully.",
        subject="License server creation succeeded.",
    )


@app.command("delete")
@handle_abort
def delete(
    ctx: typer.Context,
    id: int = typer.Option(
        ...,
        help="The id of the license server to delete.",
    ),
):
    """
    Delete an existing license server.
    """
    lm_ctx: LicenseManagerContext = ctx.obj

    # Make static type checkers happy
    assert lm_ctx is not None
    assert lm_ctx.client is not None

    make_request(
        lm_ctx.client,
        f"/lm/license_servers/{id}",
        "DELETE",
        expected_status=200,
        abort_message="Request to delete license server was not accepted by the API",
        support=True,
    )
    terminal_message(
        "The license server was deleted successfully.",
        subject="License server delete succeeded",
    )
