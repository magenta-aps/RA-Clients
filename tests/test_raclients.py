#!/usr/bin/env python3
# --------------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# --------------------------------------------------------------------------------------
from datetime import datetime
from uuid import uuid4

import pytest
from aiohttp import ClientResponseError
from pydantic import AnyHttpUrl
from ramodels.mo import Employee
from ramodels.mo import FacetClass

from raclients.mo import ModelClient
from raclients.modelclientbase import common_session_factory


@pytest.mark.asyncio
async def test_request(aioresponses):
    ok_response = {"any": "thing"}

    aioresponses.get(
        "http://example.com/version/", status=200, payload={"mo_version": "1"}
    )
    aioresponses.post(
        "http://example.com/service/e/create?force=0",
        status=200,
        payload=ok_response,
    )

    client = ModelClient(
        AnyHttpUrl("http://example.com", scheme="http", host="example.com")
    )
    async with client.context():
        resp = await client.load_mo_objs(
            objs=[
                Employee(
                    uuid=uuid4(),
                    givenname="given name",
                    surname="surname",
                    cpr_no=None,
                    seniority=datetime(2000, 1, 1),
                )
            ],
            disable_progressbar=True,
        )

        assert [ok_response] == resp


@pytest.mark.asyncio
async def test_uuid_request(aioresponses):
    ok_response = {"good": "job"}

    aioresponses.get(
        "http://example.com/version/", status=200, payload={"mo_version": "1"}
    )
    aioresponses.post(
        "http://example.com/service/f/00000000-0000-0000-0000-000000000000/?force=0",
        status=200,
        payload=ok_response,
    )

    client = ModelClient(
        AnyHttpUrl("http://example.com", scheme="http", host="example.com")
    )
    async with client.context():
        resp = await client.load_mo_objs(
            objs=[
                FacetClass(
                    facet_uuid="00000000-0000-0000-0000-000000000000",
                    name="My Awesome Class",
                    user_key="MyClass",
                    scope="TEXT",
                    org_uuid="11111111-1111-1111-1111-111111111111",
                )
            ],
            disable_progressbar=True,
        )

        assert [ok_response] == resp


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_fail_request(aioresponses):
    aioresponses.get(
        "http://example.com/version/", status=200, payload={"mo_version": "1"}
    )
    err_response = {"description": "error"}
    aioresponses.post(
        "http://example.com/service/e/create?force=0",
        status=404,
        payload=err_response,
    )
    client = ModelClient(
        AnyHttpUrl("http://example.com", scheme="http", host="example.com")
    )
    async with client.context():
        with pytest.raises(
            ClientResponseError, match=f"message='{err_response['description']}'"
        ):
            await client.load_mo_objs(
                objs=[
                    Employee(
                        uuid=uuid4(),
                        givenname="given name",
                        surname="surname",
                        cpr_no=None,
                        seniority=datetime(2000, 1, 1),
                    )
                ],
                disable_progressbar=True,
            )
    aioresponses.get(
        "http://example.com/version/", status=200, payload={"mo_version": "1"}
    )
    aioresponses.post(
        "http://example.com/service/e/create?force=0",
        status=404,
        payload={"oh": "no"},
    )
    async with client.context():
        with pytest.raises(ClientResponseError, match="message='Not Found'"):
            await client.load_mo_objs(
                objs=[
                    Employee(
                        uuid=uuid4(),
                        givenname="given name",
                        surname="surname",
                        cpr_no=None,
                        seniority=datetime(2000, 1, 1),
                    )
                ],
                disable_progressbar=True,
            )


def test_common_session():
    assert common_session_factory()
