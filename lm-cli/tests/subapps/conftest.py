from typing import Callable

import httpx
import pytest
from typer import Context, Typer
from typer.testing import CliRunner

from lm_cli.schemas import IdentityData, LicenseManagerContext, Persona, TokenSet


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
    def _helper(user_email: str, org_name: str = "dumb-org", access_token: str = "foo"):
        dummy_context.persona = Persona(
            token_set=TokenSet(access_token=access_token),
            identity_data=IdentityData(
                user_email=user_email,
                org_name=org_name,
            ),
        )

    return _helper


@pytest.fixture
def dummy_license_data():
    return [
        dict(
            product_feature="product1.license1",
            used=0,
            total=100,
            available=100,
        ),
        dict(
            product_feature="product2.license2",
            used=0,
            total=200,
            available=200,
        ),
    ]


@pytest.fixture
def dummy_booking_data():
    return [
        dict(
            id=1,
            job_id=123,
            product_feature="product1.license1",
            booked=10,
            config_id=1,
            lead_host="test-host",
            user_name="test-user",
            cluster_name="test-cluster",
        ),
        dict(
            id=2,
            job_id=234,
            product_feature="product2.license2",
            booked=20,
            config_id=2,
            lead_host="test-host",
            user_name="test-user",
            cluster_name="test-cluster",
        ),
    ]


@pytest.fixture
def dummy_configuration_data():
    return [
        dict(
            id=1,
            name="Configuration 1",
            product="product1",
            features='{"license1": 100}',
            license_servers=["flexlm:127.0.0.1:1234"],
            license_server_type="flexlm",
            grace_time=60,
            client_id="cluster-staging",
        ),
        dict(
            id=2,
            name="Configuration 2",
            product="product2",
            features='{"license2": 200}',
            license_servers=["rlm:127.0.0.1:2345"],
            license_server_type="rlm",
            grace_time=60,
            client_id="cluster-staging"
        ),
    ]


@pytest.fixture
def dummy_configuration_data_for_printing():
    return [
        dict(
            id=1,
            name="Configuration 1",
            product="product1",
            features='{"license1": 100}',
            license_servers=["flexlm:127.0.0.1:1234"],
            license_server_type="flexlm",
            grace_time="60 (seconds)",
            client_id="cluster-staging",
        ),
        dict(
            id=2,
            name="Configuration 2",
            product="product2",
            features='{"license2": 200}',
            license_servers=["rlm:127.0.0.1:2345"],
            license_server_type="rlm",
            grace_time="60 (seconds)",
            client_id="cluster-staging",
        ),
    ]
