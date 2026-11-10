"""Итоги пакета: калибровка, стоимость и журнал решений на готовых модулях ticketdesk."""

from dataclasses import dataclass
from pathlib import Path

from src.modules.m5_production.cost_per_success import (
    HUMAN_REVIEW,
    LLM_CALL,
    LLM_ERROR_RATE,
    SYSTEM_ONE_CALL,
    WRONG_ROUTE,
)
from src.ticketdesk import thresholds
from src.ticketdesk.app.batch import TicketInput
from src.ticketdesk.app.trace import SystemOneCall, TicketReport
from src.ticketdesk.calibration import (
    Bin,
    brier_score,
    expected_calibration_error,
    reliability_bins,
)
from src.ticketdesk.cascade import Route
from src.ticketdesk.cost import Scenario, markdown_table
from src.ticketdesk.decision_log import DecisionRecord, log_decision

LOG_PATH = Path(__file__).parent / "logs" / "decisions.jsonl"

Result = tuple[TicketInput, TicketReport]

DEFAULT_PRICES = {
    "system_one": SYSTEM_ONE_CALL,
    "llm": LLM_CALL,
    "human": HUMAN_REVIEW,
    "wrong_route": WRONG_ROUTE,
}


def decision_record(ticket_id: str, report: TicketReport) -> DecisionRecord:
    model = next((c.model for c in report.calls if isinstance(c, SystemOneCall) and c.model), "")
    outcome = report.outcome
    decision = outcome.decision if outcome else None
    if decision is None:
        route = outcome.action if outcome else "error"
        return DecisionRecord(
            ticket_id=ticket_id,
            model=model,
            thresholds_version=thresholds.VERSION,
            route=route,
            predicted_category=None,
            category_probability=0.0,
            urgent_probability=0.0,
            latency_ms=report.seconds * 1000,
            error=report.error,
        )
    return DecisionRecord(
        ticket_id=ticket_id,
        model=model,
        thresholds_version=thresholds.VERSION,
        route=decision.route.value,
        predicted_category=decision.triage.category.value,
        category_probability=decision.triage.category_probability,
        urgent_probability=decision.triage.urgent_probability,
        latency_ms=report.seconds * 1000,
        error=report.error,
    )


def log_report(ticket_id: str, report: TicketReport) -> None:
    log_decision(LOG_PATH, decision_record(ticket_id, report))


@dataclass(frozen=True)
class Calibration:
    title: str
    samples: int
    bins: list[Bin]
    ece: float
    brier: float


def build_calibration(
    title: str, probabilities: list[float], outcomes: list[bool]
) -> Calibration | None:
    if not probabilities:
        return None
    return Calibration(
        title=title,
        samples=len(probabilities),
        bins=reliability_bins(probabilities, outcomes),
        ece=expected_calibration_error(probabilities, outcomes),
        brier=brier_score(probabilities, outcomes),
    )


def calibrations(results: list[Result]) -> list[Calibration]:
    """Надёжность вероятностей Laya по тикетам, у которых в файле есть разметка."""
    category_p: list[float] = []
    category_ok: list[bool] = []
    urgent_p: list[float] = []
    urgent_ok: list[bool] = []
    for ticket, report in results:
        decision = report.outcome.decision if report.outcome else None
        if decision is None:
            continue
        triage = decision.triage
        if ticket.expected_category:
            category_p.append(triage.category_probability)
            category_ok.append(triage.category.value == ticket.expected_category)
        if ticket.expected_urgent is not None:
            urgent_p.append(triage.urgent_probability)
            urgent_ok.append(ticket.expected_urgent)
    found = [
        build_calibration(
            "Категория: вероятность выбранного варианта и доля верных", category_p, category_ok
        ),
        build_calibration("Срочность: вероятность «да» и доля срочных", urgent_p, urgent_ok),
    ]
    return [item for item in found if item is not None]


def batch_scenario(results: list[Result], prices: dict[str, float]) -> Scenario | None:
    """Сценарий «Этот пакет» для cost.markdown_table: доли маршрутов берутся из прогона."""
    decisions = [
        (ticket, report.outcome.decision)
        for ticket, report in results
        if report.outcome and report.outcome.decision
    ]
    if not decisions:
        return None
    total = len(decisions)
    machine = [(t, d) for t, d in decisions if d.route is not Route.HUMAN]
    labeled = [(t, d) for t, d in machine if t.expected_category and d.category]
    errors = sum(d.category.value != t.expected_category for t, d in labeled if d.category)
    return Scenario(
        name="Этот пакет",
        model_cost=prices["system_one"],
        llm_share=sum(d.route is Route.LLM for _, d in decisions) / total,
        llm_cost=prices["llm"],
        human_share=sum(d.route is Route.HUMAN for _, d in decisions) / total,
        human_cost=prices["human"],
        error_rate=errors / len(labeled) if labeled else 0.0,
        error_cost=prices["wrong_route"],
    )


def cost_table(results: list[Result], prices: dict[str, float]) -> str | None:
    scenario = batch_scenario(results, prices)
    if scenario is None:
        return None
    only_humans = Scenario(
        "Только люди", 0.0, 0.0, 0.0, 1.0, prices["human"], 0.0, prices["wrong_route"]
    )
    only_llm = Scenario(
        "Только LLM",
        prices["llm"],
        0.0,
        0.0,
        0.0,
        prices["human"],
        LLM_ERROR_RATE,
        prices["wrong_route"],
    )
    return markdown_table([only_humans, only_llm, scenario], len(results))
