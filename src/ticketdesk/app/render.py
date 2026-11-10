from dataclasses import asdict
from typing import Any

import streamlit as st

from src.ticketdesk import guards, thresholds
from src.ticketdesk.app.trace import Call, LLMCall, SystemOneCall, TicketReport
from src.ticketdesk.typed import FRUSTRATION

# action -> (уровень баннера, заголовок, пояснение)
ACTIONS = {
    "auto_reply": ("success", "Автоответ", "Тикет прошёл все проверки, ответ можно отправлять."),
    "human_review": (
        "warning",
        "Ответ на проверку человеку",
        "Черновик не прошёл выходной guard, его читает оператор.",
    ),
    "human_queue": ("info", "В очередь оператора", "Автоответ не составлялся."),
    "rejected": ("error", "Тикет отклонён", "Входной guard остановил тикет до классификации."),
}

REASONS = {
    "spam": "похоже на спам",
    "abuse": "оскорбления или угрозы",
    "injection": "попытка дать указания ИИ-ассистенту",
    "promise": "в ответе обещание денег или срока",
    "leak": "в ответе внутренняя или чужая информация",
    "low_confidence": "Laya не уверена в категории, ниже порога CATEGORY_HUMAN",
    "urgent": "тикет срочный, его сначала читает человек",
}

ROUTES = {
    "auto": "категорию берём у Laya",
    "llm": "серая зона, категорию уточняет LLM",
    "human": "категорию определяет человек",
}


def probability_table(
    rows: list[dict[str, Any]], key: str, first_column: str, extra: list[str] | None = None
) -> None:
    config: dict[str, Any] = {
        "probability": st.column_config.ProgressColumn(
            "Вероятность", min_value=0.0, max_value=1.0, format="%.3f"
        )
    }
    st.dataframe(
        rows,
        hide_index=True,
        use_container_width=True,
        column_config=config,
        column_order=[first_column, "probability", *(extra or [])],
        key=key,
    )


def render_state(call: SystemOneCall, key: str) -> None:
    with st.expander("Текст, отправленный в Laya"):
        st.code(call.state, language=None, wrap_lines=True)


def render_call_header(call: Call) -> str:
    parts = [f"{call.seconds:.2f} с"]
    if isinstance(call, SystemOneCall) and call.model:
        parts.append(f"модель {call.model}")
        parts.append(f"токены: {call.input_tokens} вход, {call.output_tokens} выход")
    return " · ".join(parts)


def render_guard(call: SystemOneCall, key: str) -> None:
    limits = guards.THRESHOLDS
    rows = [
        {
            "question": name,
            "probability": p,
            "threshold": limits[name],
            "verdict": "сработал" if p >= limits[name] else "чисто",
        }
        for name, p in call.nouls.items()
    ]
    st.dataframe(
        rows,
        hide_index=True,
        use_container_width=True,
        key=f"{key}-guard",
        column_config={
            "question": "Вопрос",
            "probability": st.column_config.ProgressColumn(
                "Вероятность «да»", min_value=0.0, max_value=1.0, format="%.3f"
            ),
            "threshold": st.column_config.NumberColumn("Порог", format="%.2f"),
            "verdict": "Результат",
        },
    )
    st.caption("Guard срабатывает, когда вероятность не ниже порога из guards.THRESHOLDS.")


