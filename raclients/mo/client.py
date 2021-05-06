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
from uuid import UUID

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

MoObj = Type[RABase]


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
        return [("/version", "mo_version")]

    def _get_path_map(self) -> Dict[RABase, str]:
        return self.__mo_path_map

    async def _post_single_to_backend(self, current_type: Type[MoObj], obj: MoObj):
        session = await self._verify_session()

        async with session.post(
            self._base_url + self.__mo_path_map[current_type],
            json=uuid_to_str(obj.dict(by_alias=True)),
        ) as response:
            response.raise_for_status()

    async def load_mo_objs(
        self, objs: Iterable[MoObj], disable_progressbar: bool = False
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
        client = ModelClient()
        async with client.context():
            await client.load_mo_objs(
                [
                    Employee.from_simplified_fields(
                        uuid=UUID("456362c4-0ee4-4e5e-a72c-751239745e64"),
                        name="test_org_name",
                        user_key="test_org_user_key",
                    )
                ]
            )

    run(main())
