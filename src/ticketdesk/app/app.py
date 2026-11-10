import csv
import io
from collections import Counter

import streamlit as st

from src.ticketdesk import guards, thresholds
from src.ticketdesk.app import analytics
from src.ticketdesk.app.analytics import Result
from src.ticketdesk.app.batch import TicketInput, parse_tickets
from src.ticketdesk.app.render import ACTIONS, render_report
from src.ticketdesk.app.settings import DEFAULTS, Settings
from src.ticketdesk.app.trace import TicketReport, analyze, check_connection
from src.ticketdesk.dataset import load_tickets
from src.ticketdesk.decision_log import read_log

st.set_page_config(page_title="Ticketdesk", page_icon="🎫", layout="wide")

EXAMPLES = {f"{t.id} · {t.subject} [{t.category.value}]": t for t in load_tickets()}


def sidebar_settings() -> Settings:
    st.sidebar.header("Подключения")
    st.sidebar.subheader("System One модель")
    laya_url = st.sidebar.text_input("Адрес", DEFAULTS.laya_url, key="laya_url")
    laya_key = st.sidebar.text_input("API-ключ", DEFAULTS.laya_key, type="password", key="laya_key")
    laya_model = st.sidebar.text_input("Модель", DEFAULTS.laya_model, key="laya_model")

    st.sidebar.subheader("LLM (OpenAI-совместимый API)")
    llm_base_url = st.sidebar.text_input("base_url", DEFAULTS.llm_base_url, key="llm_base_url")
    llm_key = st.sidebar.text_input(
        "API-ключ",
        DEFAULTS.llm_key,
        type="password",
        key="llm_key",
        help="Без ключа вместо LLM работает заглушка StubLLM: ищет ключевые слова.",
    )
    llm_model = st.sidebar.text_input("Модель", DEFAULTS.llm_model, key="llm_model")

    retry = st.sidebar.checkbox(
        "Повторять упавшие запросы",
        key="retry",
        help="Политика resilient.FAST_RETRY: два повтора с паузами 0.2 и 0.4 с.",
    )
    st.sidebar.checkbox(
        "Писать журнал решений",
        value=True,
        key="log_decisions",
        help=f"Каждое решение добавляется в {analytics.LOG_PATH.name} (модуль decision_log).",
    )
    settings = Settings(laya_url, laya_key, laya_model, llm_base_url, llm_key, llm_model, retry)
    if st.sidebar.button("Проверить подключение", use_container_width=True):
        with st.sidebar, st.spinner("Проверяю..."):
            st.session_state["connection"] = check_connection(settings)
    for ok, message in st.session_state.get("connection", []):
        (st.sidebar.success if ok else st.sidebar.error)(message)
    st.sidebar.caption("Ключи живут только в этой вкладке браузера и никуда не записываются.")

    with st.sidebar.expander("Пороги решений"):
        st.markdown(
            f"- Срочность: от {thresholds.URGENT}\n"
            f"- Категория автоматически: от {thresholds.CATEGORY_AUTO}\n"
            f"- Категория человеку: ниже {thresholds.CATEGORY_HUMAN}\n"
            f"- Guards: {guards.THRESHOLDS}\n"
            f"- Версия: {thresholds.VERSION}"
        )
    with st.sidebar.expander("Журнал решений"):
        if analytics.LOG_PATH.exists():
            records = read_log(analytics.LOG_PATH)
            st.caption(f"Записей: {len(records)}. Последние 10:")
            st.dataframe(records[-10:], hide_index=True, key="log_table")
            st.download_button("Скачать журнал", analytics.LOG_PATH.read_bytes(), "decisions.jsonl")
        else:
            st.caption("Пока пусто.")
    return settings


def log_if_enabled(ticket_id: str, report: TicketReport) -> None:
    if st.session_state.get("log_decisions"):
        analytics.log_report(ticket_id, report)


def fill_example() -> None:
    example = EXAMPLES[st.session_state["example"]]
    st.session_state["subject"] = example.subject
    st.session_state["body"] = example.body


def single_tab(settings: Settings) -> None:
    st.selectbox(
        "Пример из датасета курса",
        list(EXAMPLES),
        index=None,
        placeholder="Выберите, чтобы подставить в форму",
        key="example",
        on_change=fill_example,
    )
    subject = st.text_input("Тема тикета", key="subject")
    body = st.text_area("Текст тикета", key="body", height=180)
    if st.button("Разобрать тикет", type="primary", disabled=not (subject and body)):
        with st.spinner("Идёт разбор..."):
            fresh = analyze(settings, subject, body)
        log_if_enabled("manual", fresh)
        st.session_state["single_report"] = fresh
    report: TicketReport | None = st.session_state.get("single_report")
    if report is not None:
        render_report(report, "single")


def batch_row(ticket: TicketInput, report: TicketReport) -> dict[str, object]:
    outcome = report.outcome
    decision = outcome.decision if outcome else None
    category = decision.category.value if decision and decision.category else None
    return {
        "id": ticket.id,
        "subject": ticket.subject,
        "action": outcome.action if outcome else "error",
        "reasons": ", ".join(outcome.reasons) if outcome else "",
        "route": decision.route.value if decision else "",
        "category": category or "",
        "expected": ticket.expected_category or "",
        "urgent_probability": round(decision.triage.urgent_probability, 3) if decision else "",
        "frustration": decision.triage.frustration.name.lower() if decision else "",
        "seconds": round(report.seconds, 2),
        "error": report.error or "",
    }


