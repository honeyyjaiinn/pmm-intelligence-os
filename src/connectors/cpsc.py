from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base import Connector, Signal


class CPSCRecallConnector(Connector):
    BASE_URL = "https://www.saferproducts.gov/RestWebServices/Recall"
    HOME_URL = "https://www.saferproducts.gov/"

    def _create_session(self) -> requests.Session:
        """
        Create a browser-like session.

        SaferProducts.gov may reject Python's default requests user-agent,
        so we send normal browser headers and establish cookies first.
        """
        session = requests.Session()

        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.cpsc.gov/",
                "Connection": "keep-alive",
                "Cache-Control": "no-cache",
            }
        )

        retry_strategy = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )

        session.mount(
            "https://",
            HTTPAdapter(max_retries=retry_strategy),
        )

        return session

    def fetch(
        self,
        product_name: str = "",
        limit: int = 50,
        **kwargs,
    ) -> list[Signal]:
        params = {
            "format": "json",
        }

        if product_name.strip():
            params["ProductName"] = product_name.strip()

        session = self._create_session()

        # Establish a normal browser session and obtain any required cookies.
        try:
            session.get(self.HOME_URL, timeout=30)
        except requests.RequestException:
            # Continue because the API request may still work.
            pass

        response = session.get(
            self.BASE_URL,
            params=params,
            timeout=60,
        )

        if response.status_code == 403:
            raise RuntimeError(
                "CPSC returned HTTP 403. SaferProducts.gov blocked the "
                "automated request. Try again later or use the official "
                "CPSC CSV fallback."
            )

        response.raise_for_status()

        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "CPSC returned a response that was not valid JSON."
            ) from exc

        if not isinstance(payload, list):
            raise RuntimeError(
                "CPSC returned an unexpected response structure."
            )

        signals: list[Signal] = []

        for item in payload[:limit]:
            products = item.get("Products") or []
            hazards = item.get("Hazards") or []
            injuries = item.get("Injuries") or []
            remedies = item.get("Remedies") or []

            title = item.get("Title", "")
            description = item.get("Description", "")

            product_text = "; ".join(
                product.get("Name", "")
                for product in products
                if isinstance(product, dict) and product.get("Name")
            )

            hazard_text = "; ".join(
                hazard.get("Name", "")
                for hazard in hazards
                if isinstance(hazard, dict) and hazard.get("Name")
            )

            injury_text = "; ".join(
                injury.get("Name", "")
                for injury in injuries
                if isinstance(injury, dict) and injury.get("Name")
            )

            remedy_text = "; ".join(
                remedy.get("Name", "")
                for remedy in remedies
                if isinstance(remedy, dict) and remedy.get("Name")
            )

            combined = " | ".join(
                part
                for part in [
                    title,
                    description,
                    f"Products: {product_text}" if product_text else "",
                    f"Hazards: {hazard_text}" if hazard_text else "",
                    f"Injuries: {injury_text}" if injury_text else "",
                    f"Remedies: {remedy_text}" if remedy_text else "",
                ]
                if part
            )

            recall_id = str(item.get("RecallID", ""))

            signals.append(
                Signal(
                    source="CPSC",
                    source_type="regulatory_risk",
                    text=combined,
                    created_at=item.get("RecallDate"),
                    url=item.get("URL"),
                    external_id=recall_id or None,
                    metadata={
                        "recall_number": item.get("RecallNumber"),
                        "title": title,
                    },
                )
            )

        return signals
