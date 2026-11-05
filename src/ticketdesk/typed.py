from dataclasses import dataclass
from enum import IntEnum, StrEnum

from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

from src.ticketdesk.triage import URGENT_THRESHOLD


class Category(StrEnum):
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    OTHER = "other"


class Frustration(IntEnum):
    CALM = 0
    ANNOYED = 1
    ANGRY = 2


CATEGORY_CRITERIA = {
    Category.BILLING: "Payments, invoices, refunds, subscription charges",
    Category.TECHNICAL: "Bugs, errors, API or integration problems",
    Category.ACCOUNT: "Login, password, profile and account settings",
    Category.OTHER: "Anything else: feature requests, general questions, feedback",
}

CATEGORY = Choice(
    instructions="Which kind of problem is described in the support ticket",
    criteria={category.value: text for category, text in CATEGORY_CRITERIA.items()},
)

URGENT = Noul(
    instructions="The customer cannot work or loses money right now and needs a quick answer",
    criteria={
        "true": "A blocking problem or a hard deadline, the customer needs help immediately",
        "false": "No blocker and no deadline, the request can wait",
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


@dataclass(frozen=True)
class TypedTriage:
    category: Category
    category_probability: float
    urgent_probability: float
    frustration: Frustration

    @property
    def urgent(self) -> bool:
        return self.urgent_probability >= URGENT_THRESHOLD


def build_state(subject: str, body: str) -> str:
    return f"Subject: {subject}\n\n{body}"


def typed_triage(client: TypeSafeClient, subject: str, body: str) -> TypedTriage:
    response = client.system_one(
        state=build_state(subject, body),
        questions={"category": CATEGORY, "urgent": URGENT, "frustration": FRUSTRATION},
    )
    category = response.choices["category"]
    probabilities = response.scores["frustration"].probabilities
    most_likely_level = max(probabilities, key=lambda level: probabilities[level])
    return TypedTriage(
        category=Category(category.choice),
        category_probability=category.probabilities[category.choice],
        urgent_probability=response.nouls["urgent"].noul,
        frustration=Frustration(most_likely_level),
    )
