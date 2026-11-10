import re

from typesafe_sdk import Noul, TypeSafeClient

ARTICLES = {
    "refunds": "Refunds. Duplicate or wrong charges are refunded to the original card within "
    "5-10 business days. Open Billing > Payments and press 'Request refund' next to the charge.",
    "invoices": "Invoices. All invoices are in Billing > Invoices. You can download PDF copies for "
    "the last 24 months and add a VAT number in Billing > Company details.",
    "password_reset": "Password reset. Press 'Forgot password' on the login page. The reset email "
    "arrives within 5 minutes; check the spam folder. Links expire after one hour.",
    "two_factor": "Two-factor authentication. Enable 2FA in Profile > Security with any TOTP app. "
    "If you lost your phone, use a backup code or ask your workspace admin to reset 2FA.",
    "webhooks": "Webhooks. We retry failed webhook deliveries 5 times with backoff. Each request "
    "has an X-Signature header: an HMAC-SHA256 of the body with your webhook secret.",
    "api_limits": "API rate limits. The API allows 600 requests per minute per workspace. "
    "List endpoints return 100 items per page; use the 'cursor' parameter for the next page.",
    "export": "Data export. Settings > Export creates a CSV or JSON archive of all projects. "
    "Large exports run in the background and the download link is sent by email.",
    "team": "Team members. Admins invite colleagues in Settings > Members. Roles: Viewer, "
    "Editor, Manager, Admin. Removing a member revokes access immediately.",
}

QUERIES = [
    ("Where can I download last year's invoices with our VAT number?", "invoices"),
    ("The password reset email never arrives.", "password_reset"),
    ("I lost my phone with the authenticator app and can't sign in.", "two_factor"),
    ("How do I verify that a webhook request really came from you?", "webhooks"),
    ("I need a copy of all our project data for an audit.", "export"),
    ("How do I give a new colleague access to our workspace?", "team"),
    ("Your system took my payment two times, please return it.", "refunds"),
    ("Our integration gets blocked after a burst of requests.", "api_limits"),
    ("Can I take all my projects with me if we cancel?", "export"),
    ("How do I check that the payload you send to our endpoint is genuine?", "webhooks"),
]

WORD = re.compile(r"[a-z0-9]+")


def words(text: str) -> set[str]:
    return {word for word in WORD.findall(text.lower()) if len(word) > 3}


def keyword_search(query: str, top_k: int = 4) -> list[str]:
    query_words = words(query)
    scored = sorted(ARTICLES, key=lambda key: -len(query_words & words(ARTICLES[key])))
    return scored[:top_k]


RELEVANT = Noul(
    instructions="The help article answers the customer's question",
    criteria={
        "true": "The article explains how to solve exactly this problem",
        "false": "The article is about a different topic",
    },
)


def relevance(client: TypeSafeClient, query: str, article_ids: list[str]) -> dict[str, float]:
    """Один запрос на статью: вопрос клиента и статья в state."""
    scores = {}
    for article_id in article_ids:
        state = f"Customer question: {query}\n\nHelp article: {ARTICLES[article_id]}"
        response = client.system_one(state=state, questions={"relevant": RELEVANT})
        scores[article_id] = response.nouls["relevant"].noul
    return scores


def rerank(client: TypeSafeClient, query: str, candidates: list[str]) -> list[str]:
    """Переставляет кандидатов поиска по вероятности релевантности от Noul."""
    scores = relevance(client, query, candidates)
    return sorted(candidates, key=lambda article_id: -scores[article_id])
