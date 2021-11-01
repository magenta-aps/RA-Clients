# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from asyncio import Transport
from typing import Any
from typing import Optional
from typing import Union

from gql import Client as GQLClient
from gql.transport import AsyncTransport
from pydantic import AnyHttpUrl
from pydantic import parse_obj_as

from raclients import config
from raclients.auth import AuthenticatedAsyncHTTPXClient
from raclients.auth import AuthenticatedHTTPXClient
from raclients.graph.transport import AsyncHTTPXTransport
from raclients.graph.transport import HTTPXTransport


class GraphQLClient(GQLClient):
    def __init__(
        self,
        *args: Any,
        url: str = parse_obj_as(AnyHttpUrl, "http://mo:5000/graphql"),
        transport: Optional[Union[Transport, AsyncTransport]] = None,
        sync: bool = False,
        **kwargs: Any,
    ):
        """
        GQL Client wrapper, providing defaults and automatic authentication for OS2mo.

        Usage, with automatic authentication from environment variables:
        ```
        async with GraphQLClient(url="http://os2mo.example.org/graphql") as client:
            query = gql(
                ""'
                query MOQuery {
                  ...
                }
                ""'
            )
            result = await client.execute(query)
            print(result)
        ```

        Or synchronously:
        ```
        with GraphQLClient(sync=True) as client:
            query = gql(
                ""'
                query MOQuery {
                  ...
                }
                ""'
            )
            result = client.execute(query)
            print(result)
        ```

        The HTTPX transport can also be configured manually:
        ```
        transport = AuthenticatedAsyncHTTPXClient(
            url="http://localhost:5000/graphql",
            client_cls=AuthenticatedAsyncHTTPXClient,
            client_args=dict(
                client_id="AzureDiamond",
                client_secret="hunter2",
                auth_realm="mordor",
                auth_server="http://localhost:8081/auth",
            )
        )
        async with GraphQLClient(transport=transport) as client:
            ...
        ```
        note that the 'url' and 'sync' parameters are ignored in this case.
        """
        if transport is None:
            if sync:
                transport = HTTPXTransport(
                    url=url,
                    client_cls=AuthenticatedHTTPXClient,
                    client_args=config.get_auth_settings().dict(),
                )
            else:
                transport = AsyncHTTPXTransport(
                    url=url,
                    client_cls=AuthenticatedAsyncHTTPXClient,
                    client_args=config.get_auth_settings().dict(),
                )
        super().__init__(*args, transport=transport, **kwargs)
