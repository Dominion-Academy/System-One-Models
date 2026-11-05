from src.ticketdesk.cost import Scenario, breakdown, markdown_table

TICKETS = 1000

# Цены и точность LLM условные: подставьте свои.
LLM_CALL = 0.002  # один вызов LLM на тикет
LLM_ERROR_RATE = 0.15  # доля ошибок LLM на всём потоке тикетов
# В каскаде LLM получает только трудные тикеты, на которых модель System One не уверена.
# На них LLM ошибается чаще, чем в среднем по потоку.
LLM_HARD_ERROR_RATE = 0.30
HUMAN_REVIEW = 2.0  # из модуля про калибровку
WRONG_ROUTE = 8.0
# Jev по заявленной цене $0.042 за 1 млн входных токенов, около 300 токенов на тикет.
SYSTEM_ONE_CALL = 300 * 0.042 / 1_000_000


def cascade_scenario(hard_error_rate: float) -> Scenario:
    # Доли зон и ошибки в зоне auto из прогона каскада на hold-out (cascade_demo.py):
    # auto 33, llm 14, human 11 из 58; в auto 3 ошибки из 33.
    return Scenario(
        name="Каскад",
        model_cost=SYSTEM_ONE_CALL,
        llm_share=14 / 58,
        llm_cost=LLM_CALL,
        human_share=11 / 58,
        human_cost=HUMAN_REVIEW,
        error_rate=(3 + 14 * hard_error_rate) / 47,
        error_cost=WRONG_ROUTE,
    )


SCENARIOS = [
    Scenario(
        name="Только люди",
        model_cost=0.0,
        llm_share=0.0,
        llm_cost=0.0,
        human_share=1.0,
        human_cost=HUMAN_REVIEW,
        error_rate=0.0,
        error_cost=WRONG_ROUTE,
    ),
    Scenario(
        name="Только LLM",
        model_cost=LLM_CALL,
        llm_share=0.0,
        llm_cost=0.0,
        human_share=0.0,
        human_cost=HUMAN_REVIEW,
        error_rate=LLM_ERROR_RATE,
        error_cost=WRONG_ROUTE,
    ),
    cascade_scenario(LLM_HARD_ERROR_RATE),
]


def main() -> None:
    print(markdown_table(SCENARIOS, TICKETS))
    only_llm = breakdown(SCENARIOS[1], TICKETS).per_success
    print()
    print(f"Чувствительность: «Только LLM» стоит {only_llm:.4f} за успех при ошибках LLM 0.15.")
    print("| Ошибки LLM на трудных тикетах | Каскад, $ за успех | Дешевле «Только LLM»? |")
    print("|---|---|---|")
    for rate in (0.15, 0.20, 0.25, 0.30, 0.40):
        cascade = breakdown(cascade_scenario(rate), TICKETS).per_success
        print(f"| {rate:.2f} | {cascade:.4f} | {'да' if cascade < only_llm else 'нет'} |")
    break_even = next(
        (
            rate / 100
            for rate in range(101)
            if breakdown(cascade_scenario(rate / 100), TICKETS).per_success >= only_llm
        ),
        None,
    )
    print()
    print(f"Каскад перестаёт быть дешевле при ошибках LLM на трудных тикетах около {break_even}.")


if __name__ == "__main__":
    main()
