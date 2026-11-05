from src.modules.m4_patterns.help_center import ARTICLES, relevance
from src.ticketdesk.client import make_client

RELEVANCE_THRESHOLD = 0.6

QUERIES = [
    "The password reset email never arrives.",
    "Do you have an office in Berlin?",
]


def main() -> None:
    with make_client() as client:
        for query in QUERIES:
            scores = relevance(client, query, list(ARTICLES))
            relevant = [key for key, p in scores.items() if p >= RELEVANCE_THRESHOLD]
            print(f"Вопрос: {query}")
            for key, p in sorted(scores.items(), key=lambda item: -item[1]):
                mark = "+" if p >= RELEVANCE_THRESHOLD else " "
                print(f"  {mark} {p:.2f} {key}")
            if relevant:
                print(f"  В промпт LLM: {relevant}")
            else:
                print("  Подходящих статей нет: тикет уходит человеку")
            print()


if __name__ == "__main__":
    main()
