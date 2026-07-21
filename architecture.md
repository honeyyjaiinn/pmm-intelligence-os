# PMM Intelligence OS - Architecture Deep Dive

## Purpose

PMM Intelligence OS is an independent portfolio prototype that explores how a Product Marketing team can move from fragmented signals to governed, evidence-backed decisions.

The product is designed around one operating principle:

> Insight before generation. Evidence before recommendation. Human judgment before execution.

## High-level workflow

```text
Signals & Evidence
        ↓
Signal Hub
        ↓
Normalization + deduplication
        ↓
Deterministic baseline
        ↓
Customer Intelligence Agent
        ↓
Governance Reviewer
        ↓
PMM decision
```

## Source categories

The system separates source types so that the model does not treat all evidence as equivalent.

| Source category | Example sources | How the system treats it |
|---|---|---|
| Voice of Customer | Reviews, interviews, support tickets, community discussions | Direct customer evidence when authorized and relevant |
| Organizational knowledge | Past launch learnings, playbooks, prior messaging | Context and institutional learning, not current customer evidence |
| Competitive intelligence | News, competitor announcements, market signals | Market context, not customer sentiment |
| Product-risk intelligence | CPSC recalls, safety data | Regulatory and safety signal, not marketing copy |

## Connector layer

Every connector returns a consistent internal signal object. This lets future sources be added without rewriting the intelligence agents.

Current or prepared connectors include:

- CSV sample connector
- CPSC recall connector
- NewsAPI connector, tested locally but disabled in public deployment because of usage limitations
- Reddit connector, prepared for official API access

Future enterprise connectors could include:

- Glean
- Airtable
- Qualtrics
- Zendesk
- Salesforce
- GetWhy or other research platforms
- Confluence or internal knowledge bases

## Common signal schema

Each record is normalized into a common structure:

```text
source
source_type
text
created_at
rating
url
external_id
metadata
```

This decouples ingestion from intelligence. The AI layer does not need to know whether a signal originally came from a CSV file, API response, research platform, or support system.

## Normalization and deduplication

The normalization layer:

- cleans text;
- preserves source metadata;
- assigns source type;
- creates fingerprints for deduplication;
- removes repeated records;
- keeps traceability back to original source records.

The deduplication step matters because repeated feedback can otherwise inflate the importance of a theme.

## Deterministic baseline

Before calling the LLM, the system runs a transparent baseline that detects known PMM themes such as:

- listing effort;
- pricing uncertainty;
- search and discovery;
- trust and safety;
- shipping and fulfillment;
- app reliability;
- customer support.

The baseline provides a stable reference point for evaluating whether the GenAI layer is adding strategic value rather than simply producing better language.

## Streamlit architecture

The product is deployed as a multipage Streamlit application:

1. **Start Here** - explains the product principle and journey.
2. **Prepare Evidence** - selects sources and prepares the evidence store.
3. **Generate Intelligence** - runs the Customer Intelligence Agent.
4. **Review Recommendation** - runs the Governance Reviewer.
5. **Evidence & Audit** - exposes the deterministic baseline and normalized records.

The app uses Streamlit session state to preserve prepared evidence and agent outputs while the user moves between pages.

## Deployment

The prototype is deployed on Streamlit Community Cloud with GitHub-based deployment.

Secrets such as model API keys are not committed to the repository. They are configured through Streamlit Secrets and exposed to the application as environment variables.

## Current limitations

This is a portfolio MVP, not a production enterprise platform. Current limitations include:

- sample datasets represent internal sources;
- no persistent decision memory yet;
- no scheduled ingestion jobs;
- no enterprise authentication or role-based access control;
- no production monitoring, tracing, or cost dashboards;
- no RAG layer yet for large internal research or brand documents.

## Next architecture steps

The next logical extensions are:

1. Human approval and decision memory.
2. Retrieval over approved launch learnings and brand guidelines.
3. Scheduled ingestion and incremental processing.
4. Formal evaluation datasets for agent outputs.
5. Production observability for cost, latency, failure modes, and usage.
