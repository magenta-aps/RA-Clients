# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import AsyncGenerator
from typing import Generator
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from respx import MockRouter

from raclients.auth import AuthenticatedAsyncHTTPXClient
from raclients.auth import AuthenticatedHTTPXClient
from raclients.auth import BaseAuthenticatedClient


@pytest.fixture
def base_client(client_params: dict) -> BaseAuthenticatedClient:
    return BaseAuthenticatedClient(session=None, **client_params)


@pytest.fixture
def client(client_params: dict) -> Generator[AuthenticatedHTTPXClient, None, None]:
    with AuthenticatedHTTPXClient(**client_params) as client:
        yield client


@pytest.fixture
async def async_client(
    client_params: dict,
) -> AsyncGenerator[AuthenticatedAsyncHTTPXClient, None]:
    async with AuthenticatedAsyncHTTPXClient(**client_params) as client:
        yield client


def test_authenticated_httpx_client_init(client: AuthenticatedHTTPXClient):
    assert client.client_id == "AzureDiamond"
    assert client.client_secret == "hunter2"
    assert client.token_endpoint == (
        "http://keycloak.example.org/auth/realms/mordor/protocol/openid-connect/token"
    )
    assert client.metadata["token_endpoint"] == client.token_endpoint
    assert client.metadata["grant_type"] == "client_credentials"


def test_authenticated_httpx_client_init_from_env(client_params_env: dict):
    with AuthenticatedHTTPXClient() as client:
        assert client.client_id == client_params_env["client_id"]
        assert client.client_secret == client_params_env["client_secret"]
        assert client.auth_server == client_params_env["auth_server"]
        assert client.auth_realm == client_params_env["auth_realm"]


def test_should_fetch_token_if_not_set(base_client: BaseAuthenticatedClient):
    base_client.token = None
    assert base_client.should_fetch_token("http://www.example.org") is True


def test_should_not_fetch_token_if_set(base_client: BaseAuthenticatedClient):
    base_client.token = True
    assert base_client.should_fetch_token("http://www.example.org") is False


def test_should_not_fetch_token_if_token_endpoint(base_client: BaseAuthenticatedClient):
    base_client.token = None
    assert base_client.should_fetch_token(base_client.token_endpoint) is False


def test_should_not_fetch_token_if_withhold_token(base_client: BaseAuthenticatedClient):
    base_client.token = None
    assert (
        base_client.should_fetch_token("http://www.example.org", withhold_token=True)
        is False
    )


def test_authenticated_httpx_client_fetches_token(client: AuthenticatedHTTPXClient):
    def set_token():
        client.token = True

    client.fetch_token = Mock(side_effect=set_token)
    with patch(
        "authlib.integrations.httpx_client.oauth2_client.OAuth2Client.request"
    ) as request_mock:
        client.get("http://www.example.org")
        client.get("http://www.example.net")  # test that it only fetches a token once

    client.fetch_token.assert_called_once()
    assert request_mock.call_count == 2


@pytest.mark.asyncio
async def test_async_authenticated_httpx_client_fetches_token(
    async_client: AuthenticatedAsyncHTTPXClient,
):
    def set_token():
        async_client.token = True

    async_client.fetch_token = AsyncMock(side_effect=set_token)
    with patch(
        "authlib.integrations.httpx_client.oauth2_client.AsyncOAuth2Client.request"
    ) as request_mock:
        await async_client.get("http://www.example.org")  # test that it only fetches a
        await async_client.get("http://www.example.net")  # token once

    async_client.fetch_token.assert_awaited_once()
    assert request_mock.call_count == 2


def test_integration_sends_token_in_request(
    client: AuthenticatedHTTPXClient,
    respx_mock: MockRouter,
    token_mock: str,
):
    respx_mock.get(
        "http://www.example.org",
        headers={
            "Authorization": f"Bearer {token_mock}",
        },
    )

    response = client.get("http://www.example.org")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_integration_async_sends_token_in_request(
    async_client: AuthenticatedAsyncHTTPXClient,
    respx_mock: MockRouter,
    token_mock: str,
):
    respx_mock.get(
        "http://www.example.org",
        headers={
            "Authorization": f"Bearer {token_mock}",
        },
    )

    response = await async_client.get("http://www.example.org")
    assert response.status_code == 200
