from typing import Any

from typesafe_sdk import AsyncTypeSafeClient, TypeSafeClient


def make_client(**options: Any) -> TypeSafeClient:
    # SDK сжимает тела больше 1 КБ через zstd, а laya-serve такие тела не распаковывает (400).
    options.setdefault("compression", False)
    options.setdefault("timeout", 60)
    return TypeSafeClient(**options)


def make_async_client(**options: Any) -> AsyncTypeSafeClient:
    options.setdefault("compression", False)
    options.setdefault("timeout", 60)
    return AsyncTypeSafeClient(**options)
