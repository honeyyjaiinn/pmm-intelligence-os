# PMM Intelligence OS - Interview Demo Notes

## One-sentence explanation

PMM Intelligence OS is a multi-source decision-intelligence prototype that turns fragmented customer, organizational, competitive, and risk signals into evidence-backed Product Marketing recommendations, audits those recommendations through a separate governance agent, and keeps the PMM as the final decision-maker.

## Five-to-seven-minute walkthrough

### 1. Problem

Product marketers often have many signals but no fast, repeatable path from evidence to decision.

Signals are fragmented across reviews, interviews, support tickets, past launches, market intelligence, and product-risk data. The challenge is not simply finding information; it is translating that information into a defensible PMM decision.

### 2. Product principle

The prototype is organized around:

```text
Signals & Evidence
        ↓
PMM Intelligence
        ↓
Governance
        ↓
PMM Decision
```

Operating principle:

> Insight before generation. Evidence before recommendation. Human judgment before execution.

### 3. Signal Hub

The Signal Hub prepares the evidence before any GenAI call runs.

It connects selected sources, normalizes records into a shared schema, deduplicates them, preserves source type, and exposes the resulting evidence store.

### 4. Deterministic baseline

The deterministic baseline detects known PMM themes using transparent rules. It is intentionally kept alongside the GenAI output so that the LLM can be compared against a predictable reference.

### 5. Customer Intelligence Agent

The first GenAI agent receives the normalized evidence and launch context. It produces structured PMM recommendations including:

- customer problem;
- affected segment;
- PMM implication;
- recommendation;
- next action;
- guardrail;
- evidence row IDs;
- missing evidence;
- research questions.

### 6. Governance Reviewer

The second GenAI agent reviews the first agent's recommendations against the original evidence. It can approve, revise, or reject each insight and flags issues such as source misuse, weak evidence, overconfidence, ignored counter-evidence, or required human escalation.

### 7. Final message

The key design principle is that AI accelerates synthesis, but evidence, governance, and human PMM judgment remain responsible for the decision.

## Likely follow-up questions

### How many agents did you build?

Two GenAI agents: the Customer Intelligence Agent and the Governance Reviewer. The connectors and deterministic baseline are not agents.

### Is it agentic?

It is a constrained agentic workflow, not a fully autonomous system. The agents have specialized responsibilities and structured outputs, but the PMM still selects sources and initiates each stage.

### Did you use RAG?

Not yet. The MVP passes a bounded evidence packet directly to the model. RAG would be the next step for scaling across large internal research libraries, brand guidelines, and past launch documents.

### Why keep the deterministic baseline?

It provides a transparent reference. The LLM may be more nuanced, but the baseline is predictable, low-cost, and easier to debug.

### How do you reduce hallucinations?

Through bounded evidence, source-type preservation, structured outputs, evidence row validation, governance review, visible citations, and human ownership of the final decision.

### Why use a reviewer agent?

Because the generation agent can produce persuasive recommendations that exceed the evidence. The reviewer creates an explicit quality gate before the PMM acts.

### Why not use LangChain or LangGraph?

The current workflow only requires two controlled model calls, so the direct SDK keeps the system transparent. An orchestration framework becomes more useful when adding dynamic tool selection, branching, retries, memory, and longer-running workflows.

### How would you scale it?

I would add scheduled ingestion, a database or warehouse for normalized signals, retrieval over internal documents, asynchronous execution, role-based access, prompt and model versioning, and formal evaluation metrics.

### What would you build next?

Human approval and decision memory: allow PMMs to approve, edit, or reject recommendations and store the rationale as reusable organizational knowledge.

## Demo path

Use the live application in this order:

1. Start Here
2. Prepare Evidence
3. Generate Intelligence
4. Review Recommendation
5. Evidence & Audit

## Suggested final line

This project was designed to show that GenAI product marketing capability is not just about producing content faster. It is about turning PMM methodology into a repeatable, governed, evidence-backed operating system.
