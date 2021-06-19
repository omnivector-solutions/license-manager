#!/usr/bin/env python3
import typer
import requests

from typing import Optional

from licensemanager2.agent.settings import SETTINGS
from licensemanager2.backend.configuration import ConfigurationRow


app = typer.Typer(
    help="CLI for interaction with the license manager configuration table"
)


@app.command()
def get_all():
    """
    Get all configurations from the backend.
    """
    resp = requests.get(f"{SETTINGS.BACKEND_BASE_URL}/api/v1/config/all")
    if resp.status_code == 200:
        for item in resp.json():
            typer.echo(item)
    else:
        typer.echo(f"Could not make request, status code: {resp.status_code}")


@app.command()
def get(id: int):
    """
    Return a single configuration from the backend given a configuration id.
    """
    resp = requests.get(
        f"{SETTINGS.BACKEND_BASE_URL}/api/v1/config/{id}"
    )
    if resp.status_code == 200:
        typer.echo(resp.json())
    else:
        typer.echo(f"Could not get config {id}, status code: {resp.status_code}")


@app.command()
def add(
    id: int,
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
        f"{SETTINGS.BACKEND_BASE_URL}/api/v1/config/",
        json={
            "id": id,
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
    features: str= typer.Option(None),
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
    ctxt = dict()
    if product:
        ctxt['product'] = product
    if features:
        ctxt['features'] = features.split(",")
    if license_servers:
        ctxt['license_servers'] = license_servers.split(",")
    if license_server_type:
        ctxt['license_server_type'] = license_server_type
    if grace_time:
        ctxt['grace_time'] = grace_time
    resp = requests.put(
        f"{SETTINGS.BACKEND_BASE_URL}/api/v1/config/{id}",
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
        f"{SETTINGS.BACKEND_BASE_URL}/api/v1/config/{id}",
        data={'id': id}
    )
    if resp.status_code == 200:
        typer.echo(resp.json())
    else:
        typer.echo("Could not delete the configuration row, status code {resp.status_code}")
if __name__ == "__main__":
    app()