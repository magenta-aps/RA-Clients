#!/usr/bin/env python3
# --------------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# --------------------------------------------------------------------------------------
from typing import Any
from typing import Iterable
from typing import List

from fastapi.encoders import jsonable_encoder
from ramodels.mo import Employee
from ramodels.mo import FacetClass
from ramodels.mo import OrganisationUnit
from ramodels.mo._shared import MOBase
from ramodels.mo.details import Address
from ramodels.mo.details import Association
from ramodels.mo.details import Engagement
from ramodels.mo.details import EngagementAssociation
from ramodels.mo.details import ITUser
from ramodels.mo.details import KLE
from ramodels.mo.details import Leave
from ramodels.mo.details import Manager
from ramodels.mo.details import Role

from raclients.modelclient.base import ModelBase
from raclients.modelclient.base import ModelClientBase


class ModelClient(ModelClientBase[MOBase]):
    upload_http_method = "POST"
    create_path_map = {
        Address: "/service/details/create",
        Association: "/service/details/create",
        Employee: "/service/e/create",
        Engagement: "/service/details/create",
        EngagementAssociation: "/service/details/create",
        FacetClass: "/service/f/{facet_uuid}/",
        ITUser: "/service/details/create",
        KLE: "/service/details/create",
        Leave: "/service/details/create",
        Manager: "/service/details/create",
        OrganisationUnit: "/service/ou/create",
        Role: "/service/details/create",
    }
    edit_path_map = {
        Address: "/service/details/edit",
        Association: "/service/details/edit",
        Employee: "/service/details/edit",
        Engagement: "/service/details/edit",
        FacetClass: "/service/f/{facet_uuid}/",
        ITUser: "/service/details/edit",
        KLE: "/service/details/edit",
        Leave: "/service/details/edit",
        Manager: "/service/details/edit",
        OrganisationUnit: "/service/details/edit",
        Role: "/service/details/edit",
    }

    def __init__(self, force: bool = False, *args: Any, **kwargs: Any):
        """MO ModelClient.

        Args:
            force: Bypass MO API validation.
            *args: Positional arguments passed through to ModelClientBase.
            **kwargs: Keyword arguments passed through to ModelClientBase.

        Example usage::

            async with ModelClient(
                base_url="http://mo:5000",
                client_id="AzureDiamond",
                client_secret="hunter2",
                auth_server=parse_obj_as(AnyHttpUrl,"http://keycloak.example.org/auth"),
                auth_realm="mordor",
            ) as client:
                r = await client.upload(objects)
        """
        super().__init__(*args, **kwargs)
        self.force = force

    def get_object_url(
        self, obj: ModelBase, *args: Any, edit: bool = False, **kwargs: Any
    ) -> str:
        # Note that we additionally format the object's fields onto the path mapping to
        # support schemes such as /service/f/{facet_uuid}/, where facet_uuid is
        # retrieved from obj.facet_uuid.
        path_map = self.edit_path_map if edit else self.create_path_map
        path = path_map[type(obj)].format_map(obj.dict())
        return f"{path}?force={int(self.force)}"

    def get_object_json(
        self, obj: ModelBase, *args: Any, edit: bool = False, **kwargs: Any
    ) -> Any:
        # 'jsonable_encoder' is used directly on the obj, as 'exclude_defaults' doesn't
        # work when the object is nested within a dict.
        # TODO: Ideally we'd want to use 'exclude_unset' instead of 'exclude_defaults',
        #  but it doesn't seem to work properly with our models.
        if edit:
            obj = {
                "uuid": obj.uuid,
                "type": obj.type_,
                "data": jsonable_encoder(obj, exclude_defaults=True),
            }
        return super().get_object_json(obj, *args, **kwargs)

    async def edit(
        self, objs: Iterable[ModelBase], *args: Any, **kwargs: Any
    ) -> List[Any]:
        return await self.upload(objs, *args, edit=True, **kwargs)
