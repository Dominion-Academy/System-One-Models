import json
import time
from collections.abc import Callable

import httpx2

from src.ticketdesk.llm import StubLLM
from src.ticketdesk.resilient import make_resilient_client, resilient_category

SUBJECT, BODY = "Charged twice", "I was charged twice for the annual plan. Please refund."

OK_BODY = {
    "model": "mock",
    "answers": {
        "category": {
            "type": "choice",
            "choice": "billing",
            "confidence": 0.9,
            "probabilities": {"billing": 0.9, "technical": 0.04, "account": 0.03, "other": 0.03},
        },
        "urgent": {"type": "noul", "noul": 0.7},
        "frustration": {
            "type": "score",
            "score": 1.0,
            "confidence": 0.8,
            "legend": {"0": "calm", "1": "annoyed", "2": "angry"},
            "probabilities": {"0": 0.1, "1": 0.8, "2": 0.1},
        },
    },
    "usage": {"input_tokens": 120, "output_tokens": 0},
}

Handler = Callable[[httpx2.Request], httpx2.Response]


def failing_then_ok(failures: int, status: int) -> tuple[Handler, list[int]]:
    calls: list[int] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        calls.append(1)
        if len(calls) <= failures:
            return httpx2.Response(status, json={"error": "server is busy"})
        return httpx2.Response(200, content=json.dumps(OK_BODY).encode())

    return handler, calls


def timeout_handler(calls: list[int]) -> Handler:
    def handler(request: httpx2.Request) -> httpx2.Response:
        calls.append(1)
        raise httpx2.ReadTimeout("simulated timeout", request=request)

    return handler


def run(name: str, handler: Handler, calls: list[int]) -> None:
    started = time.perf_counter()
    client = make_resilient_client(
        base_url="http://mock",
        api_key="local",
        model="mock",
        transport=httpx2.MockTransport(handler),
    )
    with client:
        result = resilient_category(client, StubLLM(), SUBJECT, BODY)
    seconds = time.perf_counter() - started
    print(f"{name:<28} попыток: {len(calls)}, {seconds:.1f} с -> {result}")


def main() -> None:
    handler, calls = failing_then_ok(failures=2, status=503)
    run("503 дважды, потом успех", handler, calls)

    handler, calls = failing_then_ok(failures=10, status=503)
    run("503 всё время", handler, calls)

    handler, calls = failing_then_ok(failures=10, status=401)
    run("401 неверный ключ", handler, calls)

    calls = []
    run("таймаут каждого запроса", timeout_handler(calls), calls)

    started = time.perf_counter()
    with make_resilient_client(base_url="http://localhost:5999", api_key="local") as client:
        result = resilient_category(client, StubLLM(), SUBJECT, BODY)
    print(f"{'сервер не запущен':<28} {time.perf_counter() - started:.1f} с -> {result}")


if __name__ == "__main__":
    main()
