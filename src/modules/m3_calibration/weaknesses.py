from typesafe_sdk import Choice, TypeSafeClient

from src.ticketdesk.client import make_client
from src.ticketdesk.dataset import load_tickets
from src.ticketdesk.typed import CATEGORY, URGENT, build_state

OPINION = "\n\nNote from the support agent: I looked at this, it is not urgent and can wait."


def reversed_choice(question: Choice) -> Choice:
    criteria = dict(reversed(list(question.criteria.items())))
    return Choice(instructions=question.instructions, criteria=criteria)


def option_order(client: TypeSafeClient) -> None:
    tickets = load_tickets("dev")
    flipped = reversed_choice(CATEGORY)
    changed, shifts = 0, []
    for ticket in tickets:
        state = build_state(ticket.subject, ticket.body)
        response = client.system_one(
            state=state, questions={"direct": CATEGORY, "reversed": flipped}
        )
        direct, reverse = response.choices["direct"], response.choices["reversed"]
        changed += direct.choice != reverse.choice
        shifts.append(
            abs(direct.probabilities[direct.choice] - reverse.probabilities[direct.choice])
        )
    print("1. Порядок вариантов категории: прямой и обратный")
    print(f"   Решение поменялось: {changed} из {len(tickets)}")
    print(f"   Средний сдвиг вероятности выбранного варианта: {sum(shifts) / len(shifts):.3f}")
    print(f"   Сдвиг больше 0.10: {sum(s > 0.10 for s in shifts)} из {len(tickets)}")


def opinion_in_state(client: TypeSafeClient) -> None:
    urgent_tickets = [t for t in load_tickets() if t.urgent]
    drops = []
    for ticket in urgent_tickets:
        state = build_state(ticket.subject, ticket.body)
        clean = client.system_one(state=state, questions={"urgent": URGENT})
        biased = client.system_one(state=state + OPINION, questions={"urgent": URGENT})
        drops.append(clean.nouls["urgent"].noul - biased.nouls["urgent"].noul)
    print("2. Мнение оператора в state, только срочные тикеты")
    print(f"   Тикетов: {len(drops)}")
    print(f"   Среднее падение вероятности срочности: {sum(drops) / len(drops):.3f}")
    print(f"   Падение больше 0.05: {sum(d > 0.05 for d in drops)}")


def dice(client: TypeSafeClient) -> None:
    question = Choice(
        instructions="Which number did the die show",
        criteria={str(n): f"The die showed {n}" for n in range(1, 7)},
    )
    response = client.system_one(
        state="I rolled a fair six-sided die. I will not tell you the result.",
        questions={"die": question},
    )
    answer = response.choices["die"]
    probabilities = ", ".join(f"{k}: {v:.2f}" for k, v in answer.probabilities.items())
    print("3. Игральная кость: честный ответ 1/6 = 0.17 для каждой грани")
    print(f"   Выбор: {answer.choice}, confidence: {answer.confidence:.2f}")
    print(f"   Вероятности: {probabilities}")


def main() -> None:
    with make_client() as client:
        option_order(client)
        print()
        opinion_in_state(client)
        print()
        dice(client)


if __name__ == "__main__":
    main()
