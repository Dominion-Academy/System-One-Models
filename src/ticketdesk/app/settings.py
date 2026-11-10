import os
from dataclasses import dataclass

from src.ticketdesk.llm import LLM, make_llm


def default_laya_url() -> str:
    return f"http://localhost:{os.environ.get('LAYA_PORT', '5000')}"


@dataclass(frozen=True)
class Settings:
    laya_url: str
    laya_key: str
    laya_model: str
    llm_base_url: str
    llm_key: str
    llm_model: str
    retry: bool = False  # повторы запросов к System One по политике resilient.FAST_RETRY

    @property
    def uses_stub_llm(self) -> bool:
        return not self.llm_key.strip()

    def make_llm(self) -> LLM:
        return make_llm(self.llm_base_url, self.llm_key, self.llm_model)


DEFAULTS = Settings(
    laya_url=default_laya_url(),
    laya_key="local",
    laya_model="jev-latest",
    llm_base_url=os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
    llm_key="",
    llm_model=os.environ.get("LLM_MODEL", "gpt-4.1-mini"),
)
