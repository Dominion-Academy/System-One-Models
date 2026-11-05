from collections import Counter

from typesafe_sdk import Choice, Noul

from src.ticketdesk.client import make_client
from src.ticketdesk.dataset import load_tickets
from src.ticketdesk.typed import build_state

# Условные цены одного ответа LLM на тикет, в долларах.
SMALL_LLM_PRICE = 0.0004
LARGE_LLM_PRICE = 0.0100

SIMPLE = Noul(
    instructions="The ticket can be answered from public help articles, without account data or debugging",
    criteria={
        "true": "A general how-to or policy question with a standard answer",
        "false": "Needs to look at this customer's account, payments or logs, or to investigate a bug",
    },
)

TOOL = Choice(
    instructions="Which action should the support agent take first",
    criteria={
        "answer_faq": "Answer with a help article, no tools needed",
        "lookup_payment": "Look up charges, invoices or refunds of this customer",
        "reset_access": "Reset password, 2FA or remove a user's access",
        "open_incident": "Report an outage or a bug to the engineering on-call",
    },
)


def main() -> None:
    tickets = load_tickets("dev")
    simple_count = faq_count = 0
    tools: Counter[str] = Counter()
    with make_client() as client:
        for ticket in tickets:
            response = client.system_one(
                state=build_state(ticket.subject, ticket.body),
                questions={"simple": SIMPLE, "tool": TOOL},
            )
            simple = response.nouls["simple"].noul >= 0.5
            simple_count += simple
            tool = response.choices["tool"].choice
            faq_count += tool == "answer_faq"
            tools[tool] += 1
            model = "small" if simple else "large"
            print(f"{ticket.id} {model:<5} {tool:<15} {ticket.subject}")

    total = len(tickets)
    print()
    print(f"Инструменты: {dict(tools)}")
    print(f"Только большая LLM: ${total * LARGE_LLM_PRICE:.3f}")
    for rule, small in (("SIMPLE >= 0.5", simple_count), ("TOOL == answer_faq", faq_count)):
        cost = small * SMALL_LLM_PRICE + (total - small) * LARGE_LLM_PRICE
        saving = 1 - cost / (total * LARGE_LLM_PRICE)
        print(f"{rule}: в маленькую {small} из {total}, ${cost:.3f}, экономия {saving:.0%}")


if __name__ == "__main__":
    main()