def to_csv(rows: list[dict[str, object]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def load_batch_input() -> list[TicketInput] | None:
    source = st.radio(
        "Источник", ["Загрузить файл", "Dev-тикеты курса"], horizontal=True, key="batch_source"
    )
    if source == "Dev-тикеты курса":
        return [
            TicketInput(t.id, t.subject, t.body, t.category.value, t.urgent)
            for t in load_tickets("dev")
        ]
    uploaded = st.file_uploader(
        "Файл .jsonl или .csv с полями subject и body (id и category необязательны)",
        type=["jsonl", "csv"],
    )
    if uploaded is None:
        return None
    try:
        return parse_tickets(uploaded.name, uploaded.getvalue())
    except ValueError as error:
        st.error(str(error))
        return None


def batch_summary(results: list[tuple[TicketInput, TicketReport]]) -> None:
    rows = [batch_row(ticket, report) for ticket, report in results]
    counts = Counter(str(row["action"]) for row in rows)
    columns = st.columns(len(ACTIONS) + 2)
    columns[0].metric("Тикетов", len(rows))
    for column, (action, (_, title, _)) in zip(columns[1:], ACTIONS.items(), strict=False):
        column.metric(title, counts.get(action, 0))
    columns[-1].metric("Ошибок", counts.get("error", 0))

    st.dataframe(rows, hide_index=True, use_container_width=True, key="batch_table")
    st.download_button(
        "Скачать результаты (CSV)", to_csv(rows), "ticketdesk_results.csv", "text/csv"
    )
    calibration_section(results)
    cost_section(results)


def calibration_section(results: list[Result]) -> None:
    items = analytics.calibrations(results)
    if not items:
        st.caption("В файле нет полей category и urgent, поэтому калибровку считать не по чему.")
        return
    st.subheader("Надёжность вероятностей Laya")
    for item in items:
        st.markdown(f"**{item.title}.** Тикетов: {item.samples}.")
        st.dataframe(
            [
                {
                    "bin": f"{b.low:.1f}-{b.high:.1f}",
                    "n": b.count,
                    "mean_p": round(b.mean_probability, 3),
                    "observed": b.observed,
                }
                for b in item.bins
            ],
            hide_index=True,
            use_container_width=True,
            key=f"calibration-{item.title}",
            column_config={
                "bin": "Диапазон",
                "n": "Тикетов",
                "mean_p": "Средняя вероятность",
                "observed": st.column_config.ProgressColumn(
                    "Доля верных", min_value=0.0, max_value=1.0, format="%.2f"
                ),
            },
        )
        st.caption(f"ECE {item.ece:.3f}, Brier {item.brier:.3f}.")


def cost_section(results: list[Result]) -> None:
    st.subheader("Стоимость пакета")
    labels = {
        "system_one": "Вызов System One, $",
        "llm": "Вызов LLM, $",
        "human": "Ручной разбор тикета, $",
        "wrong_route": "Одна ошибка маршрута, $",
    }
    columns = st.columns(len(labels))
    prices = {
        key: column.number_input(
            labels[key], min_value=0.0, value=float(value), format="%.6f", key=f"price-{key}"
        )
        for column, (key, value) in zip(columns, analytics.DEFAULT_PRICES.items(), strict=True)
    }
    table = analytics.cost_table(results, prices)
    if table:
        st.markdown(table)
        st.caption(
            "Цены по умолчанию условные, из cost_per_success.py. Доли LLM и людей берутся из "
            "этого прогона, доля ошибок из разметки файла. У «Только LLM» ошибки LLM_ERROR_RATE."
        )


def batch_tab(settings: Settings) -> None:
    tickets = load_batch_input()
    if tickets is None:
        return
    limit = st.number_input("Сколько тикетов разобрать", 1, len(tickets), min(10, len(tickets)))
    st.caption(f"В источнике {len(tickets)} тикетов. Каждый тикет это 2-4 запроса к Laya и LLM.")
    if st.button("Разобрать пакет", type="primary"):
        progress = st.progress(0.0, text="Начинаю...")
        fresh: list[tuple[TicketInput, TicketReport]] = []
        for number, ticket in enumerate(tickets[: int(limit)], start=1):
            progress.progress((number - 1) / int(limit), text=f"Тикет {number} из {int(limit)}")
            report = analyze(settings, ticket.subject, ticket.body)
            log_if_enabled(ticket.id, report)
            fresh.append((ticket, report))
        progress.empty()
        st.session_state["batch_results"] = fresh

    results = st.session_state.get("batch_results") or []
    if not results:
        return
    st.subheader("Итоги")
    batch_summary(results)
    st.subheader("Подробный разбор тикета")
    labels = [f"{ticket.id} · {ticket.subject}" for ticket, _ in results]
    chosen = st.selectbox("Тикет", range(len(labels)), format_func=lambda i: labels[i])
    ticket, report = results[chosen]
    with st.container(border=True):
        st.markdown(f"**{ticket.subject}**")
        st.write(ticket.body)
    render_report(report, f"batch-{chosen}")


def main() -> None:
    st.title("🎫 Ticketdesk")
    st.caption("Триаж тикетов поддержки")
    settings = sidebar_settings()
    single, batch = st.tabs(["Один тикет", "Файл с тикетами"])
    with single:
        single_tab(settings)
    with batch:
        batch_tab(settings)


main()
