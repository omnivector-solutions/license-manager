"""
A ``typer`` app that can interact with Features data in a cruddy manner.
"""

from typing import Dict, List, Optional, cast

import typer

from lm_cli.constants import SortOrder
from lm_cli.exceptions import handle_abort
from lm_cli.render import StyleMapper, render_list_results, render_single_result, terminal_message
from lm_cli.requests import make_request, parse_query_params
from lm_cli.schemas import FeatureCreateSchema, LicenseManagerContext


style_mapper = StyleMapper(
    id="blue",
    feature_id="green",
    config_id="cyan",
    reserved="magenta",
)


app = typer.Typer(help="Commands to interact with features.")


@app.command("list")
@handle_abort
def list_all(
    ctx: typer.Context,
    search: Optional[str] = typer.Option(None, help="Apply a search term to results."),
    sort_order: SortOrder = typer.Option(SortOrder.UNSORTED, help="Specify sort order."),
    sort_field: Optional[str] = typer.Option(None, help="The field by which results should be sorted."),
):
    """
    Show feature information.
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
            "/lm/features/",
            "GET",
            expected_status=200,
            abort_message="Couldn't retrieve features list from API",
            support=True,
            params=params,
        ),
    )

    render_list_results(
        data,
        title="Features List",
        style_mapper=style_mapper,
    )


@app.command("get-one")
@handle_abort
def get_one(
    ctx: typer.Context,
    id: int = typer.Option(int, help="The specific id of the feature."),
):
    """
    Get a single feature by id.
    """
    lm_ctx: LicenseManagerContext = ctx.obj

    # Make static type checkers happy
    assert lm_ctx is not None
    assert lm_ctx.client is not None

    result = cast(
        Dict,
        make_request(
            lm_ctx.client,
            f"/lm/features/{id}",
            "GET",
            expected_status=200,
            abort_message="Couldn't get the feature from the API",
            support=True,
        ),
    )

    render_single_result(
        result,
        title=f"Feature id {id}",
    )


@app.command("create")
@handle_abort
def create(
    ctx: typer.Context,
    name: str = typer.Option(
        ...,
        help="The name of feature to create. Must match the feature name in the license.",
    ),
    product_id: int = typer.Option(
        ...,
        help="The product_id of the feature.",
    ),
    config_id: int = typer.Option(
        ...,
        help="The config_id of the feature.",
    ),
    reserved: int = typer.Option(
        ...,
        help="How many licenses should be reserved for usage in desktop enviroments.",
    ),
):
    """
    Create a new feature.
    """
    lm_ctx: LicenseManagerContext = ctx.obj

    # Make static type checkers happy
    assert lm_ctx is not None
    assert lm_ctx.client is not None

    request_data = FeatureCreateSchema(
        name=name,
        product_id=product_id,
        config_id=config_id,
        reserved=reserved,
    )

    make_request(
        lm_ctx.client,
        "/lm/features/",
        "POST",
        expected_status=201,
        abort_message="Feature creation failed",
        support=True,
        request_model=request_data,
    )

    terminal_message(
        "The feature was created successfully.",
        subject="Feature creation succeeded.",
    )


@app.command("delete")
@handle_abort
def delete(
    ctx: typer.Context,
    id: int = typer.Option(
        ...,
        help="The id of the feature to delete.",
    ),
):
    """
    Delete an existing feature.
    """
    lm_ctx: LicenseManagerContext = ctx.obj

    # Make static type checkers happy
    assert lm_ctx is not None
    assert lm_ctx.client is not None

    make_request(
        lm_ctx.client,
        f"/lm/features/{id}",
        "DELETE",
        expected_status=200,
        abort_message="Request to delete feature was not accepted by the API",
        support=True,
    )
    terminal_message(
        "The feature was deleted successfully.",
        subject="Feature delete succeeded",
    )
