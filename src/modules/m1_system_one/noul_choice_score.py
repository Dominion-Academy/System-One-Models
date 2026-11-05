from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

LAYA_URL = "http://localhost:5000"

TICKET = (
    "I was charged twice for my annual subscription this month. "
    "I asked for a refund of the duplicate payment two weeks ago and nobody has replied."
)

REFUND_REQUESTED = Noul(
    instructions="The customer asks for money back",
    criteria={
        "true": "The customer explicitly asks for a refund or a return of money",
        "false": "The customer does not ask for money back",
    },
)

DEPARTMENT = Choice(
    instructions="Which team should handle this",
    criteria={
        "billing": "Payment or subscription issues",
        "technical": "Bugs or integration problems",
        "sales": "Pricing or account questions",
    },
)

FRUSTRATION = Score(
    instructions="How frustrated the customer appears",
    criteria=[
        "Calm, just stating facts",
        "Frustrated but civil",
        "Very angry, strong language",
    ],
)


def ask_noul(client: TypeSafeClient) -> None:
    response = client.system_one(state=TICKET, questions={"refund": REFUND_REQUESTED})
    refund = response.nouls["refund"]
    print(f"noul: {refund.noul}")


def ask_choice(client: TypeSafeClient) -> None:
    response = client.system_one(state=TICKET, questions={"department": DEPARTMENT})
    department = response.choices["department"]
    print(f"choice: {department.choice}")
    print(f"confidence: {department.confidence}")
    print(f"probabilities: {department.probabilities}")


def ask_score(client: TypeSafeClient) -> None:
    response = client.system_one(state=TICKET, questions={"frustration": FRUSTRATION})
    frustration = response.scores["frustration"]
    print(f"score: {frustration.score}")
    print(f"legend: {frustration.legend}")
    print(f"probabilities: {frustration.probabilities}")


def ask_all(client: TypeSafeClient) -> None:
    response = client.system_one(
        state=TICKET,
        questions={
            "refund": REFUND_REQUESTED,
            "department": DEPARTMENT,
            "frustration": FRUSTRATION,
        },
    )
    print(f"refund: {response.nouls['refund'].noul}")
    print(f"department: {response.choices['department'].choice}")
    print(f"frustration: {response.scores['frustration'].score}")


def main() -> None:
    with TypeSafeClient(base_url=LAYA_URL, api_key="local", model="jev-latest") as client:
        print("--- Noul ---")
        ask_noul(client)
        print("--- Choice ---")
        ask_choice(client)
        print("--- Score ---")
        ask_score(client)
        print("--- Все три в одном запросе ---")
        ask_all(client)


if __name__ == "__main__":
    main()
