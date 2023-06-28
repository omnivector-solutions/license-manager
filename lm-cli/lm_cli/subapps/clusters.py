"""
A ``typer`` app that can interact with Clusters data in a cruddy manner.
"""

from typing import Dict, List, Optional, cast

import typer

from lm_cli.constants import SortOrder
from lm_cli.exceptions import handle_abort
from lm_cli.render import StyleMapper, render_list_results, render_single_result, terminal_message
from lm_cli.requests import make_request, parse_query_params
from lm_cli.schemas import ClusterCreateSchema, LicenseManagerContext


style_mapper = StyleMapper(
    id="blue",
    name="green",
    client_id="cyan",
    configurations="magenta",
    jobs="yellow",
)


app = typer.Typer(help="Commands to interact with clusters.")


@app.command("list")
@handle_abort
def list_all(
    ctx: typer.Context,
    search: Optional[str] = typer.Option(None, help="Apply a search term to results."),
    sort_order: SortOrder = typer.Option(SortOrder.UNSORTED, help="Specify sort order."),
    sort_field: Optional[str] = typer.Option(None, help="The field by which results should be sorted."),
):
    """
    Show cluster information.
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
            "/lm/clusters/",
            "GET",
            expected_status=200,
            abort_message="Couldn't retrieve clusters list from API",
            support=True,
            params=params,
        ),
    )

    render_list_results(
        data,
        title="Clusters List",
        style_mapper=style_mapper,
    )


@app.command("get-one")
@handle_abort
def get_one(
    ctx: typer.Context,
    id: int = typer.Option(int, help="The specific id of the cluster."),
):
    """
    Get a single cluster by id.
    """
    lm_ctx: LicenseManagerContext = ctx.obj

    # Make static type checkers happy
    assert lm_ctx is not None
    assert lm_ctx.client is not None

    result = cast(
        Dict,
        make_request(
            lm_ctx.client,
            f"/lm/clusters/{id}",
            "GET",
            expected_status=200,
            abort_message="Couldn't get the cluster from the API",
            support=True,
        ),
    )

    render_single_result(
        result,
        title=f"Cluster id {id}",
    )


@app.command("create")
@handle_abort
def create(
    ctx: typer.Context,
    name: str = typer.Option(
        ...,
        help="The name of cluster to create.",
    ),
    client_id: str = typer.Option(
        ...,
        help="The client_id of the cluster.",
    ),
):
    """
    Create a new cluster.
    """
    lm_ctx: LicenseManagerContext = ctx.obj

    # Make static type checkers happy
    assert lm_ctx is not None
    assert lm_ctx.client is not None

    request_data = ClusterCreateSchema(
        name=name,
        client_id=client_id,
    )

    make_request(
        lm_ctx.client,
        "/lm/clusters/",
        "POST",
        expected_status=201,
        abort_message="Cluster creation failed",
        support=True,
        request_model=request_data,
    )

    terminal_message(
        "The cluster was created successfully.",
        subject="Cluster creation succeeded.",
    )


@app.command("delete")
@handle_abort
def delete(
    ctx: typer.Context,
    id: int = typer.Option(
        ...,
        help="The id of the cluster to delete.",
    ),
):
    """
    Delete an existing cluster.
    """
    lm_ctx: LicenseManagerContext = ctx.obj

    # Make static type checkers happy
    assert lm_ctx is not None
    assert lm_ctx.client is not None

    make_request(
        lm_ctx.client,
        f"/lm/clusters/{id}",
        "DELETE",
        expected_status=200,
        abort_message="Request to delete cluster was not accepted by the API",
        support=True,
    )
    terminal_message(
        "The cluster was deleted successfully.",
        subject="Cluster delete succeeded",
    )
