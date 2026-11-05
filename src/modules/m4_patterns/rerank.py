import time
from collections.abc import Callable

from typesafe_sdk import TypeSafeClient

from src.modules.m4_patterns.help_center import (
    QUERIES,
    keyword_search,
    relevance,
    relevance_one_request,
)
from src.ticketdesk.client import make_client

Scorer = Callable[[TypeSafeClient, str, list[str]], dict[str, float]]


def evaluate(client: TypeSafeClient, name: str, scorer: Scorer) -> None:
    hits, seconds = 0, []
    for query, gold in QUERIES:
        candidates = keyword_search(query, top_k=4)
        started = time.perf_counter()
        scores = scorer(client, query, candidates)
        seconds.append(time.perf_counter() - started)
        hits += max(candidates, key=lambda key: scores[key]) == gold
    average_ms = sum(seconds) / len(seconds) * 1000
    print(f"{name}: первая верная {hits} из {len(QUERIES)}, {average_ms:.0f} мс на вопрос")


def main() -> None:
    recall = sum(gold in keyword_search(query, top_k=4) for query, gold in QUERIES)
    keyword_hits = sum(keyword_search(query, top_k=4)[0] == gold for query, gold in QUERIES)
    print(f"Нужная статья среди 4 кандидатов: {recall} из {len(QUERIES)}")
    print(f"Ключевые слова: первая верная {keyword_hits} из {len(QUERIES)}")
    with make_client() as client:
        evaluate(client, "Noul, статья в state", relevance)
        evaluate(client, "Noul, статьи в instructions", relevance_one_request)


if __name__ == "__main__":
    main()
