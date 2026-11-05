CATEGORIES = {"billing", "technical", "sales", "spam"}

REPLIES = [
    "billing",
    "Billing",
    "Категория: billing",
    "Скорее всего, это billing, так как клиент пишет про двойное списание.",
    '{"category": "billing"}',
]


def parse_category(reply: str) -> str:
    category = reply.strip()
    if category not in CATEGORIES:
        raise ValueError(f"Не удалось разобрать ответ: {reply!r}")
    return category


def main() -> None:
    for reply in REPLIES:
        try:
            print(f"OK     {parse_category(reply)!r}")
        except ValueError as error:
            print(f"ОШИБКА {error}")


if __name__ == "__main__":
    main()
