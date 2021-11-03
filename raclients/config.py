# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from functools import lru_cache
from typing import Any

from pydantic import AnyHttpUrl
from pydantic import BaseSettings
from pydantic import Field


class AuthSettings(BaseSettings):
    """
    Settings required for authentication against OS2mo.
    """

    client_id: str = "dipex"
    client_secret: str
    auth_realm: str = "mo"
    auth_server: AnyHttpUrl = Field("http://localhost:8081/auth")

    class Config:
        frozen = True


@lru_cache()
def get_auth_settings(*args: Any, **kwargs: Any) -> AuthSettings:
    """
    Defer creation of global auth settings object until it is needed, so we don't error
    on missing values if it never will be.
    """
    return AuthSettings(*args, **kwargs)