def render_classification(call: SystemOneCall, report: TicketReport, key: str) -> None:
    decision = report.outcome.decision if report.outcome else None
    for name, probabilities in call.choices.items():
        best = max(probabilities, key=lambda option: probabilities[option])
        st.markdown(f"**Категория.** Лучший вариант: `{best}`, {probabilities[best]:.1%}.")
        rows = [
            {"option": option, "probability": probabilities[option]}
            for option in sorted(probabilities, key=lambda option: -probabilities[option])
        ]
        probability_table(rows, f"{key}-{name}", "option")
        st.caption(
            f"Порог автомаршрута: {thresholds.CATEGORY_AUTO:.2f}, "
            f"ниже {thresholds.CATEGORY_HUMAN:.2f} решает человек, между ними LLM."
        )
        if decision is not None:
            st.markdown(f"Маршрут: **{decision.route.value}**, {ROUTES[decision.route.value]}.")
    for name, p in call.nouls.items():
        verdict = "срочный" if p >= thresholds.URGENT else "не срочный"
        st.markdown(
            f"**Срочность.** Вероятность {p:.1%}, порог {thresholds.URGENT:.2f}: {verdict}."
        )
    for name, probabilities in call.scores.items():
        rows = [
            {
                "level": f"{level}. {FRUSTRATION.criteria[int(level)]}",
                "probability": p,
            }
            for level, p in probabilities.items()
        ]
        st.markdown("**Раздражение клиента.**")
        probability_table(rows, f"{key}-{name}", "level")
    st.caption(f"Версия порогов: {thresholds.VERSION}")


def render_llm(call: LLMCall) -> None:
    st.markdown("Запрос к LLM:")
    st.code(call.prompt, language=None, wrap_lines=True)
    if call.error:
        st.error(call.error)
    else:
        st.markdown("Ответ LLM:")
        st.code(call.reply, language=None, wrap_lines=True)


def step_title(index: int, call: Call) -> str:
    titles = {
        "input_guard": "Входной guard: спам, оскорбления, инъекция",
        "classification": "Классификация, срочность и раздражение (Laya)",
        "llm_classify": "Категория от LLM",
        "llm_reply": "Черновик ответа (LLM)",
        "output_guard": "Выходной guard: обещания и утечки",
    }
    mark = " (ошибка)" if call.error else ""
    return f"Шаг {index}. {titles[call.kind]}{mark}"


def render_step(index: int, call: Call, report: TicketReport, key: str) -> None:
    with st.expander(step_title(index, call), expanded=True):
        st.caption(render_call_header(call))
        if call.error:
            st.error(call.error)
        if isinstance(call, LLMCall):
            render_llm(call)
            return
        if not call.error:
            if call.kind == "classification":
                render_classification(call, report, key)
            else:
                render_guard(call, key)
        render_state(call, key)


def render_report(report: TicketReport, key: str) -> None:
    outcome = report.outcome
    if report.error:
        st.error(f"Обработка прервана: {report.error}")
    if outcome is not None:
        level, title, text = ACTIONS[outcome.action]
        getattr(st, level)(f"**{title}.** {text}")
        for reason in outcome.reasons:
            st.markdown(f"- `{reason}`: {REASONS.get(reason, reason)}")

    system_calls = [call for call in report.calls if isinstance(call, SystemOneCall)]
    columns = st.columns(5)
    decision = outcome.decision if outcome else None
    if decision is not None:
        triage = decision.triage
        category = decision.category.value if decision.category else "человек"
        columns[0].metric("Категория", category)
        columns[1].metric("Срочность", f"{triage.urgent_probability:.0%}")
        columns[2].metric("Раздражение", triage.frustration.name.lower())
    columns[3].metric("Время", f"{report.seconds:.2f} с")
    tokens = sum(call.input_tokens + call.output_tokens for call in system_calls)
    columns[4].metric("Токены Laya", tokens)

    st.subheader("Ход обработки")
    for index, call in enumerate(report.calls, start=1):
        render_step(index, call, report, f"{key}-{index}")

    if outcome is not None and outcome.reply:
        st.subheader("Черновик ответа")
        with st.chat_message("assistant"):
            st.write(outcome.reply)

    with st.expander("Сырые данные запуска"):
        st.json(
            {
                "subject": report.subject,
                "body": report.body,
                "seconds": report.seconds,
                "outcome": asdict(outcome) if outcome else None,
                "calls": [asdict(call) for call in report.calls],
            },
            expanded=False,
        )
