# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import httpx
import pytest
from gql import gql
from pydantic import AnyHttpUrl
from pydantic import parse_obj_as
from respx import MockRouter

from raclients.graph.client import GraphQLClient
from raclients.graph.transport import HTTPXTransport

url = parse_obj_as(AnyHttpUrl, "https://os2mo.example.org/gql")


@pytest.fixture
def query_data(token_mock: str, respx_mock: MockRouter) -> dict:
    data = {"a": 1}
    respx_mock.post(
        url=url,
        json={
            "query": "query MOQuery {\n  users {\n    id\n  }\n}\n",
        },
        headers={
            "Authorization": f"Bearer {token_mock}",
        },
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": data,
            },
        )
    )

    return data


def test_init_client(client_params_env: dict):
    with GraphQLClient(url=url, sync=True):
        pass


@pytest.mark.asyncio
async def test_init_async_client(client_params_env: dict):
    async with GraphQLClient(url=url):
        pass


def test_init_client_with_client_args():
    client_args = dict(
        client_id="a",
        client_secret="b",
        auth_server="c",
        auth_realm="d",
    )
    with GraphQLClient(url=url, sync=True, client_args=client_args) as client:
        assert client.transport.client_args == client_args


def test_init_client_with_transport():
    transport = HTTPXTransport(
        url="http://localhost:5000/graphql",
        client_cls=httpx.Client,
    )
    with GraphQLClient(transport=transport):
        pass


def test_integration_client(client_params_env: dict, token_mock: str, query_data: dict):
    with GraphQLClient(url=url, sync=True) as client:
        query = gql(
            """
            query MOQuery {
                users {
                    id
                }
            }
            """
        )
        result = client.execute(query)
        assert result == query_data


@pytest.mark.asyncio
async def test_integration_async_client(
    client_params_env: dict, token_mock: str, query_data: dict
):
    async with GraphQLClient(url=url) as client:
        query = gql(
            """
            query MOQuery {
                users {
                    id
                }
            }
            """
        )
        result = await client.execute(query)
        assert result == query_data
