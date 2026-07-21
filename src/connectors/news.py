from __future__ import annotations

import os
import requests

from .base import Connector, Signal


class NewsAPIConnector(Connector):
    BASE_URL = "https://newsapi.org/v2/everything"

    def __init__(self):
        if not os.getenv("NEWS_API_KEY"):
            raise RuntimeError("Missing NEWS_API_KEY.")
        self.api_key = os.environ["NEWS_API_KEY"]

    def fetch(self, query: str, limit: int = 25, **kwargs) -> list[Signal]:
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": min(limit, 100),
            "apiKey": self.api_key,
        }
        response = requests.get(self.BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        results: list[Signal] = []
        for article in data.get("articles", []):
            text = " | ".join(
                value for value in [
                    article.get("title"),
                    article.get("description"),
                    article.get("content"),
                ] if value
            )
            results.append(
                Signal(
                    source=article.get("source", {}).get("name", "News"),
                    source_type="competitive_intelligence",
                    text=text,
                    created_at=article.get("publishedAt"),
                    url=article.get("url"),
                    external_id=article.get("url"),
                    metadata={"author": article.get("author")},
                )
            )
        return results
