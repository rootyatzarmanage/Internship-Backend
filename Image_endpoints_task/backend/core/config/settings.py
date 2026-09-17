from functools import lru_cache

from backend.core.config.base import BaseAppSettings


@lru_cache
def get_settings() -> BaseAppSettings:
    return BaseAppSettings()
