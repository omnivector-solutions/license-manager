from contextlib import asynccontextmanager
from typing import Optional
from unittest.mock import patch

import asyncpg
import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select

from lm_backend.api.models.cluster import Cluster
from lm_backend.config import settings
from lm_backend.database import Base, engine_factory
from lm_backend.permissions import Permissions


@pytest.fixture(autouse=True, scope="module")
async def alt_engine():
    """
    Provide a fixture to prepare the alternative test database.

    Note that we DO NOT cleanup the engine factory in this fixture. The main fixture will cover this.
    """
    engine = engine_factory.get_engine("alt-test-db")
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all, checkfirst=True)
        try:
            yield engine
        finally:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.drop_all)
    except asyncpg.exceptions.InvalidCatalogNameError:
        pytest.skip(
            "Skipping multi-tenancy tests as alternative test database is not available",
            allow_module_level=True,
        )


@pytest.fixture(scope="function")
def get_synth_sessions():
    """
    Get a the default and alternate sessions from the engine_factory.

    This method produces a session for both the default and alternate test database.

    This is necessary to make sure that the test code uses the same session as the one returned by
    the dependency injection for the router code. Otherwise, changes made in the router's session would not
    be visible in the test code. Note that changes made in this synthesized session are always rolled back
    and never committed.

    If multi-tenancy is enabled, the override_db_name for the default session will be the name of the normal
    test database.
    """

    @asynccontextmanager
    async def helper():
        default_session = None
        alt_session = None
        try:
            default_session = engine_factory.get_session()
            await default_session.begin_nested()

            alt_session = engine_factory.get_session("alt-test-db")
            await alt_session.begin_nested()

            def _get_session(override_db_name: Optional[str] = None):
                if override_db_name is None or override_db_name == settings.TEST_DATABASE_NAME:
                    return default_session
                elif override_db_name == "alt-test-db":
                    return alt_session
                else:
                    raise RuntimeError(f"Unknown test database name: {override_db_name}")

            with patch("lm_backend.database.engine_factory.get_session", side_effect=_get_session):
                yield (default_session, alt_session)

        finally:
            if default_session is not None:
                await default_session.rollback()
                await default_session.close()

            if alt_session is not None:
                await alt_session.rollback()
                await alt_session.close()

    return helper


@pytest.mark.asyncio
async def test_get_session():
    """
    Test that a different session is fetched from ``get_session()`` when supplying ``override_db_name``.

    Requires that the test database server is running a second test database named "alt-test-db".
    """
    default_session = None
    alt_session = None
    try:
        default_session = engine_factory.get_session()
        alt_session = engine_factory.get_session("alt-test-db")
        assert default_session is not alt_session

    finally:
        if default_session is not None:
            await default_session.close()
        if alt_session is not None:
            await alt_session.close()


@pytest.mark.asyncio
async def test_session_tenancy(get_synth_sessions):
    """
    Test tenancy with the database sessions produced by the engine_factory's ``get_session()`` helper.

    Checks that database writes and reads for the two sessions are distinct and do not effect each other.
    """
    default_client_id = settings.TEST_DATABASE_NAME
    alt_client_id = "alt-test-db"

    async with get_synth_sessions() as (default_session, alt_session):
        default_session.add(Cluster(name="Dummy Cluster", client_id=default_client_id))
        await default_session.flush()

        alt_session.add(Cluster(name="Dummy Cluster", client_id=alt_client_id))
        await alt_session.flush()

        default_clusters = (await default_session.execute(select(Cluster))).scalars().all()
        alt_clusters = (await alt_session.execute(select(Cluster))).scalars().all()

        assert len(default_clusters) == 1
        assert len(alt_clusters) == 1
        assert default_clusters != alt_clusters


@pytest.mark.asyncio
async def test_clusters_router_with_multi_tenancy(
    get_synth_sessions,
    backend_client: AsyncClient,
    inject_client_id_in_security_header,
    tweak_settings,
):
    """
    Test POST /clusters/ correctly creates clusters using multi-tenancy.

    This method checks to make sure that the correct database is used for the API request based on the
    client_id that is provided in the auth token in the request header.
    """
    default_client_id = settings.TEST_DATABASE_NAME
    alt_client_id = "alt-test-db"

    with tweak_settings(MULTI_TENANCY_ENABLED=True):
        async with get_synth_sessions() as (default_session, alt_session):

            inject_client_id_in_security_header(default_client_id, Permissions.CLUSTER_EDIT)
            default_response = await backend_client.post(
                "/lm/clusters/",
                json=dict(
                    name="default-cluster",
                    client_id=default_client_id,
                ),
            )
            assert default_response.status_code == status.HTTP_201_CREATED
            default_data = default_response.json()
            assert default_data["name"] == "default-cluster"
            assert default_data["client_id"] == default_client_id

            inject_client_id_in_security_header(alt_client_id, Permissions.CLUSTER_EDIT)
            alt_response = await backend_client.post(
                "/lm/clusters/",
                json=dict(
                    name="alt-cluster",
                    client_id=alt_client_id,
                ),
            )
            assert alt_response.status_code == status.HTTP_201_CREATED
            alt_data = alt_response.json()
            assert alt_data["name"] == "alt-cluster"
            assert alt_data["client_id"] == alt_client_id

            default_clusters = (await default_session.execute(select(Cluster))).scalars().all()
            assert len(default_clusters) == 1
            assert default_clusters[0].name == default_data["name"]

            alt_clusters = (await alt_session.execute(select(Cluster))).scalars().all()
            assert len(alt_clusters) == 1
            assert alt_clusters[0].name == alt_data["name"]
