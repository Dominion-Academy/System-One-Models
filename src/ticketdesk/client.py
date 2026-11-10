from typing import Any

from typesafe_sdk import AsyncTypeSafeClient, TypeSafeClient

# SDK сжимает тела больше 1 КБ через zstd, а laya-serve такие тела не распаковывает (400).
CLIENT_DEFAULTS: dict[str, Any] = {"compression": False, "timeout": 60}


def make_client(**options: Any) -> TypeSafeClient:
    return TypeSafeClient(**{**CLIENT_DEFAULTS, **options})


def make_async_client(**options: Any) -> AsyncTypeSafeClient:
    return AsyncTypeSafeClient(**{**CLIENT_DEFAULTS, **options})
