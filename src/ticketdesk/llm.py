import json
import os
import time
import urllib.request
from typing import Protocol

from src.ticketdesk.typed import Category

KEYWORDS = {
    Category.BILLING: ("charge", "invoice", "refund", "price", "billing", "payment", "vat"),
    Category.TECHNICAL: ("error", "api", "bug", "crash", "500", "webhook", "slow", "broken"),
    Category.ACCOUNT: ("login", "log in", "password", "account", "2fa", "access", "admin"),
}


# Начало промпта классификации: по нему отличают этот вызов от черновика ответа.
CLASSIFY_PROMPT_START = "Pick the category"


class LLM(Protocol):
    def complete(self, prompt: str) -> str: ...


class StubLLM:
    """Заглушка без сети: ищет ключевые слова и отвечает за заданное время."""

    def __init__(self, delay: float = 0.0) -> None:
        self.delay = delay

    def complete(self, prompt: str) -> str:
        time.sleep(self.delay)
        instruction, _, text = prompt.lower().partition("\n\n")
        if "category" in instruction:
            for category, words in KEYWORDS.items():
                if any(word in text for word in words):
                    return category.value
            return Category.OTHER.value
        return "Thank you for contacting us. We are looking into your request. [stub reply]"


class OpenAICompatibleLLM:
    """Вызов /chat/completions у любого OpenAI-совместимого API через стандартную библиотеку."""

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 30) -> None:
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def complete(self, prompt: str) -> str:
        body = {"model": self.model, "messages": [{"role": "user", "content": prompt}]}
        request = urllib.request.Request(
            self.url,
            data=json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            reply = json.loads(response.read())
        return str(reply["choices"][0]["message"]["content"]).strip()


def make_llm(base_url: str, api_key: str, model: str) -> LLM:
    """Без ключа возвращает заглушку, с ключом OpenAI-совместимый клиент."""
    if not api_key.strip():
        return StubLLM()
    return OpenAICompatibleLLM(
        base_url=base_url.strip(), api_key=api_key.strip(), model=model.strip()
    )


def llm_from_env() -> LLM:
    return make_llm(
        base_url=os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
        api_key=os.environ.get("LLM_API_KEY", ""),
        model=os.environ.get("LLM_MODEL", "gpt-4.1-mini"),
    )


def classify_with_llm(llm: LLM, subject: str, body: str) -> Category:
    prompt = (
        f"{CLASSIFY_PROMPT_START} of the support ticket. "
        "Answer with one word: billing, technical, account or other.\n\n"
        f"Subject: {subject}\n\n{body}"
    )
    answer = llm.complete(prompt).strip().strip(".").lower()
    try:
        return Category(answer)
    except ValueError:
        return Category.OTHER
