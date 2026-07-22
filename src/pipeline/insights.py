from __future__ import annotations

import math

import pandas as pd


THEMES = {
    "Payment flexibility": [
        "pay in 4",
        "installment",
        "instalment",
        "split",
        "flexible",
        "budget",
        "manageable",
        "higher ticket",
        "high value",
        "afford",
    ],
    "Eligibility and checkout": [
        "eligible",
        "eligibility",
        "checkout",
        "unavailable",
        "not available",
        "disappeared",
        "declined",
        "delivery methods",
        "shipping from outside",
        "older version",
        "category",
    ],
    "Cost transparency": [
        "interest",
        "rate",
        "late fee",
        "fees",
        "total cost",
        "financing",
        "repayment",
        "more expensive",
    ],
    "Refunds and returns": [
        "refund",
        "return",
        "returned",
        "payment plan",
        "remaining installments",
        "cancel",
        "adjusted",
    ],
    "Seller understanding": [
        "seller",
        "payout",
        "ship immediately",
        "wait until",
        "default",
        "after the order has shipped",
    ],
    "Trust and financial wellbeing": [
        "trust",
        "control",
        "affordability",
        "spend beyond",
        "credit",
        "debt",
        "late",
        "payment fails",
    ],
    "Experience simplicity": [
        "easy",
        "simple",
        "smooth",
        "clear",
        "fast",
        "redirect",
        "manage",
        "pre filled",
    ],
    "Customer support": [
        "support",
        "help",
        "explain",
        "response",
        "handoff",
        "switching between",
    ],
}


def _match_theme(text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def extract_theme_evidence(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for idx, record in frame.iterrows():
        text_clean = str(record.get("text_clean", ""))
        metadata = record.get("metadata")
        metadata_theme = ""
        if isinstance(metadata, dict):
            metadata_theme = str(metadata.get("theme", "")).strip()

        for theme, keywords in THEMES.items():
            score = _match_theme(text_clean, keywords)
            if metadata_theme.lower() == theme.lower():
                score += 2

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

    # Transparent directional heuristic, not a statistical probability.
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
