# PMM Intelligence OS - GenAI Agents and Governance Deep Dive

## Agent count

The system currently uses two GenAI agents.

| Agent | Role |
|---|---|
| Customer Intelligence Agent | Synthesizes normalized evidence into PMM insights and recommendations |
| Governance Reviewer | Audits the first agent's recommendations against the original evidence |

The connectors, deterministic baseline, Streamlit interface, and normalization functions are not agents. They are deterministic system components.

## Agent 1: Customer Intelligence Agent

### Purpose

The Customer Intelligence Agent turns evidence into PMM decision inputs.

It answers:

- What customer or market problem is emerging?
- Which segment appears affected?
- What does this mean for positioning, messaging, or GTM?
- What recommendation should the PMM consider?
- What action should happen next?
- What guardrail is required?
- What evidence is missing?

### Inputs

The agent receives:

- product name;
- launch goal;
- target market;
- normalized evidence packet;
- source types;
- evidence row IDs.

### Outputs

The agent returns a structured intelligence report containing:

- executive summary;
- customer problem;
- affected segments;
- evidence summary;
- evidence row IDs;
- counter-evidence or uncertainty;
- PMM implication;
- recommendation;
- next action;
- guardrail;
- confidence level;
- confidence rationale;
- missing evidence;
- recommended research questions.

## Agent 2: Reviewer and Governance Agent

### Purpose

The Governance Reviewer prevents draft recommendations from being treated as final PMM decisions.

It checks:

- whether the cited rows support the recommendation;
- whether source types are used correctly;
- whether customer evidence is confused with news or regulatory signals;
- whether counter-evidence was ignored;
- whether confidence is overstated;
- whether a product problem is being reframed as a messaging problem;
- whether legal, trust, safety, product, or research review is required.

### Outputs

For each insight, the reviewer returns:

- approve, revise, or reject verdict;
- evidence alignment;
- valid supporting row IDs;
- unsupported or misused row IDs;
- governance issues;
- reviewer rationale;
- revised recommendation;
- revised next action;
- revised guardrail;
- adjusted confidence;
- human-review requirement.

## Prompt framework

The project does not use a named agent framework such as ReAct or LangGraph. It uses a structured prompt contract.

Each agent prompt includes:

1. **Role** - the agent's responsibility.
2. **Business context** - product, launch goal, market.
3. **Evidence boundary** - use only supplied evidence.
4. **Source semantics** - what each source type means.
5. **Task decomposition** - what the agent must analyze.
6. **Guardrails** - what not to invent or overstate.
7. **Structured output schema** - required fields validated by Pydantic.

## Why structured outputs

The system is not designed as a free-form chatbot. It needs stable fields that the UI and governance layer can rely on.

Pydantic schemas provide a contract for:

- required fields;
- allowed values;
- evidence row IDs;
- confidence labels;
- structured recommendations;
- governance verdicts.

## Evidence validation

The system validates that returned evidence row IDs exist in the evidence frame. This prevents the model from citing records that are not in the dataset.

The reviewer also checks whether cited rows are actually appropriate for the recommendation.

## Hallucination controls

The project reduces, but does not eliminate, hallucination risk through:

- bounded evidence context;
- source-type preservation;
- explicit instruction not to invent claims;
- structured output validation;
- evidence row ID validation;
- second-pass governance review;
- visible source records;
- human final decision ownership.

## Why two agents

The first agent is optimized for PMM synthesis. The second is optimized for skepticism, evidence quality, and governance.

This separation creates a control point:

```text
Generation
    ↓
Governance review
    ↓
Human decision
```

The reviewer currently uses the same underlying model by default, so it is logically separate but not fully model-independent. In production, the reviewer could use a separate model, deterministic policy checks, human evaluation, and specialist escalation workflows.

## What is agentic and what is not

This is a constrained agentic workflow, not a fully autonomous system.

It is agentic because:

- agents have specialized roles;
- they receive defined context;
- they produce structured business outputs;
- one agent reviews the output of another;
- the workflow supports escalation.

It is not fully autonomous because:

- the PMM chooses sources;
- the PMM initiates each stage;
- the system does not dynamically decide which tools to call;
- there is no autonomous planning loop yet.

## Next governance improvements

Potential production improvements include:

- a deterministic policy layer;
- separate reviewer model;
- human-labeled test cases;
- acceptance and override tracking;
- legal, trust, safety, and research routing;
- model and prompt versioning;
- audit logs for every recommendation.
