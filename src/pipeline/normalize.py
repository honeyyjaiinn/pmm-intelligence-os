from __future__ import annotations

import hashlib
import re
import pandas as pd


def normalize_signals(records: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(records)
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "source", "source_type", "text", "created_at", "rating",
                "url", "external_id", "metadata", "text_clean", "fingerprint"
            ]
        )

    frame["text"] = frame["text"].fillna("").astype(str)
    frame["text_clean"] = (
        frame["text"]
        .str.lower()
        .str.replace(r"https?://\S+", " ", regex=True)
        .str.replace(r"[^a-z0-9\s]", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    frame = frame[frame["text_clean"].str.len() >= 8].copy()
    frame["fingerprint"] = frame["text_clean"].map(
        lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest()
    )
    frame = frame.drop_duplicates(subset=["fingerprint"]).reset_index(drop=True)
    return frame
