#!/usr/bin/env python3
# --------------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# --------------------------------------------------------------------------------------
from typing import Any
from typing import Dict
from typing import Tuple

from gql import Client as GQLClient
from gql.transport.aiohttp import AIOHTTPTransport
from pydantic import AnyHttpUrl


class GraphQLClient(GQLClient):
    def __init__(
        self,
        *args: Tuple[Any],
        base_url: AnyHttpUrl = AnyHttpUrl(
            "http://localhost:5000/graphql", scheme="http", host="localhost"
        ),
        **kwargs: Dict[str, Any]
    ):
        """
        Wrapper for GQL's Client, providing defaults for OS2mo.

        Usage:
        ```
        async with GraphQLClient() as session:
            query = gql(
                "" "
                query MyQuery {
                  ...
                }
                "" "
            )
            result = await session.execute(query)
            print(result)
        ```
        """
        super().__init__(*args, transport=AIOHTTPTransport(url=base_url), **kwargs)
