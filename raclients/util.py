#!/usr/bin/env python3
# --------------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# --------------------------------------------------------------------------------------
from typing import Any
from uuid import UUID

JSON = Any


def uuid_to_str(data: JSON) -> JSON:
    if isinstance(data, str) or isinstance(data, int) or data is None:
        return data
    elif isinstance(data, UUID):
        return str(data)
    elif isinstance(data, list):
        return list(map(uuid_to_str, data))
    elif isinstance(data, dict):
        return {key: uuid_to_str(value) for key, value in data.items()}
    raise TypeError(f"unexpected type: {type(data)}")
