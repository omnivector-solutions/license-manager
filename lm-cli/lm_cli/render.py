"""
Helpers for rendering user facing output.
"""

import json
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lm_cli.text_tools import dedent
from lm_cli.text_tools import indent as indent_text


class StyleMapper:
    """
    Provide a mapper that can set ``rich`` styles for rendered output of data tables and dicts.

    The subapps have list endpoints that return sets of values. These are rendered as tables in
    the output. The StyleMapper class provides a way to simply define styles that are applied
    to the columns of the table.

    Example:

    The following code will print a table where the columns are colored according to the style_mapper:

    .. code-block: python

       style_mapper = StyleMapper(
           a="bold green",
           b="red",
           c="blue",
       )
       envelope = dict(
           results=[
               dict(a=1, b=2, c=3),
               dict(a=4, b=5, c=6),
               dict(a=7, b=8, c=9),
           ],
           pagination=dict(total=3)
       )
       render_list_results(jb_ctx, envelope, style_mapper)

    """

    colors: Dict[str, str]

    def __init__(self, **colors: str):
        """
        Initialize the StyleMapper.
        """
        self.colors = colors

    def map_style(self, column: str) -> Dict[str, Any]:
        """
        Map a column name from the table to display to the style that should be used to render it.
        """
        color = self.colors.get(column, "white")
        return dict(
            style=color,
            header_style=f"bold {color}",
        )


def terminal_message(message, subject=None, color="green", footer=None, indent=True):
    """
    Print a nicely formatted message as output to the user using a ``rich`` ``Panel``.

    :param: message: The message to print.
    :param: subject: An optional subject line to add in the header of the ``Panel``.
    :param: color:   An optional color to style the ``subject`` header.
    :param: footer:  An optional message to display in the footer of the ``Panel``.
    :param: indent:  Adds padding to the left of the message.
    """
    panel_kwargs = dict(padding=1)
    if subject is not None:
        panel_kwargs["title"] = f"[{color}]{subject}"
    if footer is not None:
        panel_kwargs["subtitle"] = f"[dim italic]{footer}[/dim italic]"
    text = dedent(message)
    if indent:
        text = indent_text(text, prefix="  ")
    console = Console()
    console.print()
    console.print(Panel(text, **panel_kwargs))
    console.print()


def render_json(data: Any):
    """
    Print a nicely formatted representation of a JSON serializable python primitive.
    """
    console = Console()
    console.print()
    console.print_json(json.dumps(data))
    console.print()


def render_list_results(
    data: List[dict],
    style_mapper: Optional[StyleMapper] = None,
    title: str = "Results List",
):
    """
    Render a list of result data items in a ``rich`` ``Table``.

    :param: data:          The list of data that will be rendered.
    :param: style_mapper:  The style mapper that should be used to apply styles to the columns of the table.
    :param: title:         The title header to include above the ``Table`` output.
    """
    if len(data) == 0:
        terminal_message("There are no results to display.", subject="Nothing here...")
        return

    first_row = data[0]

    table = Table(title=title, caption=f"Total items: {len(data)}")
    if style_mapper is None:
        style_mapper = StyleMapper()
    for key in first_row.keys():
        table.add_column(key, **style_mapper.map_style(key))

    for row in data:
        table.add_row(*[str(v) for v in row.values()])

    console = Console()
    console.print()
    console.print(table)
    console.print()


def render_single_result(
    data: Dict[str, Any],
    title: str = "Result",
):
    """
    Render a single data item in a ``rich`` ``Table. That shows the key and value of each item.

    :param: data:        The data item to display. Should be a dict.
    :param: title:       The title header to include above the ``Table`` output.
    """
    table = Table(title=title)
    table.add_column("Key", header_style="bold yellow", style="yellow")
    table.add_column("Value", header_style="bold white", style="white")

    for (key, value) in data.items():
        table.add_row(key, str(value))

    console = Console()
    console.print()
    console.print(table)
    console.print()
