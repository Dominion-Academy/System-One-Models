from laya import Router

TICKET = (
    "Our API integration started returning 500 errors on every request about 20 minutes ago, "
    "and we can't process any customer orders until this is fixed."
)


def main() -> None:
    router = Router()

    result = router.predict(
        TICKET,
        {
            "department": {
                "type": "choice",
                "instructions": "Which team should handle this",
                "criteria": {
                    "billing": "Payment or subscription issues",
                    "technical": "Bugs or integration problems",
                    "sales": "Pricing or account questions",
                },
            },
            "frustration": {
                "type": "score",
                "instructions": "How frustrated the customer appears",
                "criteria": [
                    "Calm, just stating facts",
                    "Frustrated but civil",
                    "Very angry, strong language",
                ],
            },
            "is_urgent": {
                "type": "noul",
                "instructions": "The message conveys urgency or time-sensitivity",
            },
        },
    )

    answers = result["answers"]
    print(answers["department"]["choice"])
    print(answers["frustration"]["score"])
    print(answers["is_urgent"]["noul"])
    print(result["routing"]["model"])


if __name__ == "__main__":
    main()
