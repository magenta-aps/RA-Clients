#!/usr/bin/env python3
# --------------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# --------------------------------------------------------------------------------------
from asyncio import run
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Tuple
from typing import Type
from functools import partial

from pydantic import AnyHttpUrl
from ramodels.base import RABase
from ramodels.lora import Facet
from ramodels.lora import Klasse
from ramodels.lora import Organisation

from raclients.modelclientbase import ModelClientBase
from raclients.util import uuid_to_str
from raclients.lora.mox_client import create_mox_helper

# TODO: Change to from ramodels.lora import RABase
LoraBase = Type[RABase]


def scrub(obj: Any, remove_keys: List[str]):
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            if key in remove_keys:
                del obj[key]
            else:
                scrub(obj[key], remove_keys)
    elif isinstance(obj, list):
        for i in reversed(range(len(obj))):
            if obj[i] in remove_keys:
                del obj[i]
            else:
                scrub(obj[i], remove_keys)
    # Neither a dict nor a list, do nothing
    return obj


class InputKlasse(Klasse, extra="ignore"):
    pass


class InputFacet(Facet, extra="ignore"):
    pass


class ModelClient(ModelClientBase):
    def __init__(self, base_url: AnyHttpUrl = "http://localhost:8080", *args, **kwargs):
        super().__init__(base_url, *args, **kwargs)

    def _get_healthcheck_tuples(self) -> List[Tuple[str, str]]:
        return [("/version/", "lora_version")]

    def _get_path_map(self) -> Dict[LoraBase, str]:
        return [Organisation, Facet, Klasse]

    async def read_type(self):
        mox_helper = await create_mox_helper("http://localhost:8080")
        print(await mox_helper.check_connection())
        klasser = await mox_helper.search_klassifikation_klasse({"bvn": "%", "list": "True"})
        validity_scrub = partial(scrub, remove_keys=["from_included", "to_included"])

        for klasse_meta in klasser:
            uuid = klasse_meta["id"]
            klasse = klasse_meta["registreringer"][0]
            print(InputKlasse(
                uuid=uuid,
                **validity_scrub(klasse),
            ))

        facetter = await mox_helper.search_klassifikation_facet({"bvn": "%", "list": "True"})
        for facet_meta in facetter:
            uuid = facet_meta["id"]
            facet = facet_meta["registreringer"][0]
            print(InputFacet(
                uuid=uuid,
                **validity_scrub(facet),
            ))

    async def _post_single_to_backend(
        self, current_type: Type[LoraBase], obj: LoraBase
    ) -> Any:
        """

        :param current_type: Redundant, only pass it because we already have it
        :param obj:
        :return:
        """
        # session = await self._verify_session()

        uuid = obj.uuid
        # TODO, PENDING: https://github.com/samuelcolvin/pydantic/pull/2231
        # for now, uuid is included, and has to be excluded when converted to json
        dictified = obj.dict(by_alias=True, exclude={"uuid"}, exclude_none=True)
        mox_helper = await create_mox_helper("http://localhost:8080")
        print(await mox_helper.check_connection())

        __mox_method_map = {
            Klasse: {
                False: mox_helper.create_klassifikation_klasse,
                True: mox_helper.put_klassifikation_klasse,
            },
            Facet: {
                False: mox_helper.create_klassifikation_facet,
                True: mox_helper.put_klassifikation_facet,
            },
            Organisation: {
                False: mox_helper.create_organisation_organisation,
                True: mox_helper.put_organisation_organisation,
            },
        }

        create_method = __mox_method_map[current_type][uuid is not None]

        if uuid is None:
            return await create_method(dictified)
        else:
            return await create_method(uuid, dictified)

    async def load_lora_objs(
        self, objs: Iterable[LoraBase], disable_progressbar: bool = False
    ) -> List[Any]:
        """
        lazy init client session to ensure created within async context
        :param objs:
        :param disable_progressbar:
        :return:
        """
        return await self._submit_payloads(
            objs, disable_progressbar=disable_progressbar
        )


if __name__ == "__main__":

    async def main():
        client = ModelClient()
        async with client.context():
            from uuid import UUID

            print(await client.read_type())

            organisation = Organisation.from_simplified_fields(
                uuid=UUID("6d9c5332-1f68-9046-0003-d027b0963ba5"),
                name="test_org_name",
                user_key="test_org_user_key",
            )
            print(await client.load_lora_objs([organisation]))

    run(main())
