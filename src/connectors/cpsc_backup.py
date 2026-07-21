from __future__ import annotations

import requests

from .base import Connector, Signal


class CPSCRecallConnector(Connector):
    BASE_URL = "https://www.saferproducts.gov/RestWebServices/Recall"

    def fetch(self, product_name: str = "", limit: int = 50, **kwargs) -> list[Signal]:
        params = {"format": "json"}
        if product_name.strip():
            params["ProductName"] = product_name.strip()

        response = requests.get(self.BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()

        signals: list[Signal] = []
        for item in payload[:limit]:
            products = item.get("Products") or []
            hazards = item.get("Hazards") or []
            injuries = item.get("Injuries") or []
            title = item.get("Title", "")
            description = item.get("Description", "")
            product_text = "; ".join(
                p.get("Name", "") for p in products if isinstance(p, dict)
            )
            hazard_text = "; ".join(
                h.get("Name", "") for h in hazards if isinstance(h, dict)
            )
            injury_text = "; ".join(
                i.get("Name", "") for i in injuries if isinstance(i, dict)
            )

            combined = " | ".join(
                part for part in [
                    title,
                    description,
                    f"Products: {product_text}" if product_text else "",
                    f"Hazards: {hazard_text}" if hazard_text else "",
                    f"Injuries: {injury_text}" if injury_text else "",
                ] if part
            )

            recall_id = str(item.get("RecallID", ""))
            url = f"https://www.cpsc.gov/Recalls/{recall_id}" if recall_id else None
            signals.append(
                Signal(
                    source="CPSC",
                    source_type="regulatory_risk",
                    text=combined,
                    created_at=item.get("RecallDate"),
                    url=url,
                    external_id=recall_id or None,
                    metadata={"raw_title": title},
                )
            )
        return signals
