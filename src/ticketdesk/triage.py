from dataclasses import dataclass

from typesafe_sdk import TypeSafeClient

from src.ticketdesk.questions import CATEGORY, URGENT

URGENT_THRESHOLD = 0.5


@dataclass
class Triage:
    category: str
    category_probability: float
    urgent_probability: float

    @property
    def urgent(self) -> bool:
        return self.urgent_probability >= URGENT_THRESHOLD


def triage(client: TypeSafeClient, ticket: str) -> Triage:
    response = client.system_one(
        state=ticket,
        questions={"category": CATEGORY, "urgent": URGENT},
    )
    category = response.choices["category"]
    return Triage(
        category=category.choice,
        category_probability=category.probabilities[category.choice],
        urgent_probability=response.nouls["urgent"].noul,
    )
