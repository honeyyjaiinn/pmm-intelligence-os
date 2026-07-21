from __future__ import annotations

from collections import defaultdict
import math
import pandas as pd


THEMES = {
    "Listing effort": [
        "listing", "list items", "description", "title", "photos",
        "bulk upload", "create listing", "time consuming"
    ],
    "Pricing uncertainty": [
        "price", "pricing", "priced", "worth", "sold comps", "market value"
    ],
    "Fees and profitability": [
        "fee", "fees", "profit", "margin", "commission", "expensive"
    ],
    "Search and discovery": [
        "search", "discover", "visibility", "views", "algorithm", "find items"
    ],
    "Trust and safety": [
        "scam", "fraud", "trust", "authentic", "fake", "safety", "hazard",
        "recall", "fire", "injury"
    ],
    "Shipping and fulfillment": [
        "shipping", "delivery", "label", "tracking", "package", "postage"
    ],
    "App reliability": [
        "crash", "bug", "slow", "freeze", "login", "update", "broken"
    ],
    "Customer support": [
        "support", "customer service", "appeal", "response", "help"
    ],
}


def _match_theme(text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def extract_theme_evidence(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for idx, record in frame.iterrows():
        for theme, keywords in THEMES.items():
            score = _match_theme(record["text_clean"], keywords)
            if score:
                rows.append(
                    {
                        "row_id": idx,
                        "theme": theme,
                        "match_score": score,
                        "source": record["source"],
                        "source_type": record["source_type"],
                        "text": record["text"],
                        "url": record.get("url"),
                        "rating": record.get("rating"),
                    }
                )
    return pd.DataFrame(rows)


def summarize_themes(evidence: pd.DataFrame) -> pd.DataFrame:
    if evidence.empty:
        return pd.DataFrame(
            columns=["theme", "mentions", "sources", "source_types", "confidence"]
        )

    grouped = (
        evidence.groupby("theme")
        .agg(
            mentions=("row_id", "nunique"),
            sources=("source", "nunique"),
            source_types=("source_type", "nunique"),
            keyword_hits=("match_score", "sum"),
        )
        .reset_index()
    )

    # Transparent heuristic—not a probability.
    grouped["confidence"] = grouped.apply(
        lambda row: min(
            95,
            round(
                35
                + 12 * math.log1p(row["mentions"])
                + 8 * row["source_types"]
                + 3 * row["sources"]
            ),
        ),
        axis=1,
    )
    return grouped.sort_values(
        ["confidence", "mentions", "source_types"],
        ascending=False,
    ).reset_index(drop=True)
