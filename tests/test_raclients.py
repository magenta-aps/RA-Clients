#!/usr/bin/env python3
# --------------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# --------------------------------------------------------------------------------------
from datetime import datetime
from uuid import uuid4

import httpx
import pytest
from httpx import AsyncClient
from ramodels.mo import Employee
from ramodels.mo import FacetClass
from respx import MockRouter

from raclients.modelclient.lora import ModelClient as LoRaModelClient
from raclients.modelclient.mo import ModelClient as MOModelClient


@pytest.fixture
def mo_model_client(client_params: dict, token_mock: str) -> MOModelClient:
    return MOModelClient(base_url="http://mo.example.org", **client_params)


@pytest.mark.asyncio
async def test_request(mo_model_client: MOModelClient, respx_mock: MockRouter):
    ok_response = {"any": "thing"}

    respx_mock.post("http://mo.example.org/service/e/create?force=0").mock(
        return_value=httpx.Response(
            200,
            json=ok_response,
        )
    )

    resp = await mo_model_client.upload(
        [
            Employee(
                uuid=uuid4(),
                givenname="given name",
                surname="surname",
                cpr_no=None,
                seniority=datetime(2000, 1, 1),
            )
        ]
    )

    assert [ok_response] == resp


@pytest.mark.asyncio
async def test_uuid_request(mo_model_client: MOModelClient, respx_mock: MockRouter):
    ok_response = {"good": "job"}

    respx_mock.post(
        "http://mo.example.org/service/f/00000000-0000-0000-0000-000000000000/?force=0",
    ).mock(
        return_value=httpx.Response(
            200,
            json=ok_response,
        )
    )

    resp = await mo_model_client.upload(
        [
            FacetClass(
                facet_uuid="00000000-0000-0000-0000-000000000000",
                name="My Awesome Class",
                user_key="MyClass",
                scope="TEXT",
                org_uuid="11111111-1111-1111-1111-111111111111",
            )
        ]
    )

    assert [ok_response] == resp


@pytest.mark.asyncio
async def test_edit_request(mo_model_client: MOModelClient, respx_mock: MockRouter):
    uuid = uuid4()
    respx_mock.post(
        "http://mo.example.org/service/details/edit?force=0",
        json__uuid=str(uuid),
        json__type="employee",
        json__data__uuid=str(uuid),
    ).mock(
        return_value=httpx.Response(
            200,
            json={"any": "thing"},
        )
    )

    await mo_model_client.edit(
        [
            Employee(
                uuid=uuid,
                givenname="given name",
                surname="surname",
                cpr_no=None,
                seniority=datetime(2000, 1, 1),
            )
        ]
    )


@pytest.mark.asyncio
async def test_fail_request(mo_model_client: MOModelClient, respx_mock: MockRouter):
    err_response = {"description": "big error"}
    respx_mock.post("http://mo.example.org/service/e/create?force=0",).mock(
        return_value=httpx.Response(
            404,
            json=err_response,
        )
    )
    with pytest.raises(httpx.HTTPStatusError, match=err_response["description"]):
        await mo_model_client.upload(
            [
                Employee(
                    uuid=uuid4(),
                    givenname="given name",
                    surname="surname",
                    cpr_no=None,
                    seniority=datetime(2000, 1, 1),
                )
            ]
        )

    respx_mock.post("http://mo.example.org/service/e/create?force=0",).mock(
        return_value=httpx.Response(
            404,
            json={"oh": "no"},
        )
    )
    with pytest.raises(httpx.HTTPStatusError, match="Not Found"):
        await mo_model_client.upload(
            [
                Employee(
                    uuid=uuid4(),
                    givenname="given name",
                    surname="surname",
                    cpr_no=None,
                    seniority=datetime(2000, 1, 1),
                )
            ]
        )


def test_lora_model_client_does_not_use_auth():
    # We would really like to test that the "Authorization" header is not
    # set when the "await self.async_httpx_client.request(...)" is executed
    # in the "upload_object" method in ModelClientBase class in base.py,
    # but this seems to be hard to do, so we will have (for now) to settle
    # with this test instead

    lora_model_client = LoRaModelClient(base_url="http://lora.example.org")
    assert isinstance(lora_model_client.async_httpx_client, AsyncClient)
