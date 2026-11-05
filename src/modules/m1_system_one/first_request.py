from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

LAYA_URL = "http://localhost:5000"

TICKET = (
    "Our API integration started returning 500 errors on every request about 20 minutes ago, "
    "and we can't process any customer orders until this is fixed."
)


def main() -> None:
    with TypeSafeClient(base_url=LAYA_URL, api_key="local", model="jev-latest") as client:
        response = client.system_one(
            state=TICKET,
            questions={
                "department": Choice(
                    instructions="Which team should handle this",
                    criteria={
                        "billing": "Payment or subscription issues",
                        "technical": "Bugs or integration problems",
                        "sales": "Pricing or account questions",
                    },
                ),
                "frustration": Score(
                    instructions="How frustrated the customer appears",
                    criteria=[
                        "Calm, just stating facts",
                        "Frustrated but civil",
                        "Very angry, strong language",
                    ],
                ),
                "is_urgent": Noul(
                    instructions="The message conveys urgency or time-sensitivity",
                ),
            },
        )

    department = response.choices["department"]
    print(f"department: {department.choice} (confidence {department.confidence})")
    print(f"probabilities: {department.probabilities}")
    print(f"frustration: {response.scores['frustration'].score}")
    print(f"is_urgent: {response.nouls['is_urgent'].noul}")
    print(f"usage: {response.usage}")


if __name__ == "__main__":
    main()
