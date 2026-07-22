# PMM Co-Pilot — PMM Intelligence OS

An independent portfolio prototype that turns multi-source launch evidence into evidence-backed Product Marketing recommendations, then audits those recommendations through a separate Governance Reviewer.

## What changed in this redesign

- eBay-inspired light interface using the four-color accent system
- launch dropdown with previous launches
- **Add new launch** form with launch context, outcomes, metrics, voice examples, and seed feedback
- one-click full pipeline: evidence → intelligence → governance → dashboard
- chart-led overview with sentiment, themes, source mix, time trend, confidence, and governance outcomes
- Klarna and eBay U.S. partnership as the default launch
- synthetic feedback inspired by public themes, clearly labeled as non-representative
- Airtable connector added to the Signal Hub
- NewsAPI and Reddit removed from the active Signal Hub
- Prompt Operations and production runtime policy retained in Agent Configuration

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

## Agent modes

- **Demo (cached):** runs the complete pipeline locally without model calls.
- **Live (Gemini API):** calls the Customer Intelligence Agent and then the Governance Reviewer.

Add the Gemini key to `.env` or Streamlit secrets:

```text
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.1-flash-lite
GEMINI_REVIEW_MODEL=gemini-3.1-flash-lite
```

## Airtable connector

Create an Airtable Personal Access Token with access to the required base and set:

```text
AIRTABLE_PAT=...
AIRTABLE_BASE_ID=app...
AIRTABLE_TABLE_NAME=Customer Signals
AIRTABLE_VIEW=
```

Default field names can be changed in **Signal Hub → Airtable connection**.

## Data disclosure

The default Klarna buyer feedback, interview notes, and support tickets are synthetic paraphrases inspired by recurring public themes. They are designed to demonstrate the workflow. They are not verbatim customer quotations and not a representative eBay research study.

Official eBay pages are used for launch and product facts in the organizational-knowledge sample records.

## Product principle

AI recommends. Humans decide.
