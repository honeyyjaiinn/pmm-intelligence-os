from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

import requests

from .base import Connector, Signal


class AirtableConnector(Connector):
    """Read customer-signal records from an Airtable table.

    Credentials are read from environment variables by default so that the
    Personal Access Token never appears in the Streamlit interface.
    """

    API_ROOT = "https://api.airtable.com/v0"

    def __init__(
        self,
        *,
        base_id: str | None = None,
        table_name: str | None = None,
        personal_access_token: str | None = None,
        view: str | None = None,
        text_field: str = "Feedback",
        rating_field: str = "Rating",
        date_field: str = "Created At",
        segment_field: str = "Segment",
        url_field: str = "URL",
        source_type_field: str = "Source Type",
    ) -> None:
        self.base_id = (base_id or os.getenv("AIRTABLE_BASE_ID", "")).strip()
        self.table_name = (
            table_name or os.getenv("AIRTABLE_TABLE_NAME", "Customer Signals")
        ).strip()
        self.personal_access_token = (
            personal_access_token or os.getenv("AIRTABLE_PAT", "")
        ).strip()
        self.view = (view or os.getenv("AIRTABLE_VIEW", "")).strip()
        self.text_field = text_field
        self.rating_field = rating_field
        self.date_field = date_field
        self.segment_field = segment_field
        self.url_field = url_field
        self.source_type_field = source_type_field

    def fetch(self, limit: int = 100, **_: Any) -> list[Signal]:
        if not self.personal_access_token:
            raise RuntimeError("AIRTABLE_PAT is not configured.")
        if not self.base_id:
            raise RuntimeError("AIRTABLE_BASE_ID is not configured.")
        if not self.table_name:
            raise RuntimeError("AIRTABLE_TABLE_NAME is not configured.")

        endpoint = (
            f"{self.API_ROOT}/{quote(self.base_id, safe='')}/"
            f"{quote(self.table_name, safe='')}"
        )
        headers = {"Authorization": f"Bearer {self.personal_access_token}"}
        params: dict[str, Any] = {"pageSize": min(max(limit, 1), 100)}
        if self.view:
            params["view"] = self.view

        signals: list[Signal] = []
        offset: str | None = None

        while len(signals) < limit:
            if offset:
                params["offset"] = offset

            response = requests.get(
                endpoint,
                headers=headers,
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()

            for record in payload.get("records", []):
                fields = record.get("fields", {})
                text = str(fields.get(self.text_field, "")).strip()
                if not text:
                    continue

                rating = fields.get(self.rating_field)
                try:
                    rating_value = float(rating) if rating not in (None, "") else None
                except (TypeError, ValueError):
                    rating_value = None

                source_type = str(
                    fields.get(self.source_type_field, "airtable_feedback")
                ).strip() or "airtable_feedback"

                metadata = {
                    "segment": fields.get(self.segment_field),
                    "airtable_record_id": record.get("id"),
                    "airtable_fields": fields,
                }

                signals.append(
                    Signal(
                        source=f"Airtable · {self.table_name}",
                        source_type=source_type,
                        text=text,
                        created_at=str(fields.get(self.date_field, "")) or None,
                        rating=rating_value,
                        url=str(fields.get(self.url_field, "")) or None,
                        external_id=record.get("id"),
                        metadata=metadata,
                    )
                )

                if len(signals) >= limit:
                    break

            offset = payload.get("offset")
            if not offset:
                break

        return signals
