from time import perf_counter

from typesafe_sdk import TypeSafeClient

from src.modules.m1_system_one.noul_choice_score import (
    DEPARTMENT,
    FRUSTRATION,
    LAYA_URL,
    REFUND_REQUESTED,
    TICKET,
)

QUESTIONS = {
    "refund": REFUND_REQUESTED,
    "department": DEPARTMENT,
    "frustration": FRUSTRATION,
}


def main() -> None:
    with TypeSafeClient(base_url=LAYA_URL, api_key="local", model="jev-latest") as client:
        start = perf_counter()
        for name, question in QUESTIONS.items():
            client.system_one(state=TICKET, questions={name: question})
        sequential = perf_counter() - start

        start = perf_counter()
        client.system_one(state=TICKET, questions=QUESTIONS)
        single = perf_counter() - start

    print(f"три запроса подряд: {sequential:.3f} с")
    print(f"один запрос с тремя вопросами: {single:.3f} с")


if __name__ == "__main__":
    main()
