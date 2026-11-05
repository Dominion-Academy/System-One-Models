from dataclasses import dataclass
from enum import StrEnum

from typesafe_sdk import TypeSafeClient

from src.ticketdesk import thresholds
from src.ticketdesk.llm import LLM, classify_with_llm
from src.ticketdesk.typed import Category, TypedTriage, typed_triage


class Route(StrEnum):
    AUTO = "auto"
    LLM = "llm"
    HUMAN = "human"


@dataclass(frozen=True)
class CascadeDecision:
    route: Route
    category: Category | None
    urgent: bool
    triage: TypedTriage


def choose_route(category_probability: float) -> Route:
    if category_probability >= thresholds.CATEGORY_AUTO:
        return Route.AUTO
    if category_probability < thresholds.CATEGORY_HUMAN:
        return Route.HUMAN
    return Route.LLM


def cascade(client: TypeSafeClient, llm: LLM, subject: str, body: str) -> CascadeDecision:
    result = typed_triage(client, subject, body)
    route = choose_route(result.category_probability)
    match route:
        case Route.AUTO:
            category: Category | None = result.category
        case Route.LLM:
            category = classify_with_llm(llm, subject, body)
        case Route.HUMAN:
            category = None
    urgent = result.urgent_probability >= thresholds.URGENT
    return CascadeDecision(route=route, category=category, urgent=urgent, triage=result)
