# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Any
from typing import Optional

from authlib.integrations.httpx_client import (
    AsyncOAuth2Client as AsyncHTTPXOAuth2Client,
)
from authlib.integrations.httpx_client import OAuth2Client as HTTPXOAuth2Client
from authlib.oauth2 import OAuth2Client
from pydantic import AnyHttpUrl

from raclients import config


class BaseAuthenticatedClient(OAuth2Client):
    def __init__(
        self,
        *args: Any,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        auth_server: Optional[AnyHttpUrl] = None,
        auth_realm: Optional[str] = None,
        grant_type: Optional[str] = "client_credentials",
        token_endpoint_auth_method: Optional[str] = "client_secret_post",
        **kwargs: Any
    ):
        """
        Base used to implement authenticated HTTPX clients. Does not work on its own.

        Args:
            client_id: Optional client identifier used to obtain tokens. Uses value from
                       environment if not given.
            client_secret: Optional client secret used to obtain tokens. Uses value from
                           environment if not given.
            auth_server: Optional HTTP URL of the authentication server. Uses value from
                        environment if not given.
            auth_realm: Optional keycloak realm used for authentication. Uses value from
                        environment if not given.
            *args: Other arguments, passed to Authlib's OAuth2Client.
            grant_type: OAuth2 grant type.
            token_endpoint_auth_method: RFC7591 client authentication method. Authlib
                                        supports 'client_secret_basic' (default),
                                        'client_secret_post', and None.
            **kwargs: Other keyword arguments, passed to Authlib's OAuth2Client.
        """
        self.auth_server = auth_server or config.get_auth_settings().auth_server
        self.auth_realm = auth_realm or config.get_auth_settings().auth_realm

        super().__init__(
            *args,
            client_id=client_id or config.get_auth_settings().client_id,
            client_secret=client_secret or config.get_auth_settings().client_secret,
            grant_type=grant_type,
            token_endpoint=self.token_endpoint,
            token_endpoint_auth_method=token_endpoint_auth_method,
            **kwargs,
        )

    @property
    def token_endpoint(self) -> str:
        """
        Returns: Token endpoint based on given auth server and realm. Currently only
                 supports keycloak.
        """
        return "{server}/realms/{realm}/protocol/openid-connect/token".format(
            server=self.auth_server,
            realm=self.auth_realm,
        )

    def should_fetch_token(self, url: str, withhold_token: bool = False) -> bool:
        """
        Determine if we should fetch a token. Authlib automatically _refreshes_ tokens,
        but it does not fetch the initial one. Therefore, we should fetch a token the
        first time a request is sent; i.e. when self.token is None.

        Args:
            url: The URL of the request we are in the context of. Used to avoid
                 recursion, since fetching a token also uses our caller self.request().
            withhold_token: Forwarded from `self.request(..., withhold_token=False)`. If
                            this is set, Authlib does not pass a token in the request,
                            in which case there is no need to fetch one either.

        Returns: True if a token should be fetched. False otherwise.
        """
        return not withhold_token and self.token is None and url != self.token_endpoint


class AuthenticatedHTTPXClient(BaseAuthenticatedClient, HTTPXOAuth2Client):
    """
    Synchronous HTTPX Client that automatically authenticates requests.

    Example usage, with configuration from environment variables:
    ```
    with AuthenticatedHTTPXClient() as client:
        r = client.get("https://example.org")
    ```
    or with explicit configuration:
    ```
    with AuthenticatedHTTPXClient(
        client_id="AzureDiamond",
        client_secret="hunter2",
        auth_server=parse_obj_as(AnyHttpUrl, "http://keycloak.example.org/auth"),
        auth_realm="mordor",
    ) as client:
        r = client.get("https://example.org")
    ```
    """

    def request(
        self, method: str, url: str, withhold_token: bool = False, **kwargs: Any
    ) -> Any:
        """
        Decorate Authlib's OAuth2Client.request() to automatically fetch a token the
        first time a request is made. `withhold_token` is extracted from the arguments
        since it is needed to determine if we should fetch_token().
        """
        if self.should_fetch_token(url, withhold_token):
            self.fetch_token()
        return super().request(method, url, withhold_token, **kwargs)


class AuthenticatedAsyncHTTPXClient(BaseAuthenticatedClient, AsyncHTTPXOAuth2Client):
    """
    Asynchronous HTTPX Client that automatically authenticates requests.

    Example usage, with configuration from environment variables:
    ```
    async with AuthenticatedAsyncHTTPXClient() as client:
        r = client.get("https://example.org")
    ```
    or with explicit configuration:
    ```
    async with AuthenticatedAsyncHTTPXClient(
        client_id="AzureDiamond",
        client_secret="hunter2",
        auth_server=parse_obj_as(AnyHttpUrl, "http://keycloak.example.org/auth"),
        auth_realm="mordor",
    ) as client:
        r = client.get("https://example.org")
    ```
    """

    async def request(
        self, method: str, url: str, withhold_token: bool = False, **kwargs: Any
    ) -> Any:
        """
        Decorate Authlib's AsyncOAuth2Client.request() to automatically fetch a token
        the first time a request is made. `withhold_token` is extracted from the
        arguments since it is needed to determine if we should fetch_token().
        """
        if self.should_fetch_token(url, withhold_token):
            await self.fetch_token()
        return await super().request(method, url, withhold_token, **kwargs)
