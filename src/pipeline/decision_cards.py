from __future__ import annotations

import pandas as pd


RECOMMENDATIONS = {
    "Payment flexibility": {
        "decision": "Lead with flexibility and purchase control, not with credit novelty.",
        "next_action": "Test value messages by category and order value, especially electronics, collectibles, fashion, and refurbished goods.",
        "risk": "Do not frame financing as universally affordable or encourage spending beyond a buyer's means.",
    },
    "Eligibility and checkout": {
        "decision": "Make eligibility clear before the final checkout step.",
        "next_action": "Create eligibility messaging for order value, category, shipping origin, delivery method, location, and app version.",
        "risk": "A listing-level promise that disappears at checkout can reduce trust and conversion.",
    },
    "Cost transparency": {
        "decision": "Separate Pay in 4 from interest-bearing financing in every message.",
        "next_action": "Show repayment timing, interest, late-fee risk, and total cost before confirmation.",
        "risk": "Financial claims and disclosures require Legal and Compliance review.",
    },
    "Refunds and returns": {
        "decision": "Use one joined-up eBay and Klarna explanation for returns and payment-plan changes.",
        "next_action": "Build a visual refund timeline covering eBay approval, Klarna adjustment, and expected timing.",
        "risk": "Unclear ownership between two brands can create support loops and trust loss.",
    },
    "Seller understanding": {
        "decision": "Explain that Klarna is a buyer payment choice and does not require sellers to manage installments.",
        "next_action": "Add a seller FAQ covering payout, shipping, buyer default, and returns.",
        "risk": "Seller confusion can lead to unnecessary delays or incorrect buyer guidance.",
    },
    "Trust and financial wellbeing": {
        "decision": "Balance the convenience story with responsible-use language and clear terms.",
        "next_action": "Review all affordability language with Legal, Compliance, and Customer Trust teams.",
        "risk": "Overly promotional BNPL messaging can create regulatory, brand, and customer-wellbeing risk.",
    },
    "Experience simplicity": {
        "decision": "Use the smooth checkout and payment-management experience as supporting proof.",
        "next_action": "Measure redirect completion, payment-plan visibility, and support contacts after checkout.",
        "risk": "A simple happy path should not hide eligibility or support friction.",
    },
    "Customer support": {
        "decision": "Clarify which brand owns each support moment.",
        "next_action": "Create routing guidance for checkout eligibility, approval decisions, returns, and payment schedules.",
        "risk": "Customers may be passed between eBay and Klarna when ownership is unclear.",
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
