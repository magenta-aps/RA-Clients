#!/usr/bin/env python3
# --------------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# --------------------------------------------------------------------------------------
from asyncio import run
from typing import Any
from typing import cast
from typing import Dict
from typing import Iterable
from typing import List
from typing import Tuple
from typing import Type

from aiohttp import ClientSession
from jsonschema import validate
from pydantic import AnyHttpUrl
from ramodels.lora import Facet
from ramodels.lora import Klasse
from ramodels.lora import Organisation
from ramodels.lora._shared import LoraBase

from raclients.modelclientbase import ModelClientBase
from raclients.util import uuid_to_str


class ModelClient(ModelClientBase):
    __mox_path_map = {
        Organisation: "/organisation/organisation",
        Facet: "/klassifikation/facet",
        Klasse: "/klassifikation/klasse",
    }

    def __init__(
        self,
        base_url: AnyHttpUrl = AnyHttpUrl("http://localhost:8080"),
        validate: bool = True,
        *args,
        **kwargs,
    ):
        self.validate: bool = validate
        self.schema_cache: Dict[LoraBase, Dict[str, Any]] = {}
        super().__init__(base_url, *args, **kwargs)

    async def _fetch_schema(self, session: ClientSession, url: str) -> Dict[str, Any]:
        """Fetch jsonschema from LoRa."""
        response = await session.get(url)
        response.raise_for_status()
        return cast(Dict[str, Any], await response.json())

    async def _get_schema(
        self, session: ClientSession, current_type: Type[LoraBase]
    ) -> Dict[str, Any]:
        schema = self.schema_cache.get(current_type)
        if schema:
            return schema

        generic_url = self._base_url + self.__mox_path_map[current_type]
        url = generic_url + "/schema"
        schema = await self._fetch_schema(session, url)
        self.schema_cache[current_type] = schema
        return schema

    def _get_healthcheck_tuples(self) -> List[Tuple[str, str]]:
        return [("/version/", "lora_version")]

    def _get_path_map(self) -> Dict[LoraBase, str]:
        return self.__mox_path_map

    async def _post_single_to_backend(
        self, current_type: Type[LoraBase], obj: LoraBase
    ) -> Any:
        """

        :param current_type: Redundant, only pass it because we already have it
        :param obj:
        :return:
        """
        session: ClientSession = await self._verify_session()

        uuid = obj.uuid
        # TODO, PENDING: https://github.com/samuelcolvin/pydantic/pull/2231
        # for now, uuid is included, and has to be excluded when converted to json
        jsonified = uuid_to_str(
            obj.dict(by_alias=True, exclude={"uuid"}, exclude_none=True)
        )
        generic_url = self._base_url + self.__mox_path_map[current_type]

        if self.validate:
            schema = await self._get_schema(session, current_type)
            validate(instance=jsonified, schema=schema)

        if uuid is None:  # post
            async with session.post(
                generic_url,
                json=jsonified,
            ) as response:
                response.raise_for_status()
                return await response.json()
        else:  # put
            async with session.put(
                generic_url + f"/{uuid}",
                json=jsonified,
            ) as response:
                response.raise_for_status()
                return await response.json()

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
