import time

from src.modules.m4_patterns.help_center import QUERIES, keyword_search, rerank
from src.ticketdesk.client import make_client

TOP_K = 4


def show(order: list[str], gold: str) -> str:
    return " ".join(f"[{key}]" if key == gold else key for key in order)


def main() -> None:
    found, search_hits, rerank_hits, seconds = 0, 0, 0, []
    with make_client() as client:
        for query, gold in QUERIES:
            candidates = keyword_search(query, top_k=TOP_K)
            started = time.perf_counter()
            reranked = rerank(client, query, candidates)
            seconds.append(time.perf_counter() - started)

            found += gold in candidates
            search_hits += candidates[0] == gold
            rerank_hits += reranked[0] == gold
            print(query)
            print(f"  поиск: {show(candidates, gold)}")
            print(f"  реранк:  {show(reranked, gold)}")

    total = len(QUERIES)
    print()
    print(f"Нужная статья среди {TOP_K} кандидатов: {found} из {total}")
    print(f"Первая верная у поиска: {search_hits} из {total}")
    print(f"Первая верная после реранка: {rerank_hits} из {total}")
    print(f"Реранкинг: {sum(seconds) / total * 1000:.0f} мс на вопрос")


if __name__ == "__main__":
    main()
