import asyncio
import time
from collections import Counter

from typesafe_sdk import AsyncTypeSafeClient, RetryPolicy, TypeSafeError

from src.ticketdesk.client import make_async_client
from src.ticketdesk.dataset import load_tickets
from src.ticketdesk.typed import CATEGORY, build_state

REQUESTS = 30

POLICIES = {
    "без повторов": RetryPolicy(max_retries=0),
    "2 повтора, до 1 с": RetryPolicy(max_retries=2, backoff_initial=0.2, backoff_max=1.0),
    "6 повторов, до 8 с": RetryPolicy(
        max_retries=6, backoff_initial=0.5, backoff_max=8.0, timeout=60
    ),
}


async def one(client: AsyncTypeSafeClient, state: str) -> str:
    try:
        await client.system_one(state=state, questions={"category": CATEGORY})
        return "ok"
    except TypeSafeError as error:
        return type(error).__name__


async def burst(policy: RetryPolicy) -> Counter[str]:
    tickets = load_tickets()[:REQUESTS]
    async with make_async_client(retry=policy) as client:
        results = await asyncio.gather(
            *(one(client, build_state(t.subject, t.body)) for t in tickets)
        )
    return Counter(results)


def main() -> None:
    for name, policy in POLICIES.items():
        started = time.perf_counter()
        results = asyncio.run(burst(policy))
        seconds = time.perf_counter() - started
        print(f"{name:<20} {seconds:5.1f} с  {dict(results)}")


if __name__ == "__main__":
    main()
