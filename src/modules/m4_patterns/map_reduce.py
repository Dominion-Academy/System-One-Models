import asyncio
import time
from collections import Counter, defaultdict
from dataclasses import dataclass

from typesafe_sdk import AsyncTypeSafeClient

from src.ticketdesk import thresholds
from src.ticketdesk.client import make_async_client
from src.ticketdesk.dataset import LabeledTicket, load_tickets
from src.ticketdesk.typed import CATEGORY, FRUSTRATION, URGENT, Category, build_state

CONCURRENCY = 8


@dataclass(frozen=True)
class Features:
    category: Category
    urgent: bool
    frustration: float


async def extract(
    client: AsyncTypeSafeClient, semaphore: asyncio.Semaphore, ticket: LabeledTicket
) -> Features:
    async with semaphore:
        response = await client.system_one(
            state=build_state(ticket.subject, ticket.body),
            questions={"category": CATEGORY, "urgent": URGENT, "frustration": FRUSTRATION},
        )
    return Features(
        category=Category(response.choices["category"].choice),
        urgent=response.nouls["urgent"].noul >= thresholds.URGENT,
        frustration=response.scores["frustration"].score,
    )


async def map_tickets(tickets: list[LabeledTicket], concurrency: int) -> list[Features]:
    semaphore = asyncio.Semaphore(concurrency)
    async with make_async_client() as client:
        return await asyncio.gather(*(extract(client, semaphore, t) for t in tickets))


def reduce_features(features: list[Features]) -> None:
    counts = Counter(f.category for f in features)
    urgent = Counter(f.category for f in features if f.urgent)
    frustration: defaultdict[Category, list[float]] = defaultdict(list)
    for f in features:
        frustration[f.category].append(f.frustration)
    print("категория   тикетов  срочных  раздражение")
    for category, count in counts.most_common():
        mean = sum(frustration[category]) / count
        print(f"{category.value:<11} {count:7d}  {urgent[category]:7d}  {mean:11.2f}")


def main() -> None:
    tickets = load_tickets()
    for concurrency in (1, CONCURRENCY):
        started = time.perf_counter()
        features = asyncio.run(map_tickets(tickets, concurrency))
        seconds = time.perf_counter() - started
        print(f"{len(tickets)} тикетов, одновременно {concurrency}: {seconds:.1f} с")
    print()
    reduce_features(features)


if __name__ == "__main__":
    main()
