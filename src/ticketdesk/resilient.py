import urllib.error
from dataclasses import dataclass
from typing import Any

from typesafe_sdk import RetryPolicy, TypeSafeClient, TypeSafeError

from src.ticketdesk.client import make_client
from src.ticketdesk.llm import LLM, classify_with_llm
from src.ticketdesk.typed import Category, typed_triage

# Два повтора с паузами 0.2 и 0.4 с, на всё не больше 5 с.
FAST_RETRY = RetryPolicy(max_retries=2, backoff_initial=0.2, backoff_max=1.0, timeout=5.0)
REQUEST_TIMEOUT = 3.0


def make_resilient_client(**options: Any) -> TypeSafeClient:
    options.setdefault("retry", FAST_RETRY)
    options.setdefault("timeout", REQUEST_TIMEOUT)
    return make_client(**options)


@dataclass(frozen=True)
class ResilientResult:
    category: Category | None
    source: str
    error: str | None = None


def resilient_category(
    client: TypeSafeClient, llm: LLM, subject: str, body: str
) -> ResilientResult:
    try:
        result = typed_triage(client, subject, body)
        return ResilientResult(category=result.category, source="system_one")
    except TypeSafeError as error:
        reason = type(error).__name__
    try:
        category = classify_with_llm(llm, subject, body)
        return ResilientResult(category=category, source="llm_fallback", error=reason)
    except (urllib.error.URLError, TimeoutError, KeyError) as error:
        return ResilientResult(None, source="human", error=f"{reason}, {type(error).__name__}")
