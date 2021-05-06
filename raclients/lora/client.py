#!/usr/bin/env python3
# --------------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# --------------------------------------------------------------------------------------
from asyncio import run
from typing import Dict
from typing import Iterable
from typing import List
from typing import Tuple
from typing import Type

from pydantic import AnyHttpUrl
from ramodels.base import RABase
from ramodels.lora import Facet
from ramodels.lora import Klasse
from ramodels.lora import Organisation

from raclients.modelclientbase import ModelClientBase
from raclients.util import uuid_to_str

LoraObj = Type[RABase]


class ModelClient(ModelClientBase):
    __mox_path_map = {
        Organisation: "/organisation/organisation",
        Facet: "/klassifikation/facet",
        Klasse: "/klassifikation/klasse",
    }

    def __init__(self, base_url: AnyHttpUrl = "http://localhost:8080", *args, **kwargs):
        super().__init__(base_url, *args, **kwargs)

    def _get_healthcheck_tuples(self) -> List[Tuple[str, str]]:
        return [("/version", "lora_version")]

    def _get_path_map(self) -> Dict[RABase, str]:
        return self.__mox_path_map

    async def _post_single_to_backend(self, current_type: Type[LoraObj], obj: LoraObj):
        """

        :param current_type: Redundant, only pass it because we already have it
        :param obj:
        :return:
        """
        session = await self._verify_session()

        uuid = obj.get_uuid()
        # TODO, PENDING: https://github.com/samuelcolvin/pydantic/pull/2231
        # for now, uuid is included, and has to be excluded when converted to json
        jsonified = uuid_to_str(
            obj.dict(by_alias=True, exclude={"uuid"}, exclude_none=True)
        )
        generic_url = self._base_url + self.__mox_path_map[current_type]
        if uuid is None:  # post
            async with session.post(
                generic_url,
                json=jsonified,
            ) as response:
                response.raise_for_status()
        else:  # put
            async with session.put(
                generic_url + f"/{uuid}",
                json=jsonified,
            ) as response:
                response.raise_for_status()

    async def load_lora_objs(
        self, objs: Iterable[LoraObj], disable_progressbar: bool = False
    ):
        """
        lazy init client session to ensure created within async context
        :param objs:
        :param disable_progressbar:
        :return:
        """
        await self._submit_payloads(objs, disable_progressbar=disable_progressbar)


if __name__ == "__main__":

    async def main():
        client = ModelClient(base_url="https://morademo.magenta.dk")
        async with client.context():
            pass
            # await client.load_lora_objs(
            #    [
            #        Organisation.from_simplified_fields(
            #            uuid=UUID("456362c4-0ee4-4e5e-a72c-751239745e64"),
            #            name="test_org_name",
            #            user_key="test_org_user_key",
            #        )
            #    ]
            # )

    run(main())
