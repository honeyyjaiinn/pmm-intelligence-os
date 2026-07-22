from __future__ import annotations

from pathlib import Path

import pandas as pd

from .base import Connector, Signal


class CSVConnector(Connector):
    def __init__(self, path: str | Path, source: str, source_type: str):
        self.path = Path(path)
        self.source = source
        self.source_type = source_type

    def fetch(self, **kwargs) -> list[Signal]:
        if not self.path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.path}")

        frame = pd.read_csv(self.path)
        if "text" not in frame.columns:
            raise ValueError("CSV must include a 'text' column.")

        results: list[Signal] = []
        reserved = {
            "text",
            "rating",
            "created_at",
            "url",
            "external_id",
        }

        for idx, row in frame.fillna("").iterrows():
            rating = None
            if "rating" in frame.columns and row.get("rating") != "":
                try:
                    rating = float(row.get("rating"))
                except (TypeError, ValueError):
                    rating = None

            metadata = {
                str(column): row.get(column)
                for column in frame.columns
                if column not in reserved and row.get(column) not in (None, "")
            }

            results.append(
                Signal(
                    source=self.source,
                    source_type=self.source_type,
                    text=str(row["text"]).strip(),
                    created_at=str(row.get("created_at", "")) or None,
                    rating=rating,
                    url=str(row.get("url", "")) or None,
                    external_id=str(row.get("external_id", idx)),
                    metadata=metadata,
                )
            )

        return [item for item in results if item.text]
