from dataclasses import dataclass

from typesafe_sdk import TypeSafeClient

from src.ticketdesk.cascade import CascadeDecision, Route, cascade
from src.ticketdesk.guards import check_input, check_reply
from src.ticketdesk.llm import LLM


@dataclass(frozen=True)
class Outcome:
    action: str
    reasons: list[str]
    decision: CascadeDecision | None = None
    reply: str | None = None


def draft_reply(llm: LLM, subject: str, body: str) -> str:
    prompt = (
        "Write a short, polite first reply to this support ticket. "
        "Do not promise refunds, discounts or deadlines.\n\n"
        f"Subject: {subject}\n\n{body}"
    )
    return llm.complete(prompt)


def handle_ticket(client: TypeSafeClient, llm: LLM, subject: str, body: str) -> Outcome:
    guard = check_input(client, subject, body)
    if not guard.passed:
        return Outcome(action="rejected", reasons=guard.reasons)

    decision = cascade(client, llm, subject, body)
    if decision.route is Route.HUMAN:
        return Outcome(action="human_queue", reasons=["low_confidence"], decision=decision)

    if decision.urgent:
        # Срочный тикет сначала читает оператор: автоответ ему не нужен, ему нужен человек.
        return Outcome(action="human_queue", reasons=["urgent"], decision=decision)

    reply = draft_reply(llm, subject, body)
    reply_guard = check_reply(client, subject, body, reply)
    if not reply_guard.passed:
        return Outcome(
            action="human_review", reasons=reply_guard.reasons, decision=decision, reply=reply
        )
    return Outcome(action="auto_reply", reasons=[], decision=decision, reply=reply)
