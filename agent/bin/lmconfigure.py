#!/usr/bin/env python3
from typing import Dict
import typer
import requests

from tabulate import tabulate

from lm_agent.settings import settings
from lm_agent.workload_managers.slurm.common import LM2_AGENT_HEADERS


app = typer.Typer(
    help="CLI for interaction with the license manager configuration table"
)


@app.command()
def get_all():
    """
    Get all configurations from the backend.
    """
    resp = requests.get(
        f"{settings.BACKEND_BASE_URL}/api/v1/config/all",
        headers=LM2_AGENT_HEADERS,
    )
    if resp.status_code == 200:
        tabulate_response = tabulate(
            (my_dict for my_dict in resp.json()), headers="keys"
        )
        typer.echo(tabulate_response)
    else:
        typer.echo(f"Could not get all the configurations, status code: {resp.status_code}")


@app.command()
def get(id: int):
    """
    Return a single configuration from the backend given a configuration id.
    """
    resp = requests.get(
        f"{settings.BACKEND_BASE_URL}/api/v1/config/{id}",
        headers=LM2_AGENT_HEADERS,
    )
    if resp.status_code == 200:
        tabulate_response = tabulate(
            (my_dict for my_dict in resp.json()), headers="keys"
        )
        typer.echo(tabulate_response)
    else:
        typer.echo(f"Could not get config {id}, status code: {resp.status_code}")


@app.command()
def add(
    product: str,
    features: str,
    license_servers: str,
    license_server_type: str,
    grace_time: int
):
    """
    Add a configuration to the database.
    """
    resp = requests.post(
        f"{settings.BACKEND_BASE_URL}/api/v1/config/",
        headers=LM2_AGENT_HEADERS,
        json={
            "product": product,
            "features": features.split(","),
            "license_servers": license_servers.split(","),
            "license_server_type": license_server_type,
            "grace_time": grace_time,
        }
    )
    if resp.status_code == 200:
        typer.echo(resp.json())
    else:
        typer.echo(f"Could not add configuration, status code {resp.status_code}")


@app.command()
def update(
    id: int,
    product: str = typer.Option(None),
    features: str = typer.Option(None),
    license_servers: str = typer.Option(None),
    license_server_type: str = typer.Option(None),
    grace_time: int = typer.Option(None),
):
    """
    Update a configuration row with optionally provided values.
    For example, specify an argument with "--product newproduct"
    """
    if not id:
        typer.echo("Please supply an ID")
        return
    ctxt: Dict = dict()
    if product:
        ctxt['product'] = product
    if features:
        ctxt['features'] = features.split(",")
    if license_servers:
        ctxt['license_servers'] = license_servers.split(",")
    if license_server_type:
        ctxt['license_server_type'] = license_server_type
    if grace_time:
        ctxt['grace_time'] = int(grace_time)

    resp = requests.put(
        f"{settings.BACKEND_BASE_URL}/api/v1/config/{id}",
        headers=LM2_AGENT_HEADERS,
        json=ctxt
    )
    if resp.status_code == 200:
        typer.echo(resp.json())
    else:
        typer.echo(f"Could not update the configuration row, status code {resp.status_code}")


@app.command()
def delete(id: int):
    """
    Delete a configuration entry from the configuration table.
    """
    if not id:
        typer.echo("Please supply an ID")
        return
    resp = requests.delete(
        f"{settings.BACKEND_BASE_URL}/api/v1/config/{id}",
        headers=LM2_AGENT_HEADERS,
        data={'id': id}
    )
    if resp.status_code == 200:
        typer.echo(resp.json())
    else:
        typer.echo(f"Could not delete the configuration row, status code {resp.status_code}")


if __name__ == "__main__":
    app()
