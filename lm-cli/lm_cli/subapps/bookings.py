"""
A ``typer`` app that can interact with Bookings endpoint to list data.
"""

from typing import List, Optional, cast

import typer

from lm_cli.constants import SortOrder
from lm_cli.exceptions import handle_abort
from lm_cli.render import StyleMapper, render_list_results
from lm_cli.requests import make_request, parse_query_params
from lm_cli.schemas import LicenseManagerContext


style_mapper = StyleMapper(
    id="blue",
    job_id="white",
    product_feature="green",
    booked="cyan",
    config_id="magenta",
    lead_host="white",
    user_name="red",
    cluster_name="yellow",
)


app = typer.Typer(help="Commands to interact with bookings.")


@app.command("list")
@handle_abort
def list_all(
    ctx: typer.Context,
    search: Optional[str] = typer.Option(None, help="Apply a search term to results."),
    sort_order: SortOrder = typer.Option(SortOrder.UNSORTED, help="Specify sort order."),
    sort_field: Optional[str] = typer.Option(None, help="The field by which results should be sorted."),
):
    """
    Show booking information.
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
            "/booking/all",
            "GET",
            expected_status=200,
            abort_message="Couldn't retrieve booking list from API",
            support=True,
            params=params,
        ),
    )

    render_list_results(
        data,
        title="Bookings List",
        style_mapper=style_mapper,
    )
