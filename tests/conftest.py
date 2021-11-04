# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Generator

import httpx
import pytest
from pydantic import AnyHttpUrl
from pydantic import parse_obj_as
from respx import MockRouter

from raclients.config import get_auth_settings


@pytest.fixture
def client_params() -> dict:
    return dict(
        client_id="AzureDiamond",
        client_secret="hunter2",
        auth_server=parse_obj_as(AnyHttpUrl, "http://keycloak.example.org/auth"),
        auth_realm="mordor",
    )


@pytest.fixture
def client_params_env(client_params: dict, monkeypatch) -> Generator[dict, None, None]:
    monkeypatch.setenv("CLIENT_ID", client_params["client_id"])
    monkeypatch.setenv("CLIENT_SECRET", client_params["client_secret"])
    monkeypatch.setenv("AUTH_SERVER", client_params["auth_server"])
    monkeypatch.setenv("AUTH_REALM", client_params["auth_realm"])
    yield client_params
    get_auth_settings.cache_clear()  # ensure we don't leak into other tests


@pytest.fixture
def token_mock(client_params: dict, monkeypatch, respx_mock: MockRouter) -> str:
    token = "my_token"
    url = "{server}/realms/{realm}/protocol/openid-connect/token".format(
        server=client_params["auth_server"],
        realm=client_params["auth_realm"],
    )

    respx_mock.post(
        url=url,
        content=(
            "grant_type=client_credentials"
            "&client_id={client_id}"
            "&client_secret={client_secret}".format(
                **client_params,
            )
        ),
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "token_type": "Bearer",
                "access_token": token,
            },
        )
    )

    return token
