import subprocess
import buzz
import httpx
from lm_test.config import settings
from lm_test.exceptions import AuthTokenError, ResponseNotJSONError, ResponseError
from typing import Optional, Union


def acquire_token() -> str:
    """
    Retrieves a token from OIDC based on the app settings.
    """
    oidc_body = dict(
        audience=settings.OIDC_AUDIENCE,
        client_id=settings.OIDC_CLIENT_ID,
        client_secret=settings.OIDC_CLIENT_SECRET,
        grant_type="client_credentials",
    )
    oidc_url = f"https://{settings.OIDC_DOMAIN}/protocol/openid-connect/token"
    response = httpx.post(oidc_url, data=oidc_body)

    AuthTokenError.require_condition(
        response.status_code == 200, f"Failed to get auth token from OIDC: {response.text}"
    )
    with AuthTokenError.handle_errors("Malformed response payload from OIDC"):
        token = response.json()["access_token"]

    return token


class BaseBackendClient(httpx.AsyncClient):
    """
    Base class for all backend clients.
    """

    _token: Optional[str]

    def __init__(self, url: str):
        self._token = None
        super().__init__(base_url=url, auth=self._inject_token)

    def _inject_token(self, request: httpx.Request) -> httpx.Request:
        if self._token is None:
            self._token = acquire_token()
        request.headers["authorization"] = f"Bearer {self._token}"
        return request


class LM_API_Client(BaseBackendClient):
    """
    Client to make requests to the License Manager API.
    """
    def __init__(self):
        super().__init__(url=settings.LM_API_BASE_URL)


class LM_SIM_Client(BaseBackendClient):
    """
    Client to make requests to the License Manager Simulator.
    """
    def __init__(self):
        super().__init__(url=settings.LM_SIM_BASE_URL)


async def create_resource(client: BaseBackendClient, resource_data: dict, resource_url: str):
    """
    Sends a POST request to an endpoint and returns the parsed response.
    """
    resource_created = await client.post(
        resource_url,
        json=resource_data,
    )

    ResponseError.require_condition(
        resource_created.status_code == 201, f"Failed to create resource: {resource_created.text}"
    )

    with ResponseNotJSONError.handle_errors("Failed to create resource"):
        resource = resource_created.json()

    return resource


async def delete_resource(
    client: BaseBackendClient,
    resource_id: Optional[Union[int, str]],
    resource_url: str,
    payload: Optional[dict] = None,
):
    """
    Sends a DEL request to an endpoint to delete a resource.
    """
    url = f"{resource_url}/{resource_id}" if resource_id else resource_url

    resource_deleted = await client.request(
        "DELETE",
        url,
        json=payload,
    )

    ResponseError.require_condition(
        resource_deleted.status_code in [200, 204], f"Failed to delete resource: {resource_deleted.text}"
    )


def run(*command):
    """
    Run a command and return the result.
    """
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        check=False,
    )

    with buzz.handle_errors(
        "Got returncode={} when running {} due to: {}".format(
            result.returncode,
            " ".join(result.args),
            result.stderr,
        )
    ):
        result.check_returncode()

    return result.stdout
