# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Any
from typing import Dict
from typing import Optional
from typing import Type
from typing import Union

import httpx
from gql import Client as GQLClient
from gql.transport import AsyncTransport
from gql.transport import Transport
from pydantic import AnyHttpUrl
from pydantic import parse_obj_as

from raclients import config
from raclients.auth import AuthenticatedAsyncHTTPXClient
from raclients.auth import AuthenticatedHTTPXClient
from raclients.graph.transport import AsyncHTTPXTransport
from raclients.graph.transport import BaseHTTPXTransport
from raclients.graph.transport import HTTPXTransport


class GraphQLClient(GQLClient):
    def __init__(
        self,
        *args: Any,
        url: str = parse_obj_as(AnyHttpUrl, "http://mo:5000/graphql"),
        transport: Optional[Union[Transport, AsyncTransport]] = None,
        sync: bool = False,
        client_args: Optional[Dict[str, Any]] = None,
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
            query = gql(...)
            result = client.execute(query)
            print(result)
        ```

        Authentication parameters can be given directly, instead of being loaded from
        the environment:
        ```
        client_args=dict(
            client_id="AzureDiamond",
            client_secret="hunter2",
            auth_realm="mordor",
            auth_server="http://localhost:8081/auth",
        )
        async with GraphQLClient(
            url="http://os2mo.example.org/graphql",
            client_args=client_args,
        ) as client:
            ...
        ```

        It is alo possible to configure the HTTPX transport manually. Note that the
        'url', 'sync', and 'client_args' parameters are ignored in this case.
        ```
        transport = AsyncHTTPXTransport(
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
        """
        if transport is None:
            transport_cls: Type[BaseHTTPXTransport]  # you happy now, mypy?
            client_cls: Type[Union[httpx.Client, httpx.AsyncClient]]

            if sync:
                transport_cls = HTTPXTransport
                client_cls = AuthenticatedHTTPXClient
            else:
                transport_cls = AsyncHTTPXTransport
                client_cls = AuthenticatedAsyncHTTPXClient

            transport = transport_cls(
                url=url,
                client_cls=client_cls,
                client_args=client_args or config.get_auth_settings().dict(),
            )

        super().__init__(*args, transport=transport, **kwargs)
