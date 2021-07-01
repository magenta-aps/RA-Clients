#!/usr/bin/env python3
# --------------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# --------------------------------------------------------------------------------------
from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import AnyHttpUrl
from ramodels.mo import Employee

from raclients import __version__
from raclients.mo import ModelClient
from raclients.modelclientbase import common_session_factory


def test_version():
    assert __version__ == "0.3.2"


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


def test_common_session():
    assert common_session_factory()
