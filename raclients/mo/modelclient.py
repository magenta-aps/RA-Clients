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

from pydantic import AnyHttpUrl
from ramodels.base import RABase
from ramodels.mo import Address
from ramodels.mo import Employee
from ramodels.mo import Engagement
from ramodels.mo import EngagementAssociation
from ramodels.mo import Manager
from ramodels.mo import OrganisationUnit

from raclients.modelclientbase import ModelClientBase
from raclients.util import uuid_to_str

# TODO: Change to from ramodels.mo import MOBase
MOBase = Type[RABase]


class ModelClient(ModelClientBase):
    __mo_path_map = {
        OrganisationUnit: "/service/ou/create",
        Employee: "/service/e/create",
        Engagement: "/service/details/create",
        EngagementAssociation: "/service/details/create",
        Manager: "/service/details/create",
        Address: "/service/details/create",
    }

    def __init__(self, base_url: AnyHttpUrl = "http://localhost:5000", *args, **kwargs):
        super().__init__(base_url, *args, **kwargs)

    def _get_healthcheck_tuples(self) -> List[Tuple[str, str]]:
        return [("/version/", "mo_version")]

    def _get_path_map(self) -> Dict[MOBase, str]:
        return self.__mo_path_map

    async def _post_single_to_backend(
        self, current_type: Type[MOBase], obj: MOBase
    ) -> Any:
        session = await self._verify_session()

        async with session.post(
            self._base_url + self.__mo_path_map[current_type],
            json=uuid_to_str(obj.dict(by_alias=True)),
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def load_mo_objs(
        self, objs: Iterable[MOBase], disable_progressbar: bool = False
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

            employee = Employee(
                uuid=UUID("456362c4-0ee4-4e5e-a72c-751239745e64"),
                name="Brian Orskov",
            )
            print(await client.load_mo_objs([employee]))

    run(main())
