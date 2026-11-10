"""Запуск handle_ticket с записью каждого обращения к Laya и к LLM."""

import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from typesafe_sdk import TypeSafeClient, TypeSafeError

from src.ticketdesk import typed
from src.ticketdesk.app.settings import Settings
from src.ticketdesk.client import CLIENT_DEFAULTS
from src.ticketdesk.llm import CLASSIFY_PROMPT_START, LLM
from src.ticketdesk.pipeline import Outcome, handle_ticket
from src.ticketdesk.resilient import FAST_RETRY

# Ошибки, после которых тикет остаётся без решения: недоступный сервер, таймаут, неверный ответ.
HANDLED_ERRORS = (TypeSafeError, OSError, KeyError, ValueError)


@dataclass
class SystemOneCall:
    kind: str  # input_guard, classification, output_guard
    state: str
    seconds: float
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    nouls: dict[str, float] = field(default_factory=dict)
    choices: dict[str, dict[str, float]] = field(default_factory=dict)
    scores: dict[str, dict[str, float]] = field(default_factory=dict)
    error: str | None = None


@dataclass
class LLMCall:
    kind: str  # llm_classify, llm_reply
    prompt: str
    seconds: float
    reply: str = ""
    error: str | None = None


Call = SystemOneCall | LLMCall


@dataclass
class TicketReport:
    subject: str
    body: str
    calls: list[Call]
    seconds: float
    outcome: Outcome | None = None
    error: str | None = None


def describe_error(error: Exception) -> str:
    return f"{type(error).__name__}: {error}"


def system_one_kind(question_names: set[str]) -> str:
    if "spam" in question_names:
        return "input_guard"
    if "promise" in question_names:
        return "output_guard"
    return "classification"


class TracingClient(TypeSafeClient):
    """Обычный клиент Laya, который кладёт каждый вызов system_one в список calls."""

    def __init__(self, calls: list[Call], **options: Any) -> None:
        super().__init__(**{**CLIENT_DEFAULTS, **options})
        self._calls = calls

    def system_one(self, state: Any, questions: Mapping[str, Any], **kwargs: Any) -> Any:
        call = SystemOneCall(kind=system_one_kind(set(questions)), state=str(state), seconds=0.0)
        started = time.perf_counter()
        try:
            response = super().system_one(state, questions, **kwargs)
        except Exception as error:
            call.seconds = time.perf_counter() - started
            call.error = describe_error(error)
            self._calls.append(call)
            raise
        call.seconds = time.perf_counter() - started
        call.model = response.model
        call.input_tokens = response.usage.input_tokens
        call.output_tokens = response.usage.output_tokens
        call.nouls = {name: answer.noul for name, answer in response.nouls.items()}
        call.choices = {
            name: {str(option): p for option, p in answer.probabilities.items()}
            for name, answer in response.choices.items()
        }
        call.scores = {
            name: {str(level): p for level, p in answer.probabilities.items()}
            for name, answer in response.scores.items()
        }
        self._calls.append(call)
        return response


class TracingLLM:
    def __init__(self, inner: LLM, calls: list[Call]) -> None:
        self.inner = inner
        self.calls = calls

    def complete(self, prompt: str) -> str:
        kind = "llm_classify" if prompt.startswith(CLASSIFY_PROMPT_START) else "llm_reply"
        call = LLMCall(kind=kind, prompt=prompt, seconds=0.0)
        started = time.perf_counter()
        try:
            call.reply = self.inner.complete(prompt)
        except Exception as error:
            call.error = describe_error(error)
            raise
        finally:
            call.seconds = time.perf_counter() - started
            self.calls.append(call)
        return call.reply


def make_tracing_client(calls: list[Call], settings: Settings, **options: Any) -> TracingClient:
    if settings.retry:
        options.setdefault("retry", FAST_RETRY)
    return TracingClient(
        calls,
        base_url=settings.laya_url.strip(),
        api_key=settings.laya_key.strip(),
        model=settings.laya_model.strip(),
        **options,
    )


def analyze(settings: Settings, subject: str, body: str) -> TicketReport:
    calls: list[Call] = []
    llm = TracingLLM(settings.make_llm(), calls)
    started = time.perf_counter()
    report = TicketReport(subject=subject, body=body, calls=calls, seconds=0.0)
    with make_tracing_client(calls, settings) as client:
        try:
            report.outcome = handle_ticket(client, llm, subject, body)
        except HANDLED_ERRORS as error:
            report.error = describe_error(error)
    report.seconds = time.perf_counter() - started
    return report


def check_connection(settings: Settings) -> list[tuple[bool, str]]:
    """Проверяет System One и LLM. Возвращает пары «успех, сообщение»."""
    results: list[tuple[bool, str]] = []
    with make_tracing_client([], settings, timeout=10) as client:
        try:
            response = client.system_one(
                state="ping", questions={"urgent": typed.URGENT}, timeout=10
            )
            results.append((True, f"System One отвечает, модель {response.model}."))
        except HANDLED_ERRORS as error:
            results.append((False, f"System One недоступна: {describe_error(error)}"))
    if settings.uses_stub_llm:
        results.append((True, "Ключ LLM не задан: используется заглушка StubLLM."))
    else:
        try:
            answer = settings.make_llm().complete("Answer with one word: ok")
            results.append((True, f"LLM отвечает: {answer[:60]!r}"))
        except HANDLED_ERRORS as error:
            results.append((False, f"LLM недоступна: {describe_error(error)}"))
    return results
