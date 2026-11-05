from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    name: str
    model_cost: float  # вызовы моделей на каждый тикет, $
    llm_share: float  # доля тикетов, где дополнительно вызывается LLM
    llm_cost: float  # цена одного такого вызова LLM, $
    human_share: float  # доля тикетов, которые решает человек
    human_cost: float  # цена ручного разбора одного тикета, $
    error_rate: float  # доля ошибок среди решённых автоматически
    error_cost: float  # цена одной ошибки, $


@dataclass(frozen=True)
class CostBreakdown:
    models: float
    humans: float
    errors: float
    successes: float

    @property
    def total(self) -> float:
        return self.models + self.humans + self.errors

    @property
    def per_success(self) -> float:
        return self.total / self.successes


def breakdown(scenario: Scenario, tickets: int) -> CostBreakdown:
    automatic = tickets * (1 - scenario.human_share)
    errors = automatic * scenario.error_rate
    llm_calls = tickets * scenario.llm_share
    return CostBreakdown(
        models=tickets * scenario.model_cost + llm_calls * scenario.llm_cost,
        humans=tickets * scenario.human_share * scenario.human_cost,
        errors=errors * scenario.error_cost,
        successes=tickets - errors,
    )


def markdown_table(scenarios: list[Scenario], tickets: int) -> str:
    lines = [
        f"| Сценарий ({tickets} тикетов) | Модели, $ | Люди, $ | Ошибки, $ | Всего, $ | За успех, $ |",
        "|---|---|---|---|---|---|",
    ]
    for scenario in scenarios:
        b = breakdown(scenario, tickets)
        lines.append(
            f"| {scenario.name} | {b.models:.2f} | {b.humans:.2f} | {b.errors:.2f} "
            f"| {b.total:.2f} | {b.per_success:.4f} |"
        )
    return "\n".join(lines)
