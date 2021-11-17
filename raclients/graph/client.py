# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Any
from typing import Dict
from typing import Optional
from typing import Type
from typing import Union

import httpx
from gql import Client as GQLClient

from raclients.auth import AuthenticatedAsyncHTTPXClient
from raclients.auth import AuthenticatedHTTPXClient
from raclients.graph.transport import AsyncHTTPXTransport
from raclients.graph.transport import BaseHTTPXTransport
from raclients.graph.transport import HTTPXTransport


class GraphQLClient(GQLClient):
    def __init__(
        self,
        url: str,
        client_id: str,
        client_secret: str,
        auth_realm: str,
        auth_server: str,
        *args: Any,
        sync: bool = False,
        httpx_client_kwargs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        """
        GQL Client wrapper providing defaults and automatic authentication for OS2mo.

        Args:
            url: URL of the GraphQL server endpoint.
            client_id: Keycloak client id used for authentication.
            client_secret: Keycloak client secret used for authentication.
            auth_realm: Keycloak auth realm used for authentication.
            auth_server: URL of the Keycloak server used for authentication.
            *args: Extra arguments passed to the superclass init method.
            sync: If true, this client is initialised with a synchronous transport.
            httpx_client_kwargs: Extra keyword arguments passed to the HTTPX client.
            **kwargs: Extra keyword arguments passed to the superclass init method.

        Example:
            Asynchronously::

                client = GraphQLClient(
                    url="http://os2mo.example.org/graphql",
                    client_id="AzureDiamond",
                    client_secret="hunter2",
                    auth_realm="mordor",
                    auth_server="http://keycloak.example.org:8081/auth",
                )
                async with client as session:
                    query = gql(
                        ""'
                        query MOQuery {
                          ...
                        }
                        ""'
                    )
                    result = await session.execute(query)
                    print(result)

            Or synchronously::

                with GraphQLClient(sync=True) as session:
                    result = session.execute(query)
        """
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
            client_args=dict(
                client_id=client_id,
                client_secret=client_secret,
                auth_realm=auth_realm,
                auth_server=auth_server,
                **(httpx_client_kwargs or {}),
            ),
        )

        super().__init__(*args, transport=transport, **kwargs)
