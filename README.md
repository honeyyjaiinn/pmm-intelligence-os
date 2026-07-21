# PMM Intelligence OS — MVP v0.1

An interview-ready prototype for a Product Marketing Capabilities team.

## What it does

The app combines external and simulated internal signals into evidence-backed PMM decision cards:

- Reddit discussions through Reddit OAuth
- News and competitor signals through NewsAPI
- CPSC product-recall data through the public CPSC REST API
- App-review, interview, survey, support-ticket, and past-launch data through CSV connectors

The pipeline:

`Connectors → normalized signal store → theme extraction → evidence aggregation → decision cards`

## Why CSV for app reviews?

Apple's official App Store Connect API can retrieve customer reviews only for apps managed by the authenticated developer account. It is not a general public API for collecting another company's reviews. For a lawful portfolio MVP, this project uses a CSV adapter for app reviews. In production, a company would connect its own App Store Connect account or an approved customer-feedback vendor.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

The app runs without credentials using sample Voice-of-Customer data and the public CPSC connector. Add Reddit and NewsAPI credentials to enable those connectors.

## MVP scope

The first vertical slice intentionally focuses on one PMM question:

> What customer problem should lead the positioning for a new seller productivity product?

It produces:

- top themes across sources
- supporting evidence counts
- source diversity
- a confidence heuristic
- a recommended PMM action
- evidence rows for auditability

## Production roadmap

1. Replace heuristic themes with an evaluated LLM classification pipeline.
2. Add a vector store and retrieval for brand guidelines and past GTM material.
3. Persist normalized events in a warehouse.
4. Schedule ingestion and incremental updates.
5. Add human approval, feedback capture, governance, and prompt versioning.
6. Connect Airtable, Glean, Confluence, GetWhy, Qualtrics, and Zendesk through authorized enterprise APIs.
