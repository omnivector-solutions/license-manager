"""
Persistent data storage for the API.
"""
import typing
from dataclasses import dataclass

from fastapi import Depends
from fastapi.exceptions import HTTPException
from loguru import logger
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import Mapped, MappedColumn
from sqlalchemy.sql.expression import ColumnElement, UnaryExpression
from starlette import status
from yarl import URL

from lm_api.config import settings
from lm_api.security import IdentityPayload, PermissionMode, lockdown_with_identity


def build_db_url(
    override_db_name: typing.Optional[str] = None,
    force_test: bool = False,
    asynchronous: bool = True,
) -> str:
    """
    Build a database url based on settings.

    If ``force_test`` is set, build from the test database settings.
    If ``asynchronous`` is set, use asyncpg.
    If ``override_db_name`` replace the database name in the settings with the supplied value.
    """
    prefix = "TEST_" if force_test else ""
    db_user = getattr(settings, f"{prefix}DATABASE_USER")
    db_password = getattr(settings, f"{prefix}DATABASE_PSWD")
    db_host = getattr(settings, f"{prefix}DATABASE_HOST")
    db_port = getattr(settings, f"{prefix}DATABASE_PORT")
    db_name = getattr(settings, f"{prefix}DATABASE_NAME") if override_db_name is None else override_db_name
    db_path = "/{}".format(db_name)
    db_scheme = "postgresql+asyncpg" if asynchronous else "postgresql"

    return str(
        URL.build(
            scheme=db_scheme,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            path=db_path,
        )
    )


class EngineFactory:
    """
    Provide a factory class that creates engines and keeps track of them in an engine mapping.

    This is used for multi-tenancy and database URL creation at request time.
    """

    engine_map: typing.Dict[str, AsyncEngine]

    def __init__(self):
        """
        Initialize the EngineFactory.
        """
        self.engine_map = dict()

    async def cleanup(self):
        """
        Close all engines stored in the engine map and clears the engine_map.
        """
        for engine in self.engine_map.values():
            await engine.dispose()
        self.engine_map = dict()

    def get_engine(self, override_db_name: typing.Optional[str] = None) -> AsyncEngine:
        """
        Get a database engine.

        If the database url is already in the engine map, return the engine stored there. Otherwise, build
        a new one, store it, and return the new engine.
        """
        db_url = build_db_url(
            override_db_name=override_db_name,
            force_test=settings.DEPLOY_ENV.lower() == "test",
        )
        if db_url not in self.engine_map:
            self.engine_map[db_url] = create_async_engine(db_url, pool_pre_ping=True)
        return self.engine_map[db_url]

    def get_session(self, override_db_name: typing.Optional[str] = None) -> AsyncSession:
        """
        Get an asynchronous database session.

        Gets a new session from the correct engine in the engine map.
        """
        engine = self.get_engine(override_db_name=override_db_name)
        return AsyncSession(engine, expire_on_commit=False)


engine_factory = EngineFactory()


@dataclass
class SecureSession:
    """
    Provide a container class for an IdentityPayload and AsyncSesson for the current request.
    """

    identity_payload: IdentityPayload
    session: AsyncSession


def secure_session(*scopes: str, permission_mode: PermissionMode = PermissionMode.SOME, commit: bool = True):
    """
    Provide an injectable for FastAPI that checks permissions and returns a database session for this request.

    This should be used for all secured routes that need access to the database. It will commit the
    transaction upon completion of the request. If an exception occurs, it will rollback the transaction.
    If multi-tenancy is enabled, it will retrieve a database session for the database associated with the
    client_id found in the requesting user's auth token.

    If testing mode is enabled, it will flush the session instead of committing changes to the database.

    Note that the session should NEVER be explicitly committed anywhere else in the source code.
    """

    async def dependency(
        identity_payload: IdentityPayload = Depends(
            lockdown_with_identity(*scopes, permission_mode=permission_mode)
        ),
    ) -> typing.AsyncIterator[SecureSession]:
        override_db_name = identity_payload.organization_id if settings.MULTI_TENANCY_ENABLED else None
        session = engine_factory.get_session(override_db_name=override_db_name)
        await session.begin_nested()
        try:
            yield SecureSession(
                identity_payload=identity_payload,
                session=session,
            )
            # In test mode, we should not commit to the database. Instead, just flush to the session
            if settings.DEPLOY_ENV.lower() == "test":
                logger.debug("Flushing session due to test mode")
                await session.flush()
            elif commit is True:
                logger.debug("Committing session")
                await session.commit()
        except Exception as err:
            logger.warning(f"Rolling back session due to error: {err}")
            await session.rollback()
            raise err
        finally:
            # In test mode, we should not close the session so that assertions can be made about the state
            # of the db session in the test functions after calling the application logic
            if settings.DEPLOY_ENV.lower() != "test":
                logger.debug("Closing session")
                await session.close()

    return dependency


def render_sql(query) -> str:
    """
    Render a sqlalchemy query into a string for debugging.
    """
    return query.compile(compile_kwargs={"literal_binds": True})


def search_clause(
    search_terms: str,
    searchable_fields: typing.List[MappedColumn[typing.Any]],
) -> ColumnElement[bool]:
    """
    Create search clause across searchable fields with search terms.
    """
    return or_(*[field.ilike(f"%{term}%") for field in searchable_fields for term in search_terms.split()])


def sort_clause(
    sort_field: str,
    sortable_fields: typing.List[MappedColumn[typing.Any]],
    sort_ascending: bool,
) -> typing.Union[Mapped[typing.Any], UnaryExpression]:
    """
    Create a sort clause given a sort field, the list of sortable fields, and a sort_ascending flag.
    """
    sort_field_names = [f.name for f in sortable_fields]
    try:
        index = sort_field_names.index(sort_field)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sorting column requested: {sort_field}. Must be one of {sort_field_names}",
        )
    sort_column: typing.Union[Mapped[typing.Any], UnaryExpression] = sortable_fields[index]
    if not sort_ascending:
        sort_column = sort_column.desc()
    return sort_column
