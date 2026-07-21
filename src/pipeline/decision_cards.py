from __future__ import annotations

import pandas as pd


RECOMMENDATIONS = {
    "Listing effort": {
        "decision": "Lead positioning with time savings and workflow automation.",
        "next_action": "Test 'Create high-quality listings faster' with high-volume and growth sellers.",
        "risk": "Avoid promising fully autonomous listing quality without human review.",
    },
    "Pricing uncertainty": {
        "decision": "Make marketplace-informed pricing guidance a core value pillar.",
        "next_action": "Validate willingness to use price recommendations and identify trust thresholds.",
        "risk": "Do not imply guaranteed sale price or revenue outcomes.",
    },
    "Fees and profitability": {
        "decision": "Address ROI and seller economics directly in messaging.",
        "next_action": "Build a transparent value calculator and test against fee-sensitive segments.",
        "risk": "AI messaging cannot compensate for unresolved pricing or policy concerns.",
    },
    "Search and discovery": {
        "decision": "Position the product around visibility and buyer reach—not AI novelty.",
        "next_action": "Test proof points tied to impressions, qualified traffic, and conversion.",
        "risk": "Do not promise ranking improvements without substantiated evidence.",
    },
    "Trust and safety": {
        "decision": "Elevate trust, authenticity, and risk transparency in the GTM narrative.",
        "next_action": "Partner with Legal, Trust, and Safety before publishing claims.",
        "risk": "Safety signals may require escalation rather than marketing action.",
    },
    "Shipping and fulfillment": {
        "decision": "Include operational simplicity as a supporting messaging pillar.",
        "next_action": "Segment feedback by occasional versus professional sellers.",
        "risk": "Avoid masking policy or carrier problems with copy changes.",
    },
    "App reliability": {
        "decision": "Treat reliability as a launch-readiness gate, not a messaging problem.",
        "next_action": "Escalate recurring defects and delay promotion if critical journeys fail.",
        "risk": "A campaign may amplify negative sentiment when product quality is unstable.",
    },
    "Customer support": {
        "decision": "Build clear expectation-setting and escalation guidance into launch assets.",
        "next_action": "Map top support questions into FAQs and in-product education.",
        "risk": "Do not automate sensitive support decisions without human oversight.",
    },
}


def build_decision_cards(summary: pd.DataFrame) -> list[dict]:
    cards: list[dict] = []
    for _, row in summary.head(5).iterrows():
        rec = RECOMMENDATIONS.get(
            row["theme"],
            {
                "decision": "Investigate this recurring signal before finalizing GTM.",
                "next_action": "Run targeted research and validate the affected segment.",
                "risk": "Insufficient evidence for a broad recommendation.",
            },
        )
        cards.append(
            {
                "theme": row["theme"],
                "mentions": int(row["mentions"]),
                "source_types": int(row["source_types"]),
                "confidence": int(row["confidence"]),
                **rec,
            }
        )
    return cards
