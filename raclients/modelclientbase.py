#!/usr/bin/env python3
# --------------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# --------------------------------------------------------------------------------------
from abc import ABC
from abc import abstractmethod
from asyncio import as_completed
from asyncio import gather
from asyncio import sleep
from contextlib import asynccontextmanager
from itertools import groupby
from itertools import starmap
from typing import Callable
from typing import Coroutine
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type

from aiohttp import ClientSession
from aiohttp import TCPConnector
from more_itertools import chunked
from pydantic import AnyHttpUrl
from ramodels.base import RABase
from tqdm import tqdm


class ModelClientBase(ABC):
    def __init__(
        self,
        base_url: AnyHttpUrl,
        session_factory: Callable[[], ClientSession] = lambda: ClientSession(
            connector=TCPConnector(limit=20)
        ),
        chunk_size: int = 100,
    ):
        # connection logic
        self._base_url = base_url
        self._chunk_size = chunk_size
        self._session_factory = session_factory
        self._session: Optional[ClientSession] = None

    @asynccontextmanager
    async def context(self):
        try:
            async with self._session_factory() as session:
                self._session = session
                await self.__check_if_server_online()

                yield
        finally:
            self._session = None

    async def _verify_session(self) -> ClientSession:
        if self._session is None:
            raise Exception("Need to initialize client session!")
        return self._session

    async def __check_if_server_online(self, attempts=100, delay=1) -> None:
        """Check if backend is online.

        :param attempts: Number of repeats
        :param delay: Number of sleeps in-between
        :return:
        """
        await self._verify_session()
        async with self._session_factory() as session:

            async def check_endpoint(url, response):
                for _ in range(attempts):
                    try:
                        resp = await session.get(url)
                        resp.raise_for_status()
                        if response in await resp.json():
                            return
                        raise Exception("Invalid response")
                    except Exception as exp:
                        print(exp)
                        await sleep(delay)
                raise Exception("Unable to connect")

            healthcheck_tuples = self._get_healthcheck_tuples()
            healthcheck_tuples = [
                (self._base_url + subpath, response)
                for subpath, response in healthcheck_tuples
            ]
            tasks = starmap(check_endpoint, healthcheck_tuples)
            await gather(*tasks)

    async def _post_to_backend(
        self, current_type: Type[RABase], data: Iterable[RABase]
    ):
        """
        wrapper allows passing list of mox objs, for individual posting
        :param current_type:
        :param data:
        :return:
        """
        await self._verify_session()
        await gather(
            *map(
                lambda obj: self._post_single_to_backend(
                    current_type=current_type, obj=obj
                ),
                data,
            )
        )

    async def __submit(self, data: Iterable[RABase]):
        """
        maps the object appropriately to either MO or LoRa

        :param data: An iterable of objects of the *same* type!
        :return:
        """

        data = list(data)
        current_type = type(data[0])

        assert all([isinstance(obj, current_type) for obj in data])

        if current_type in self._get_path_map():
            await self._post_to_backend(current_type, data)
            return

        raise TypeError(f"unknown type: {current_type}")

    async def _submit_payloads(self, objs: Iterable[RABase], disable_progressbar=False):
        objs = list(objs)
        groups = groupby(objs, lambda x: type(x).__name__)
        chunked_groups: List[Tuple[str, Iterable[List[RABase]]]] = [
            (type_name, list(chunked(objs, self._chunk_size)))
            for type_name, objs in groups
        ]
        chunked_tasks: List[Tuple[str, List[Coroutine]]] = [
            (type_name, list(map(self.__submit, chunks)))
            for type_name, chunks in chunked_groups
        ]
        if not chunked_tasks or all([not tasks for _, tasks in chunked_tasks]):
            return
        for key, tasks in chunked_tasks:
            for f in tqdm(
                as_completed(tasks),
                total=len(tasks),
                unit="chunk",
                desc=key,
                disable=disable_progressbar,
            ):
                await f

    @abstractmethod
    def _get_healthcheck_tuples(self) -> List[Tuple[str, str]]:
        pass

    @abstractmethod
    def _get_path_map(self) -> Dict[RABase, str]:
        pass

    @abstractmethod
    async def _post_single_to_backend(self, current_type: Type[RABase], obj: RABase):
        pass
