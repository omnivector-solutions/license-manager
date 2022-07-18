"""
A ``typer`` app that can interact with Licenses endpoint to list data.
"""

from typing import Any, Dict, List, Optional, cast

import typer

from lm_cli.constants import SortOrder
from lm_cli.exceptions import handle_abort
from lm_cli.render import StyleMapper, render_list_results
from lm_cli.requests import make_request
from lm_cli.schemas import LicenseManagerContext


style_mapper = StyleMapper(
    product_feature="green",
    used="cyan",
    total="magenta",
    available="yellow",
)


app = typer.Typer(help="Commands to interact with licenses.")


@app.command("list")
@handle_abort
def list_all(
    ctx: typer.Context,
    search: Optional[str] = typer.Option(None, help="Apply a search term to results."),
    sort_order: SortOrder = typer.Option(SortOrder.UNSORTED, help="Specify sort order."),
    sort_field: Optional[str] = typer.Option(None, help="The field by which results should be sorted."),
):
    """
    Show license usage information.
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
            "/license/all",
            "GET",
            expected_status=200,
            abort_message="Couldn't retrieve license list from API",
            support=True,
            params=params,
        ),
    )

    render_list_results(
        data,
        title="Licenses List",
        style_mapper=style_mapper,
    )
