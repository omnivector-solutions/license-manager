"""
A ``typer`` app that can interact with Products data in a cruddy manner.
"""

from typing import Dict, List, Optional, cast

import typer

from lm_cli.constants import SortOrder
from lm_cli.exceptions import handle_abort
from lm_cli.render import StyleMapper, render_list_results, render_single_result, terminal_message
from lm_cli.requests import make_request, parse_query_params
from lm_cli.schemas import LicenseManagerContext, ProductCreateSchema


style_mapper = StyleMapper(
    id="blue",
    name="green",
)


app = typer.Typer(help="Commands to interact with products.")


@app.command("list")
@handle_abort
def list_all(
    ctx: typer.Context,
    search: Optional[str] = typer.Option(None, help="Apply a search term to results."),
    sort_order: SortOrder = typer.Option(SortOrder.UNSORTED, help="Specify sort order."),
    sort_field: Optional[str] = typer.Option(None, help="The field by which results should be sorted."),
):
    """
    Show product information.
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
            "/lm/products",
            "GET",
            expected_status=200,
            abort_message="Couldn't retrieve products list from API",
            support=True,
            params=params,
        ),
    )

    render_list_results(
        data,
        title="Products List",
        style_mapper=style_mapper,
    )


@app.command("get-one")
@handle_abort
def get_one(
    ctx: typer.Context,
    id: int = typer.Option(int, help="The specific id of the product."),
):
    """
    Get a single product by id.
    """
    lm_ctx: LicenseManagerContext = ctx.obj

    # Make static type checkers happy
    assert lm_ctx is not None
    assert lm_ctx.client is not None

    result = cast(
        Dict,
        make_request(
            lm_ctx.client,
            f"/lm/products/{id}",
            "GET",
            expected_status=200,
            abort_message="Couldn't get the product from the API",
            support=True,
        ),
    )

    render_single_result(
        result,
        title=f"Product id {id}",
    )


@app.command("create")
@handle_abort
def create(
    ctx: typer.Context,
    name: str = typer.Option(
        ...,
        help="The name of product to create. Must match the product name in the license.",
    ),
):
    """
    Create a new product.
    """
    lm_ctx: LicenseManagerContext = ctx.obj

    # Make static type checkers happy
    assert lm_ctx is not None
    assert lm_ctx.client is not None

    request_data = ProductCreateSchema(
        name=name,
    )

    make_request(
        lm_ctx.client,
        "/lm/products",
        "POST",
        expected_status=201,
        abort_message="Product creation failed",
        support=True,
        request_model=request_data,
    )

    terminal_message(
        "The product was created successfully.",
        subject="Product creation succeeded.",
    )


@app.command("delete")
@handle_abort
def delete(
    ctx: typer.Context,
    id: int = typer.Option(
        ...,
        help="The id of the product to delete.",
    ),
):
    """
    Delete an existing product.
    """
    lm_ctx: LicenseManagerContext = ctx.obj

    # Make static type checkers happy
    assert lm_ctx is not None
    assert lm_ctx.client is not None

    make_request(
        lm_ctx.client,
        f"/lm/products/{id}",
        "DELETE",
        expected_status=200,
        abort_message="Request to delete product was not accepted by the API",
        support=True,
    )
    terminal_message(
        "The product was deleted successfully.",
        subject="Product delete succeeded",
    )
