from typing import Callable

import httpx
import pytest
from typer import Context, Typer
from typer.testing import CliRunner

from lm_cli.schemas import LicenseManagerContext, Persona, TokenSet


@pytest.fixture
def dummy_domain():
    return "https://dummy.com"


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def make_test_app(dummy_context):
    def _main_callback(ctx: Context):
        ctx.obj = dummy_context

    def _helper(command_name: str, command_function: Callable):
        main_app = Typer()
        main_app.callback()(_main_callback)
        main_app.command(name=command_name)(command_function)
        return main_app

    return _helper


@pytest.fixture
def dummy_context(dummy_domain):
    return LicenseManagerContext(
        persona=None,
        client=httpx.Client(base_url=dummy_domain, headers={"Authorization": "Bearer XXXXXXXX"}),
    )


@pytest.fixture
def attach_persona(dummy_context):
    def _helper(user_email: str, access_token: str = "foo"):
        dummy_context.persona = Persona(
            token_set=TokenSet(access_token=access_token),
            user_email=user_email,
        )

    return _helper


@pytest.fixture
def dummy_booking_data():
    return [
        {"id": 1, "job_id": 123, "feature_id": 1, "quantity": 50},
        {"id": 2, "job_id": 234, "feature_id": 2, "quantity": 35},
    ]


@pytest.fixture
def dummy_cluster_data(dummy_configuration_data):
    return [
        {
            "id": 1,
            "name": "Cluster 1",
            "client_id": "cluster1",
            "configurations": dummy_configuration_data,
            "jobs": [
                {
                    "id": 1,
                    "slurm_job_id": "string",
                    "cluster_id": 1,
                    "username": "string",
                    "lead_host": "string",
                    "bookings": [
                        {"id": 1, "job_id": 1, "feature_id": 1, "quantity": 50},
                        {"id": 2, "job_id": 1, "feature_id": 2, "quantity": 25},
                    ],
                }
            ],
        }
    ]


@pytest.fixture
def dummy_cluster_data_for_printing():
    return [
        {
            "id": 1,
            "name": "Cluster 1",
            "client_id": "cluster1",
            "configurations": "Abaqus, Converge",
        }
    ]


@pytest.fixture
def dummy_configuration_data():
    return [
        {
            "id": 1,
            "name": "Abaqus",
            "cluster_id": 1,
            "features": [
                {
                    "id": 1,
                    "name": "abaqus",
                    "product": {"id": 1, "name": "abaqus"},
                    "config_id": 1,
                    "reserved": 100,
                    "inventory": {"id": 1, "feature_id": 1, "total": 1000, "used": 500},
                }
            ],
            "license_servers": [
                {"id": 1, "config_id": 1, "host": "licserv0001", "port": 1234},
                {"id": 2, "config_id": 1, "host": "licserv0002", "port": 2345},
            ],
            "grace_time": 60,
            "type": "flexlm",
        },
        {
            "id": 2,
            "name": "Converge",
            "cluster_id": 1,
            "features": [
                {
                    "id": 2,
                    "name": "converge_super",
                    "product": {"id": 2, "name": "converge"},
                    "config_id": 2,
                    "reserved": 50,
                    "inventory": {"id": 2, "feature_id": 2, "total": 600, "used": 300},
                }
            ],
            "license_servers": [
                {"id": 3, "config_id": 2, "host": "licserv0003", "port": 1234},
                {"id": 4, "config_id": 2, "host": "licserv0004", "port": 2345},
            ],
            "grace_time": 60,
            "type": "rlm",
        },
    ]


@pytest.fixture
def dummy_configuration_data_for_printing():
    return [
        {
            "id": 1,
            "name": "Abaqus",
            "cluster_id": 1,
            "features": "abaqus",
            "license_servers": "licserv0001:1234, licserv0002:2345",
            "grace_time": "60 (seconds)",
            "type": "flexlm",
        },
        {
            "id": 2,
            "name": "Converge",
            "cluster_id": 1,
            "features": "converge_super",
            "license_servers": "licserv0003:1234, licserv0004:2345",
            "grace_time": "60 (seconds)",
            "type": "rlm",
        },
    ]


@pytest.fixture
def dummy_feature_data():
    return [
        {
            "id": 1,
            "name": "abaqus",
            "product": {"id": 1, "name": "abaqus"},
            "config_id": 1,
            "reserved": 100,
            "inventory": {"id": 1, "feature_id": 1, "total": 1000, "used": 500},
        },
        {
            "id": 2,
            "name": "converge_super",
            "product": {"id": 2, "name": "converge"},
            "config_id": 2,
            "reserved": 50,
            "inventory": {"id": 2, "feature_id": 2, "total": 600, "used": 300},
        },
    ]


@pytest.fixture
def dummy_feature_data_for_printing():
    return [
        {
            "id": 1,
            "config_id": 1,
            "product": "abaqus",
            "feature": "abaqus",
            "total": 1000,
            "used": 500,
            "reserved": 100,
            "booked": 50,
            "available": 350,
        },
        {
            "id": 2,
            "config_id": 2,
            "product": "converge",
            "feature": "converge_super",
            "total": 600,
            "used": 300,
            "reserved": 50,
            "booked": 35,
            "available": 215,
        },
    ]


@pytest.fixture
def dummy_job_data():
    return [
        {
            "id": 1,
            "slurm_job_id": "string",
            "cluster_id": 1,
            "username": "string",
            "lead_host": "string",
            "bookings": [
                {"id": 1, "job_id": 1, "feature_id": 1, "quantity": 50},
                {"id": 2, "job_id": 1, "feature_id": 2, "quantity": 25},
            ],
        }
    ]


@pytest.fixture
def dummy_job_data_for_printing():
    return [
        {
            "id": 1,
            "slurm_job_id": "string",
            "cluster_id": 1,
            "username": "string",
            "lead_host": "string",
            "bookings": "feature_id: 1, quantity: 50 | feature_id: 2, quantity: 25",
        }
    ]


@pytest.fixture
def dummy_license_server_data():
    return [
        {"id": 1, "config_id": 1, "host": "licserv0001", "port": 1234},
        {"id": 2, "config_id": 1, "host": "licserv0002", "port": 2345},
    ]


@pytest.fixture
def dummy_product_data():
    return [
        {
            "id": 1,
            "name": "abaqus",
        },
        {
            "id": 2,
            "name": "converge",
        },
    ]
