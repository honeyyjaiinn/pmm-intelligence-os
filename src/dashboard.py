from __future__ import annotations

from collections import Counter
from datetime import date, datetime
import html
import os
import re
import time
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from src.connectors import (
    AirtableConnector,
    CPSCRecallConnector,
    CSVConnector,
    Signal,
)
from src.ebay_ui import (
    EBAY_COLORS,
    render_launch_header,
    render_pipeline_banner,
    render_sidebar_brand,
)
from src.pipeline import (
    build_decision_cards,
    extract_theme_evidence,
    normalize_signals,
    summarize_themes,
)
from src.pipeline.gemini_insights import (
    IntelligenceReport,
    StrategicInsight,
    generate_intelligence_report,
)
from src.pipeline.gemini_reviewer import (
    GovernanceReview,
    InsightReview,
    ReviewIssue,
    review_intelligence_report,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SENTIMENT_COLORS = {
    "Positive": EBAY_COLORS["green"],
    "Neutral": EBAY_COLORS["yellow"],
    "Negative": EBAY_COLORS["red"],
}

VERDICT_COLORS = {
    "approve": EBAY_COLORS["green"],
    "revise": EBAY_COLORS["yellow"],
    "reject": EBAY_COLORS["red"],
}

CONFIDENCE_COLORS = {
    "high": EBAY_COLORS["green"],
    "medium": EBAY_COLORS["yellow"],
    "low": EBAY_COLORS["red"],
}


# ---------------------------------------------------------------------------
# Launch registry and state
# ---------------------------------------------------------------------------


def _default_launches() -> dict[str, dict[str, Any]]:
    return {
        "klarna-ebay-us": {
            "id": "klarna-ebay-us",
            "name": "Klarna & eBay Partnership",
            "display_name": "Klarna Buy Now, Pay Later on eBay",
            "tagline": "Flexible payments for eligible U.S. marketplace purchases",
            "category": "Payments · Checkout financing · Circular commerce",
            "launch_date": "2025-04-23",
            "target_markets": "United States",
            "expansion_markets": (
                "U.K., Austria, France, Italy, the Netherlands, Spain"
            ),
            "competitors": "Affirm, Afterpay, PayPal Pay Later, Shop Pay Installments",
            "launch_goal": (
                "Increase adoption of flexible payments while preserving "
                "checkout clarity, customer trust, and responsible-use standards"
            ),
            "why_launch": (
                "eBay expanded its global Klarna partnership to the U.S. to give "
                "eligible shoppers more choice and flexibility at checkout. The "
                "opportunity is strongest for higher-consideration purchases such "
                "as electronics, fashion, collectibles, refurbished products, and "
                "other items where paying the full amount upfront can be a barrier."
            ),
            "expected_outcomes": [
                "More eligible buyers can complete higher-consideration purchases using a payment schedule that fits their budget.",
                "Improved checkout choice and reduced friction caused by a single upfront payment.",
                "Clearer education on eligibility, Pay in 4, financing costs, refunds, and support ownership.",
                "A stronger circular-commerce story through the Klarna-to-eBay resell experience.",
            ],
            "success_metrics": [
                "Klarna option exposure and selection rate",
                "Checkout completion for eligible orders",
                "Average order value and conversion by eligible category",
                "Eligibility-related abandonment and support contacts",
                "Refund-plan adjustment time",
                "Buyer and seller sentiment by journey stage",
            ],
            "supporting_insights": [
                "The partnership launched in the U.S. after earlier rollout across key European markets.",
                "Pay in 4 and longer-term financing serve different customer needs and require different disclosure standards.",
                "Eligibility varies by order value, location, currency, shipping origin, category, delivery method, and app version.",
                "Public discussion shows interest in flexibility alongside confusion about checkout availability, shipping, seller payout, and refunds.",
            ],
            "brand_voice": [
                "More ways to pay for the things you love.",
                "Clear choice. Flexible payments. Confident checkout.",
            ],
            "feedback": [],
            "sample_dataset": True,
        },
        "ebay-vault": {
            "id": "ebay-vault",
            "name": "eBay Vault",
            "display_name": "eBay Vault — Graded Card Storage",
            "tagline": "Secure storage and streamlined resale for collectors",
            "category": "Collectibles · Trust · Fulfillment",
            "launch_date": "2025-02-10",
            "target_markets": "United States",
            "expansion_markets": "",
            "competitors": "PSA Vault, Fanatics Collect, PWCC",
            "launch_goal": "Increase collector trust and repeat activity for high-value graded cards",
            "why_launch": (
                "Collectors need secure storage, clear ownership, and a simple path "
                "from purchase to resale without repeatedly shipping valuable cards."
            ),
            "expected_outcomes": [
                "Reduce handling friction for high-value cards.",
                "Increase trust in storage and ownership records.",
                "Support faster resale within the marketplace.",
            ],
            "success_metrics": [
                "Vault adoption",
                "Repeat purchase rate",
                "Resale time",
                "Trust-related support contacts",
            ],
            "supporting_insights": [
                "Collectors value security but need transparent fees and withdrawal rules.",
                "Proof of custody and condition is central to trust.",
            ],
            "brand_voice": ["Store securely. Sell when the moment is right."],
            "feedback": [
                "I like not having to ship an expensive card again before reselling it.",
                "The storage process feels secure, but the fee structure needs to be easier to compare.",
                "I want clearer timing for withdrawals and physical delivery.",
                "The ownership history gives me more confidence as a buyer.",
            ],
            "sample_dataset": False,
        },
        "ebay-certified-fitment": {
            "id": "ebay-certified-fitment",
            "name": "eBay Guaranteed Fit",
            "display_name": "eBay Guaranteed Fit — Auto Parts",
            "tagline": "More confidence that the part will fit the vehicle",
            "category": "Motors · Trust · Returns",
            "launch_date": "2025-01-15",
            "target_markets": "United States",
            "expansion_markets": "Canada",
            "competitors": "Amazon Automotive, RockAuto, AutoZone",
            "launch_goal": "Reduce fitment uncertainty and avoid preventable returns",
            "why_launch": (
                "Vehicle compatibility is a major source of buyer hesitation and "
                "returns in automotive parts."
            ),
            "expected_outcomes": [
                "Increase confidence before purchase.",
                "Reduce fitment-related returns.",
                "Improve seller listing quality.",
            ],
            "success_metrics": [
                "Fitment confirmation usage",
                "Fitment-related return rate",
                "Conversion on compatible listings",
            ],
            "supporting_insights": [
                "Buyers want compatibility explained in plain language.",
                "Sellers need easy tools to provide accurate vehicle data.",
            ],
            "brand_voice": ["The right part. The first time."],
            "feedback": [
                "The fit check made me more confident before ordering.",
                "My trim level was missing, so I still had to contact the seller.",
                "Returning an incompatible part was easier than expected.",
                "The compatibility details need to be more visible on mobile.",
            ],
            "sample_dataset": False,
        },
    }


def initialize_dashboard_state() -> None:
    defaults: dict[str, Any] = {
        "launches": _default_launches(),
        "active_launch_id": "klarna-ebay-us",
        "launch_selector": "klarna-ebay-us",
        "show_new_launch_form": False,
        "agent_mode": "Demo (cached)",
        "pipeline_requested": False,
        "pipeline_running": False,
        "pipeline_complete": False,
        "pipeline_error": "",
        "last_run_at": None,
        "run_history": [],
        "evidence_frame": None,
        "selected_sources": [],
        "connector_errors": [],
        "baseline_evidence": None,
        "baseline_summary": None,
        "baseline_cards": [],
        "gemini_report": None,
        "governance_review": None,
        # Signal Hub
        "use_reviews": True,
        "use_interviews": True,
        "use_support": True,
        "use_past_launches": True,
        "use_airtable": False,
        "use_cpsc": False,
        "cpsc_query": "lithium battery",
        "airtable_base_id": os.getenv("AIRTABLE_BASE_ID", ""),
        "airtable_table_name": os.getenv("AIRTABLE_TABLE_NAME", "Customer Signals"),
        "airtable_view": os.getenv("AIRTABLE_VIEW", ""),
        "airtable_text_field": "Feedback",
        "airtable_rating_field": "Rating",
        "airtable_date_field": "Created At",
        "airtable_segment_field": "Segment",
        "airtable_source_type_field": "Source Type",
        # Customer Intelligence configuration
        "intel_analysis_objective": "Launch adoption and readiness",
        "intel_output_depth": "Balanced",
        "intel_max_insights": 4,
        "intel_min_evidence_records": 2,
        "intel_segment_focus": "All evidence-supported segments",
        "intel_confidence_policy": "Conservative",
        "intel_require_counter_evidence": True,
        "intel_require_guardrails": True,
        # Governance configuration
        "governance_strictness": "High",
        "governance_required_alignment": "Strong",
        "governance_downgrade_overconfidence": True,
        "governance_human_review_threshold": "High-risk or unsupported claims",
        "governance_escalation_categories": [
            "PMM",
            "Product",
            "Research",
            "Legal",
            "Trust & Safety",
        ],
        # Runtime policy
        "runtime_preprocessing_policy": "Rules + lightweight ML",
        "runtime_bucket_dimensions": [
            "Sentiment",
            "Topic",
            "Segment",
            "Region",
            "Recency",
        ],
        "runtime_retrieval_policy": "RAG over evidence buckets and representative records",
        "runtime_model_routing": "Low-cost tagging models; reasoning model for synthesis",
        "runtime_optimization_priority": "Balanced quality, latency, and cost",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Prepare evidence once so the dashboard opens with useful charts.
    if st.session_state.evidence_frame is None:
        _refresh_evidence()


def get_active_launch() -> dict[str, Any]:
    launches = st.session_state.launches
    launch_id = st.session_state.active_launch_id
    if launch_id not in launches:
        launch_id = next(iter(launches))
        st.session_state.active_launch_id = launch_id
        st.session_state.launch_selector = launch_id
    return launches[launch_id]


def _reset_pipeline_results() -> None:
    st.session_state.pipeline_complete = False
    st.session_state.pipeline_error = ""
    st.session_state.gemini_report = None
    st.session_state.governance_review = None
    st.session_state.last_run_at = None


def _activate_launch(launch_id: str) -> None:
    if launch_id == st.session_state.active_launch_id:
        return
    st.session_state.active_launch_id = launch_id
    st.session_state.show_new_launch_form = False
    _reset_pipeline_results()
    _refresh_evidence()


# ---------------------------------------------------------------------------
# Signal preparation
# ---------------------------------------------------------------------------


def _infer_rating(text: str) -> float | None:
    lower = text.lower()
    positive = [
        "easy",
        "clear",
        "smooth",
        "confident",
        "helped",
        "like",
        "useful",
        "secure",
        "worked",
    ]
    negative = [
        "confusing",
        "missing",
        "unavailable",
        "broken",
        "declined",
        "frustrating",
        "difficult",
        "unclear",
        "problem",
    ]
    score = sum(word in lower for word in positive) - sum(
        word in lower for word in negative
    )
    if score >= 2:
        return 5.0
    if score == 1:
        return 4.0
    if score <= -2:
        return 1.0
    if score == -1:
        return 2.0
    return 3.0


def _custom_launch_signals(launch: dict[str, Any]) -> list[Signal]:
    feedback = [str(item).strip() for item in launch.get("feedback", []) if str(item).strip()]
    signals: list[Signal] = []

    for index, text in enumerate(feedback):
        rating = _infer_rating(text)
        signals.append(
            Signal(
                source="Launch seed feedback (sample)",
                source_type="app_review",
                text=text,
                created_at=date.today().isoformat(),
                rating=rating,
                external_id=f"seed-{index}",
                metadata={
                    "segment": "launch audience",
                    "synthetic": True,
                },
            )
        )

    narrative_records = [
        ("Launch rationale", launch.get("why_launch", "")),
        (
            "Expected outcomes",
            " ".join(launch.get("expected_outcomes", [])),
        ),
        (
            "Success metrics",
            " ".join(launch.get("success_metrics", [])),
        ),
    ]

    for index, (label, text) in enumerate(narrative_records):
        if not text:
            continue
        signals.append(
            Signal(
                source=f"{label} (launch configuration)",
                source_type="organizational_knowledge",
                text=str(text),
                created_at=str(launch.get("launch_date", "")) or None,
                external_id=f"launch-config-{index}",
                metadata={
                    "segment": "organizational learning",
                    "synthetic": False,
                },
            )
        )

    return signals


def _prepare_evidence() -> tuple[pd.DataFrame, list[str], list[str]]:
    launch = get_active_launch()
    signals: list[Signal] = []
    errors: list[str] = []
    selected_sources: list[str] = []

    def add_csv(filename: str, source: str, source_type: str) -> None:
        connector = CSVConnector(
            PROJECT_ROOT / "sample_data" / filename,
            source,
            source_type,
        )
        signals.extend(connector.fetch())
        selected_sources.append(source)

    if launch.get("sample_dataset"):
        if st.session_state.use_reviews:
            add_csv(
                "app_reviews.csv",
                "Buyer feedback (synthetic, public-theme inspired)",
                "app_review",
            )
        if st.session_state.use_interviews:
            add_csv(
                "interviews.csv",
                "Customer interviews (synthetic)",
                "interview",
            )
        if st.session_state.use_support:
            add_csv(
                "support_tickets.csv",
                "Support tickets (synthetic)",
                "support",
            )
        if st.session_state.use_past_launches:
            add_csv(
                "past_launches.csv",
                "Launch and product knowledge",
                "organizational_knowledge",
            )
    else:
        signals.extend(_custom_launch_signals(launch))
        selected_sources.append("Launch-specific sample evidence")

    if st.session_state.use_airtable:
        try:
            connector = AirtableConnector(
                base_id=st.session_state.airtable_base_id,
                table_name=st.session_state.airtable_table_name,
                view=st.session_state.airtable_view,
                text_field=st.session_state.airtable_text_field,
                rating_field=st.session_state.airtable_rating_field,
                date_field=st.session_state.airtable_date_field,
                segment_field=st.session_state.airtable_segment_field,
                source_type_field=st.session_state.airtable_source_type_field,
            )
            signals.extend(connector.fetch(limit=100))
            selected_sources.append(
                f"Airtable · {st.session_state.airtable_table_name}"
            )
        except Exception as exc:  # connector errors should not break the demo
            errors.append(f"Airtable: {exc}")

    if st.session_state.use_cpsc:
        try:
            signals.extend(
                CPSCRecallConnector().fetch(
                    product_name=st.session_state.cpsc_query,
                    limit=20,
                )
            )
            selected_sources.append("CPSC recalls")
        except Exception as exc:
            errors.append(f"CPSC: {exc}")

    frame = normalize_signals([signal.to_dict() for signal in signals])
    return frame, errors, selected_sources


def _refresh_evidence() -> None:
    frame, errors, selected_sources = _prepare_evidence()
    evidence = extract_theme_evidence(frame)
    summary = summarize_themes(evidence)

    st.session_state.evidence_frame = frame
    st.session_state.connector_errors = errors
    st.session_state.selected_sources = selected_sources
    st.session_state.baseline_evidence = evidence
    st.session_state.baseline_summary = summary
    st.session_state.baseline_cards = build_decision_cards(summary)


# ---------------------------------------------------------------------------
# Sentiment and demo agents
# ---------------------------------------------------------------------------


def _metadata_value(metadata: Any, key: str) -> str:
    if isinstance(metadata, dict):
        value = metadata.get(key, "")
        return str(value).strip()
    return ""


def _sentiment_label(row: pd.Series) -> str:
    metadata_sentiment = _metadata_value(row.get("metadata"), "sentiment").lower()
    if metadata_sentiment in {"positive", "neutral", "negative"}:
        return metadata_sentiment.title()

    rating = row.get("rating")
    try:
        numeric_rating = float(rating)
        if pd.notna(numeric_rating):
            if numeric_rating >= 4:
                return "Positive"
            if numeric_rating <= 2:
                return "Negative"
            return "Neutral"
    except (TypeError, ValueError):
        pass

    text = str(row.get("text", ""))
    inferred = _infer_rating(text)
    if inferred is None:
        return "Neutral"
    if inferred >= 4:
        return "Positive"
    if inferred <= 2:
        return "Negative"
    return "Neutral"


def _frame_with_analysis(frame: pd.DataFrame) -> pd.DataFrame:
    enriched = frame.copy()
    if enriched.empty:
        enriched["sentiment"] = []
        enriched["segment"] = []
        enriched["theme"] = []
        return enriched

    enriched["sentiment"] = enriched.apply(_sentiment_label, axis=1)
    enriched["segment"] = enriched["metadata"].map(
        lambda value: _metadata_value(value, "segment") or "Unspecified"
    )
    enriched["theme"] = enriched["metadata"].map(
        lambda value: _metadata_value(value, "theme") or "Unclassified"
    )
    return enriched


def _rows_for_theme(theme: str, limit: int = 6) -> list[int]:
    evidence = st.session_state.baseline_evidence
    frame = st.session_state.evidence_frame
    if evidence is None or evidence.empty:
        return list(frame.index[: max(2, min(limit, len(frame)))])

    rows = (
        evidence.loc[evidence["theme"] == theme, "row_id"]
        .drop_duplicates()
        .head(limit)
        .astype(int)
        .tolist()
    )
    if len(rows) < 2:
        for row_id in frame.index.tolist():
            if row_id not in rows:
                rows.append(int(row_id))
            if len(rows) >= 2:
                break
    return rows


def _segments_for_rows(frame: pd.DataFrame, row_ids: list[int]) -> list[str]:
    segments: list[str] = []
    for row_id in row_ids:
        if row_id not in frame.index:
            continue
        segment = _metadata_value(frame.loc[row_id].get("metadata"), "segment")
        if segment and segment not in segments:
            segments.append(segment)
    return segments[:4] or ["Evidence-supported launch audience"]


def _demo_intelligence_report() -> IntelligenceReport:
    frame = st.session_state.evidence_frame
    cards = st.session_state.baseline_cards
    launch = get_active_launch()

    if frame is None or frame.empty:
        raise RuntimeError("No evidence is available for the demo report.")

    theme_titles = {
        "Payment flexibility": "Payment flexibility is the strongest adoption promise",
        "Eligibility and checkout": "Eligibility clarity is a conversion and trust requirement",
        "Cost transparency": "Pay in 4 and financing need separate, plain-language education",
        "Refunds and returns": "Refund ownership must feel like one joined-up experience",
        "Seller understanding": "Sellers need a simple explanation of payout and shipping",
        "Trust and financial wellbeing": "Responsible-use guardrails belong in the launch story",
        "Experience simplicity": "A smooth payment-management experience can reinforce confidence",
        "Customer support": "Support routing is part of the product experience",
    }

    problem_text = {
        "Payment flexibility": "Buyers value a way to spread higher-consideration purchases, but the benefit is strongest when it is framed as choice and control rather than encouragement to spend more.",
        "Eligibility and checkout": "Some buyers only discover at checkout that Klarna is unavailable because eligibility varies by order, category, location, shipping, delivery method, or account decision.",
        "Cost transparency": "Customers can confuse interest-free Pay in 4 with interest-bearing financing and may not understand total repayment cost or late-payment consequences.",
        "Refunds and returns": "Customers are unsure how an eBay return changes their Klarna payment schedule and which company owns each step.",
        "Seller understanding": "Some sellers and buyers incorrectly assume shipping or seller payout depends on completion of the buyer's installment schedule.",
        "Trust and financial wellbeing": "The convenience message can create brand risk when terms, affordability, and responsible use are not equally visible.",
        "Experience simplicity": "The redirect and payment-management experience can feel easy on the happy path, but clarity breaks when a purchase is declined or ineligible.",
        "Customer support": "Customers may be passed between eBay and Klarna when checkout, approval, returns, and payment-plan questions are not clearly routed.",
    }

    insights: list[StrategicInsight] = []
    maximum = int(st.session_state.intel_max_insights)

    for card in cards[:maximum]:
        theme = card["theme"]
        row_ids = _rows_for_theme(theme)
        source_types = sorted(
            {
                str(frame.loc[row_id, "source_type"])
                for row_id in row_ids
                if row_id in frame.index
            }
        )
        segments = _segments_for_rows(frame, row_ids)
        confidence = (
            "high"
            if card["confidence"] >= 82 and len(source_types) >= 3
            else "medium"
            if card["confidence"] >= 64
            else "low"
        )

        insights.append(
            StrategicInsight(
                title=theme_titles.get(theme, theme),
                customer_problem=problem_text.get(
                    theme,
                    "The evidence shows a recurring customer or launch-readiness issue that needs validation before broad GTM use.",
                ),
                affected_segments=segments,
                evidence_summary=(
                    f"{card['mentions']} evidence records across "
                    f"{card['source_types']} source types point to this theme. "
                    "The records include a mix of synthetic customer evidence and clearly separated organizational knowledge."
                ),
                evidence_row_ids=row_ids,
                source_types=source_types,
                counter_evidence_or_uncertainty=(
                    "The portfolio dataset is directional and not representative of the full eBay customer base. Live conversion, eligibility, support, and refund data are still needed."
                ),
                pmm_implication=card["decision"],
                recommendation=card["decision"],
                next_action=card["next_action"],
                guardrail=card["risk"],
                confidence_level=confidence,
                confidence_rationale=(
                    "Confidence reflects evidence volume and source diversity in this demo dataset; it is not a statistical probability."
                ),
            )
        )

    if not insights:
        raise RuntimeError("The demo baseline did not produce any strategic themes.")

    top_themes = ", ".join(card["theme"] for card in cards[:3])
    return IntelligenceReport(
        executive_summary=(
            f"For {launch['display_name']}, the evidence points to {top_themes}. "
            "The opportunity is real, but launch success depends on making eligibility, total cost, refunds, and support ownership as clear as the flexibility benefit."
        ),
        insights=insights,
        missing_evidence=[
            "Representative U.S. checkout conversion and abandonment data for eligible and ineligible orders",
            "Segmented usage by category, order value, device, and buyer tenure",
            "End-to-end refund timing and support-transfer data",
            "Seller understanding of payout, shipping, and buyer default",
        ],
        recommended_research_questions=[
            "At which point do buyers first understand whether their order is eligible?",
            "Which disclosure best separates Pay in 4 from interest-bearing financing?",
            "What information prevents seller confusion about payout and shipping?",
            "Which refund message most clearly explains the eBay and Klarna handoff?",
        ],
    )


def _demo_governance_review(report: IntelligenceReport) -> GovernanceReview:
    frame = st.session_state.evidence_frame
    reviews: list[InsightReview] = []
    has_revisions = False

    for insight in report.insights:
        source_type_count = len(set(insight.source_types))
        synthetic_count = 0
        for row_id in insight.evidence_row_ids:
            if row_id not in frame.index:
                continue
            synthetic_value = _metadata_value(frame.loc[row_id].get("metadata"), "synthetic")
            if synthetic_value.lower() in {"true", "1", "yes"}:
                synthetic_count += 1

        requires_financial_review = any(
            word in insight.title.lower()
            for word in ("cost", "financing", "responsible", "refund")
        )
        alignment = "strong" if source_type_count >= 3 else "partial"
        verdict = "approve" if alignment == "strong" and not requires_financial_review else "revise"
        if verdict == "revise":
            has_revisions = True

        issues: list[ReviewIssue] = []
        if synthetic_count:
            issues.append(
                ReviewIssue(
                    category="missing_context",
                    severity="medium",
                    explanation=(
                        "The customer-facing records are synthetic examples inspired by public themes. They are useful for workflow demonstration but cannot support population-level claims."
                    ),
                    affected_row_ids=insight.evidence_row_ids,
                )
            )
        if requires_financial_review:
            issues.append(
                ReviewIssue(
                    category="safety_or_legal",
                    severity="high",
                    explanation=(
                        "Financing, affordability, interest, late-fee, and refund language requires Legal or Compliance review before external use."
                    ),
                    affected_row_ids=insight.evidence_row_ids,
                )
            )

        revised_confidence = insight.confidence_level
        if alignment != "strong" and revised_confidence == "high":
            revised_confidence = "medium"

        reviews.append(
            InsightReview(
                insight_title=insight.title,
                verdict=verdict,
                evidence_alignment=alignment,
                cited_row_ids=insight.evidence_row_ids,
                valid_supporting_row_ids=insight.evidence_row_ids,
                unsupported_or_misused_row_ids=[],
                issues=issues,
                reviewer_rationale=(
                    "The direction is supported by the available evidence. "
                    "External claims must remain bounded because the customer dataset is synthetic and directional."
                ),
                revised_customer_problem=insight.customer_problem,
                revised_pmm_implication=insight.pmm_implication,
                revised_recommendation=insight.recommendation,
                revised_next_action=insight.next_action,
                revised_guardrail=(
                    insight.guardrail
                    + " Validate wording with the responsible human owner before use."
                ),
                revised_confidence_level=revised_confidence,
                human_review_required=requires_financial_review or verdict != "approve",
            )
        )

    return GovernanceReview(
        overall_verdict=("approve_with_revisions" if has_revisions else "approve"),
        executive_assessment=(
            "The report is useful for launch planning and is generally aligned with the supplied evidence. "
            "The main limitation is that customer records are synthetic, so recommendations should guide research and message testing rather than support broad market claims."
        ),
        insight_reviews=reviews,
        cross_cutting_risks=[
            "Synthetic customer evidence is not representative of all eBay buyers or sellers.",
            "BNPL and financing language creates legal, compliance, and customer-wellbeing considerations.",
            "Eligibility and refund experiences involve two brands and require clear ownership.",
        ],
        required_human_escalations=[
            "PMM: approve final positioning and message hierarchy",
            "Product and Payments: validate eligibility and checkout behavior",
            "Legal/Compliance: review financing, affordability, interest, and late-fee language",
            "Customer Support: validate refund and escalation guidance",
        ],
        audit_summary=(
            "Evidence-backed themes may proceed to controlled PMM testing. Financial, eligibility, and refund claims require revision or human approval before external use."
        ),
    )


# ---------------------------------------------------------------------------
# Full one-click pipeline
# ---------------------------------------------------------------------------


def run_full_pipeline() -> None:
    st.session_state.pipeline_running = True
    st.session_state.pipeline_error = ""

    with st.status("Running the full PMM pipeline…", expanded=True) as status:
        try:
            st.write("1. Collecting and normalizing enabled signals")
            _refresh_evidence()
            frame = st.session_state.evidence_frame
            if frame is None or frame.empty:
                raise RuntimeError("No usable signals were collected.")
            time.sleep(0.15)

            st.write("2. Detecting themes and preparing evidence packets")
            if st.session_state.baseline_summary is None:
                raise RuntimeError("Theme preparation failed.")
            time.sleep(0.15)

            launch = get_active_launch()
            intelligence_config = {
                "analysis_objective": st.session_state.intel_analysis_objective,
                "output_depth": st.session_state.intel_output_depth,
                "maximum_insights": st.session_state.intel_max_insights,
                "minimum_evidence_records": st.session_state.intel_min_evidence_records,
                "segment_focus": st.session_state.intel_segment_focus,
                "confidence_policy": st.session_state.intel_confidence_policy,
                "require_counter_evidence": st.session_state.intel_require_counter_evidence,
                "require_guardrails": st.session_state.intel_require_guardrails,
            }
            governance_config = {
                "strictness": st.session_state.governance_strictness,
                "required_alignment": st.session_state.governance_required_alignment,
                "downgrade_overconfidence": st.session_state.governance_downgrade_overconfidence,
                "human_review_threshold": st.session_state.governance_human_review_threshold,
                "escalation_categories": st.session_state.governance_escalation_categories,
            }

            st.write("3. Running the Customer Intelligence Agent")
            if st.session_state.agent_mode == "Live (Gemini API)":
                report = generate_intelligence_report(
                    frame=frame,
                    product_name=launch["display_name"],
                    launch_goal=launch["launch_goal"],
                    target_market=launch["target_markets"],
                    configuration=intelligence_config,
                )
            else:
                report = _demo_intelligence_report()
            st.session_state.gemini_report = report
            time.sleep(0.15)

            st.write("4. Running the Governance Reviewer")
            if st.session_state.agent_mode == "Live (Gemini API)":
                review = review_intelligence_report(
                    frame=frame,
                    draft_report=report,
                    product_name=launch["display_name"],
                    launch_goal=launch["launch_goal"],
                    target_market=launch["target_markets"],
                    configuration=governance_config,
                )
            else:
                review = _demo_governance_review(report)
            st.session_state.governance_review = review

            run_time = datetime.now().astimezone()
            st.session_state.last_run_at = run_time.isoformat()
            st.session_state.pipeline_complete = True
            st.session_state.run_history.insert(
                0,
                {
                    "launch": launch["display_name"],
                    "timestamp": run_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "mode": st.session_state.agent_mode,
                    "signals": int(len(frame)),
                    "insights": int(len(report.insights)),
                    "verdict": review.overall_verdict,
                },
            )
            st.session_state.run_history = st.session_state.run_history[:10]
            status.update(label="Pipeline run complete", state="complete", expanded=False)

        except Exception as exc:
            st.session_state.pipeline_complete = False
            st.session_state.pipeline_error = str(exc)
            status.update(label="Pipeline run failed", state="error", expanded=True)
            st.error(str(exc))
        finally:
            st.session_state.pipeline_running = False
            st.session_state.pipeline_requested = False


# ---------------------------------------------------------------------------
# Sidebar and launch creation
# ---------------------------------------------------------------------------


def render_sidebar() -> None:
    with st.sidebar:
        render_sidebar_brand()

        launches = st.session_state.launches
        launch_ids = list(launches.keys())
        current_id = st.session_state.active_launch_id
        if current_id not in launch_ids:
            current_id = launch_ids[0]

        selected = st.selectbox(
            "Product launch",
            options=launch_ids,
            index=launch_ids.index(current_id),
            format_func=lambda launch_id: launches[launch_id]["display_name"],
            key="launch_selector",
        )
        _activate_launch(selected)

        if st.session_state.show_new_launch_form:
            if st.button(
                "← Back to launch",
                key="sidebar_back_to_launch",
                use_container_width=True,
            ):
                st.session_state.show_new_launch_form = False
                st.rerun()
        else:
            if st.button(
                "＋ Add new launch",
                key="sidebar_add_new_launch",
                use_container_width=True,
            ):
                st.session_state.show_new_launch_form = True
                st.rerun()

        st.divider()
        st.radio(
            "Agent mode",
            ["Demo (cached)", "Live (Gemini API)"],
            key="agent_mode",
            help=(
                "Demo mode runs the complete workflow using deterministic cached agents. "
                "Live mode calls Gemini twice: intelligence, then governance."
            ),
        )

        if st.session_state.agent_mode == "Live (Gemini API)" and not os.getenv(
            "GEMINI_API_KEY"
        ):
            st.warning("GEMINI_API_KEY is not configured. Use Demo mode or add the key.")

        st.divider()
        if st.button(
            "↻ Sync data & run full pipeline",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.pipeline_running,
        ):
            st.session_state.pipeline_requested = True

        if st.session_state.last_run_at:
            run_time = datetime.fromisoformat(st.session_state.last_run_at)
            st.caption(f"Last run: {run_time.strftime('%b %d, %Y · %I:%M %p')}")

        if st.session_state.connector_errors:
            with st.expander("Connector notes"):
                for error in st.session_state.connector_errors:
                    st.warning(error)

        st.divider()
        st.caption(
            "The sample customer records are synthetic and paraphrased from public themes. "
            "They demonstrate the workflow and are not a representative eBay research study."
        )


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or f"launch-{len(st.session_state.launches) + 1}"


def _generated_feedback(name: str, category: str, goal: str) -> list[str]:
    return [
        f"The value of {name} is clear, but I need a simpler explanation before I would try it.",
        f"This could save time for customers in {category}, especially when the current journey feels complicated.",
        f"I like the direction, but I want more control and a clear way to review the result before acting.",
        f"The launch goal makes sense, although pricing, eligibility, and support ownership need to be transparent.",
        f"I would trust the experience more if it showed why a recommendation was made and what evidence supported it.",
        f"The product seems useful, but the happy path and the failure path need equally clear guidance.",
        f"I would compare this with existing alternatives before changing my current workflow.",
        f"The strongest message is the customer outcome, not the technology behind it: {goal}.",
    ]


def render_new_launch_form() -> None:
    back_col, _ = st.columns([1.2, 5])
    with back_col:
        if st.button(
            "← Back to launch",
            key="page_back_to_launch",
            use_container_width=True,
        ):
            st.session_state.show_new_launch_form = False
            st.rerun()

    st.title("Set up a new launch")
    st.caption(
        "Create a launch configuration, add seed feedback, and run the same one-click intelligence and governance pipeline."
    )

    with st.form("new_launch_form"):
        auto_generate = st.checkbox(
            "Auto-generate a few sample feedback records",
            value=True,
        )

        st.markdown("### Launch details")
        name = st.text_input("Launch name", placeholder="e.g. eBay Restored Tech")
        tagline = st.text_input(
            "Tagline",
            placeholder="e.g. Certified refurbished electronics",
        )
        category = st.text_input(
            "Category",
            placeholder="e.g. Consumer Electronics · Refurbished",
        )
        launch_date = st.date_input("Launch date", value=date.today())

        left, right = st.columns(2)
        with left:
            target_markets = st.text_input(
                "Target markets (comma-separated)",
                placeholder="United States, Canada",
            )
        with right:
            expansion_markets = st.text_input(
                "Expansion markets (optional)",
                placeholder="United Kingdom",
            )

        competitors = st.text_input(
            "Competitors (comma-separated)",
            placeholder="Back Market, Amazon Renewed",
        )
        launch_goal = st.text_area(
            "Launch goal",
            placeholder="What business and customer outcome should this launch achieve?",
        )
        why_launch = st.text_area(
            "Why this launch",
            placeholder="What customer, market, or business problem makes this launch necessary?",
        )
        expected_outcomes = st.text_area(
            "Expected outcomes — one per line",
            placeholder="Increase qualified adoption\nReduce customer confusion\nImprove launch readiness",
        )
        success_metrics = st.text_area(
            "Success metrics — one per line",
            placeholder="Activation rate\nConversion\nSupport contact rate\nCustomer sentiment",
        )
        brand_voice = st.text_area(
            "Brand voice examples — one per line",
            placeholder="Built to make the complex feel simple.\nMore confidence at every step.",
        )
        seed_feedback = st.text_area(
            "Seed customer feedback — one record per line",
            placeholder="Add sample buyer, seller, support, or research feedback here.",
            height=170,
        )

        submitted = st.form_submit_button(
            "Create launch",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        if st.button("Cancel"):
            st.session_state.show_new_launch_form = False
            st.rerun()
        return

    if not name.strip() or not launch_goal.strip() or not why_launch.strip():
        st.error("Launch name, launch goal, and why this launch are required.")
        return

    launch_id = _slugify(name)
    suffix = 2
    original_id = launch_id
    while launch_id in st.session_state.launches:
        launch_id = f"{original_id}-{suffix}"
        suffix += 1

    feedback = [line.strip() for line in seed_feedback.splitlines() if line.strip()]
    if auto_generate and not feedback:
        feedback = _generated_feedback(name, category, launch_goal)

    st.session_state.launches[launch_id] = {
        "id": launch_id,
        "name": name.strip(),
        "display_name": name.strip(),
        "tagline": tagline.strip() or "Product Marketing launch intelligence",
        "category": category.strip() or "Unspecified category",
        "launch_date": launch_date.isoformat(),
        "target_markets": target_markets.strip() or "Unspecified",
        "expansion_markets": expansion_markets.strip(),
        "competitors": competitors.strip() or "Not configured",
        "launch_goal": launch_goal.strip(),
        "why_launch": why_launch.strip(),
        "expected_outcomes": [
            line.strip() for line in expected_outcomes.splitlines() if line.strip()
        ],
        "success_metrics": [
            line.strip() for line in success_metrics.splitlines() if line.strip()
        ],
        "supporting_insights": [
            "This launch uses user-provided configuration and sample feedback.",
            "Run the pipeline to identify evidence-supported themes and risks.",
        ],
        "brand_voice": [
            line.strip() for line in brand_voice.splitlines() if line.strip()
        ],
        "feedback": feedback,
        "sample_dataset": False,
    }
    st.session_state.active_launch_id = launch_id
    st.session_state.launch_selector = launch_id
    st.session_state.show_new_launch_form = False
    _reset_pipeline_results()
    _refresh_evidence()
    st.success("Launch created. It is now available in the sidebar dropdown.")
    st.rerun()


# ---------------------------------------------------------------------------
# Charts and dashboard rendering
# ---------------------------------------------------------------------------


def _style_figure(fig, *, height: int = 340) -> None:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=45, b=10),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color="#333333", size=12),
        title_font=dict(size=16, color="#191919"),
        legend_title_text="",
        hoverlabel=dict(bgcolor="#FFFFFF"),
    )


def _render_sentiment_chart(frame: pd.DataFrame) -> None:
    counts = (
        frame["sentiment"].value_counts().reindex(["Positive", "Neutral", "Negative"], fill_value=0)
    )
    chart = counts.rename_axis("sentiment").reset_index(name="signals")
    fig = px.pie(
        chart,
        names="sentiment",
        values="signals",
        hole=0.62,
        title="Customer sentiment",
        color="sentiment",
        color_discrete_map=SENTIMENT_COLORS,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    _style_figure(fig)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_theme_chart(summary: pd.DataFrame) -> None:
    chart = summary.head(7).sort_values("mentions")
    fig = px.bar(
        chart,
        x="mentions",
        y="theme",
        orientation="h",
        title="Top evidence themes",
        labels={"mentions": "Evidence records", "theme": ""},
        color="confidence",
        color_continuous_scale=["#DDE6FF", EBAY_COLORS["blue"]],
    )
    fig.update_coloraxes(showscale=False)
    _style_figure(fig)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_source_chart(frame: pd.DataFrame) -> None:
    chart = frame["source"].value_counts().reset_index()
    chart.columns = ["source", "signals"]
    fig = px.bar(
        chart,
        x="source",
        y="signals",
        title="Signal mix by source",
        labels={"source": "", "signals": "Signals"},
        color="source",
        color_discrete_sequence=[
            EBAY_COLORS["blue"],
            EBAY_COLORS["red"],
            EBAY_COLORS["yellow"],
            EBAY_COLORS["green"],
            "#8B5CF6",
            "#0EA5E9",
        ],
    )
    fig.update_layout(showlegend=False)
    fig.update_xaxes(tickangle=-18)
    _style_figure(fig)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_trend_chart(frame: pd.DataFrame) -> None:
    chart = frame.copy()
    chart["created_at"] = pd.to_datetime(chart["created_at"], errors="coerce")
    chart = chart.dropna(subset=["created_at"])
    if chart.empty:
        st.info("No usable dates are available for the trend chart.")
        return
    chart["month"] = chart["created_at"].dt.to_period("M").dt.to_timestamp()
    chart = (
        chart.groupby(["month", "sentiment"]).size().reset_index(name="signals")
    )
    fig = px.line(
        chart,
        x="month",
        y="signals",
        color="sentiment",
        markers=True,
        title="Feedback trend over time",
        labels={"month": "", "signals": "Signals", "sentiment": ""},
        color_discrete_map=SENTIMENT_COLORS,
    )
    _style_figure(fig)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_confidence_chart(report: IntelligenceReport) -> None:
    counts = Counter(insight.confidence_level for insight in report.insights)
    chart = pd.DataFrame(
        {
            "confidence": ["high", "medium", "low"],
            "insights": [counts.get("high", 0), counts.get("medium", 0), counts.get("low", 0)],
        }
    )
    fig = px.bar(
        chart,
        x="confidence",
        y="insights",
        title="Intelligence confidence",
        color="confidence",
        color_discrete_map=CONFIDENCE_COLORS,
    )
    fig.update_layout(showlegend=False)
    _style_figure(fig, height=310)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_governance_chart(review: GovernanceReview) -> None:
    counts = Counter(item.verdict for item in review.insight_reviews)
    chart = pd.DataFrame(
        {
            "verdict": ["approve", "revise", "reject"],
            "insights": [counts.get("approve", 0), counts.get("revise", 0), counts.get("reject", 0)],
        }
    )
    fig = px.pie(
        chart,
        names="verdict",
        values="insights",
        hole=0.6,
        title="Governance outcomes",
        color="verdict",
        color_discrete_map=VERDICT_COLORS,
    )
    fig.update_traces(textinfo="value+label")
    _style_figure(fig, height=310)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_launch_meta(launch: dict[str, Any]) -> None:
    values = [
        ("Category", launch["category"]),
        ("Launch date", launch["launch_date"]),
        ("Target market", launch["target_markets"]),
        ("Competitors tracked", launch["competitors"]),
    ]
    # Keep the generated HTML compact. Indented nested HTML can be interpreted
    # by Markdown as a code block instead of rendered content.
    cards = "".join(
        '<div class="launch-meta-card">'
        f'<div class="meta-label">{html.escape(label)}</div>'
        f'<div class="meta-value">{html.escape(str(value))}</div>'
        "</div>"
        for label, value in values
    )
    st.markdown(
        f'<div class="launch-meta-grid">{cards}</div>',
        unsafe_allow_html=True,
    )


def _pipeline_html() -> str:
    complete = st.session_state.pipeline_complete
    steps = [
        "Collect and normalize signals",
        "Detect themes and build evidence",
        "Customer Intelligence Agent",
        "Governance Reviewer",
        "PMM decision dashboard",
    ]
    rows: list[str] = []
    for index, label in enumerate(steps, start=1):
        state_class = "done" if complete else ""
        marker = "✓" if complete else str(index)
        rows.append(
            f'<div class="pipeline-step {state_class}">'
            f'<span class="pipeline-step-number">{marker}</span>'
            f'<span>{html.escape(label)}</span>'
            "</div>"
        )
    return (
        '<div class="pipeline-card"><h3>One-click pipeline</h3>'
        + "".join(rows)
        + "</div>"
    )


def _top_theme_for_sentiment(frame: pd.DataFrame, sentiment: str) -> str:
    if frame.empty or "theme" not in frame.columns:
        return "No clear theme yet"
    subset = frame.loc[
        (frame["sentiment"] == sentiment)
        & (frame["theme"].fillna("") != "Unclassified"),
        "theme",
    ]
    if subset.empty:
        return "No clear theme yet"
    return str(subset.value_counts().index[0])


def _render_overview_metrics(frame: pd.DataFrame) -> None:
    total = len(frame)
    positive = int((frame["sentiment"] == "Positive").sum()) if total else 0
    negative = int((frame["sentiment"] == "Negative").sum()) if total else 0
    positive_share = round(100 * positive / total) if total else 0
    negative_share = round(100 * negative / total) if total else 0
    source_count = int(frame["source"].nunique()) if total else 0

    positive_theme = _top_theme_for_sentiment(frame, "Positive")
    negative_theme = _top_theme_for_sentiment(frame, "Negative")
    pipeline_value = "Complete" if st.session_state.pipeline_complete else "Ready"
    pipeline_description = (
        "The latest one-click run finished. Intelligence and governance results are ready."
        if st.session_state.pipeline_complete
        else "One click will run evidence preparation, intelligence, and governance review."
    )

    cards = [
        (
            "Signals",
            str(total),
            f"Evidence records collected from {source_count} active source{'s' if source_count != 1 else ''}.",
            "blue",
        ),
        (
            "Positive",
            f"{positive_share}%",
            f"Signals expressing clear value or satisfaction. Strongest theme: {positive_theme}.",
            "green",
        ),
        (
            "Negative",
            f"{negative_share}%",
            f"Signals showing friction or concern. Strongest theme: {negative_theme}.",
            "red",
        ),
        (
            "Pipeline",
            pipeline_value,
            pipeline_description,
            "yellow",
        ),
    ]

    columns = st.columns(4)
    for column, (label, value, description, accent) in zip(columns, cards):
        with column:
            st.markdown(
                f'<div class="metric-card {accent}">'
                f'<div class="metric-card-label">{html.escape(label)}</div>'
                f'<div class="metric-card-value">{html.escape(value)}</div>'
                f'<div class="metric-card-description">{html.escape(description)}</div>'
                "</div>",
                unsafe_allow_html=True,
            )


def _segment_group(raw_segment: str) -> str:
    value = raw_segment.strip().lower()
    if "seller" in value:
        return "Professional sellers"
    if any(token in value for token in ("high-ticket", "collector")):
        return "High-consideration buyers"
    if any(token in value for token in ("value-focused", "refurbished")):
        return "Value-conscious buyers"
    if any(token in value for token in ("first-time", "occasional")):
        return "New and occasional BNPL users"
    if any(
        token in value
        for token in ("returning", "repeat", "mobile", "multi-item", "cross-border", "buyer")
    ):
        return "Active marketplace buyers"
    if not value or value in {"unspecified", "organizational learning"}:
        return "General launch audience"
    return raw_segment.strip().title()


SEGMENT_NEEDS = {
    "Professional sellers": "Clear payout, shipping, and support ownership.",
    "High-consideration buyers": "Payment flexibility without weakening trust in the purchase.",
    "Value-conscious buyers": "Upfront eligibility and total-cost clarity.",
    "New and occasional BNPL users": "Simple education before the final checkout step.",
    "Active marketplace buyers": "A smooth checkout, payment-management, and refund journey.",
    "General launch audience": "Clear value, eligibility, and support information.",
}


def _build_segment_profiles(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()

    customer_frame = frame.loc[
        frame["source_type"].astype(str) != "organizational_knowledge"
    ].copy()
    customer_frame = customer_frame.loc[
        customer_frame["segment"].astype(str).str.lower() != "organizational learning"
    ]
    if customer_frame.empty:
        return pd.DataFrame()

    customer_frame["segment_group"] = customer_frame["segment"].map(_segment_group)
    profiles: list[dict[str, Any]] = []

    for segment_name, segment_rows in customer_frame.groupby("segment_group"):
        evidence_count = int(len(segment_rows))
        positive_count = int((segment_rows["sentiment"] == "Positive").sum())
        negative_count = int((segment_rows["sentiment"] == "Negative").sum())
        positive_share = round(100 * positive_count / evidence_count) if evidence_count else 0
        negative_share = round(100 * negative_count / evidence_count) if evidence_count else 0
        classified_themes = segment_rows.loc[
            segment_rows["theme"].fillna("") != "Unclassified",
            "theme",
        ]
        top_theme = (
            str(classified_themes.value_counts().index[0])
            if not classified_themes.empty
            else "Needs more evidence"
        )
        profiles.append(
            {
                "segment": str(segment_name),
                "evidence": evidence_count,
                "positive_share": positive_share,
                "negative_share": negative_share,
                "top_theme": top_theme,
                "pmm_need": SEGMENT_NEEDS.get(
                    str(segment_name),
                    "Validate needs and message fit with more segment-specific research.",
                ),
            }
        )

    return pd.DataFrame(profiles).sort_values(
        ["evidence", "segment"],
        ascending=[False, True],
    )


def _render_segmentation_layer(frame: pd.DataFrame) -> None:
    profiles = _build_segment_profiles(frame)
    st.markdown(
        '<div class="section-title">User segmentation layer</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Evidence-derived, directional segments for PMM planning. These are not statistically validated market segments."
    )

    if profiles.empty:
        st.info("No customer segment information is available in the selected evidence.")
        return

    chart_column, profile_column = st.columns([1, 1.55])
    with chart_column:
        fig = px.bar(
            profiles.sort_values("evidence"),
            x="evidence",
            y="segment",
            orientation="h",
            title="Evidence by user segment",
            labels={"evidence": "Evidence records", "segment": ""},
        )
        fig.update_traces(marker_color=EBAY_COLORS["blue"])
        _style_figure(fig, height=360)
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with profile_column:
        cards = "".join(
            '<div class="segment-card">'
            f'<div class="segment-card-title">{html.escape(str(row.segment))}</div>'
            f'<div class="segment-card-meta">{int(row.evidence)} evidence records · '
            f'{int(row.positive_share)}% positive · {int(row.negative_share)}% negative</div>'
            f'<div class="segment-card-theme"><strong>Main theme:</strong> {html.escape(str(row.top_theme))}</div>'
            f'<div class="segment-card-need"><strong>PMM need:</strong> {html.escape(str(row.pmm_need))}</div>'
            "</div>"
            for row in profiles.itertuples(index=False)
        )
        st.markdown(
            f'<div class="segment-card-grid">{cards}</div>',
            unsafe_allow_html=True,
        )


def render_overview_tab() -> None:
    launch = get_active_launch()
    raw_frame = st.session_state.evidence_frame
    frame = _frame_with_analysis(raw_frame)
    summary = st.session_state.baseline_summary

    _render_launch_meta(launch)

    _render_overview_metrics(frame)

    st.markdown('<div class="section-title">Why this launch</div>', unsafe_allow_html=True)
    narrative, pipeline = st.columns([2.2, 1])
    with narrative:
        st.markdown(
            f'<div class="soft-card"><p>{html.escape(launch["why_launch"])}</p></div>',
            unsafe_allow_html=True,
        )
    with pipeline:
        st.markdown(_pipeline_html(), unsafe_allow_html=True)

    st.markdown('<div class="section-title">Launch outcomes</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        outcome_items = "".join(
            f"<li>{html.escape(item)}</li>" for item in launch.get("expected_outcomes", [])
        )
        st.markdown(
            f'<div class="soft-card"><h3>Expected outcomes</h3><ul>{outcome_items}</ul></div>',
            unsafe_allow_html=True,
        )
    with right:
        insight_items = "".join(
            f"<li>{html.escape(item)}</li>" for item in launch.get("supporting_insights", [])
        )
        st.markdown(
            f'<div class="soft-card"><h3>Supporting insights going in</h3><ul>{insight_items}</ul></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-title">Signal dashboard</div>', unsafe_allow_html=True)
    st.caption(
        "Sentiment is directional. Sample customer records are synthetic and based on public discussion themes, not a representative research sample."
    )
    chart_left, chart_right = st.columns(2)
    with chart_left:
        _render_sentiment_chart(frame)
    with chart_right:
        _render_theme_chart(summary)

    chart_left, chart_right = st.columns(2)
    with chart_left:
        _render_source_chart(frame)
    with chart_right:
        _render_trend_chart(frame)

    if st.session_state.pipeline_complete:
        report = st.session_state.gemini_report
        review = st.session_state.governance_review
        chart_left, chart_right = st.columns(2)
        with chart_left:
            _render_confidence_chart(report)
        with chart_right:
            _render_governance_chart(review)

    st.markdown('<div class="section-title">Success measures</div>', unsafe_allow_html=True)
    metric_columns = st.columns(3)
    for index, metric in enumerate(launch.get("success_metrics", [])):
        with metric_columns[index % 3]:
            st.markdown(
                f'<div class="soft-card"><div class="meta-label">Measure {index + 1}</div><div class="meta-value">{html.escape(metric)}</div></div>',
                unsafe_allow_html=True,
            )

    if st.session_state.run_history:
        with st.expander(f"Run history ({len(st.session_state.run_history)})"):
            st.dataframe(pd.DataFrame(st.session_state.run_history), use_container_width=True, hide_index=True)


def render_signal_hub_tab() -> None:
    st.markdown('<div class="section-title">Signal Hub</div>', unsafe_allow_html=True)
    st.caption(
        "Choose the evidence sources used by the one-click pipeline. NewsAPI and Reddit have been removed; Airtable is available as the enterprise signal source."
    )

    source_cols = st.columns(3)
    with source_cols[0]:
        st.checkbox("Buyer feedback samples", key="use_reviews")
        st.checkbox("Customer interviews", key="use_interviews")
    with source_cols[1]:
        st.checkbox("Support tickets", key="use_support")
        st.checkbox("Past launch knowledge", key="use_past_launches")
    with source_cols[2]:
        st.checkbox("Airtable", key="use_airtable")
        st.checkbox("CPSC recalls", key="use_cpsc")

    if st.session_state.use_airtable:
        with st.expander("Airtable connection", expanded=True):
            st.info(
                "Store AIRTABLE_PAT in .env or Streamlit secrets. The token is never shown in the UI."
            )
            left, right = st.columns(2)
            with left:
                st.text_input("Base ID", key="airtable_base_id")
                st.text_input("Table name", key="airtable_table_name")
                st.text_input("View (optional)", key="airtable_view")
                st.text_input("Feedback text field", key="airtable_text_field")
            with right:
                st.text_input("Rating field", key="airtable_rating_field")
                st.text_input("Date field", key="airtable_date_field")
                st.text_input("Segment field", key="airtable_segment_field")
                st.text_input("Source type field", key="airtable_source_type_field")

    if st.session_state.use_cpsc:
        st.text_input("CPSC product query", key="cpsc_query")

    if st.button("Refresh signal preview"):
        _reset_pipeline_results()
        _refresh_evidence()
        st.success("Signal preview refreshed. Run the full pipeline to regenerate agent results.")

    frame = _frame_with_analysis(st.session_state.evidence_frame)
    source_counts = frame["source"].value_counts().reset_index()
    source_counts.columns = ["Source", "Signals"]
    st.dataframe(source_counts, use_container_width=True, hide_index=True)

    st.markdown(
        """
        <div class="source-note">
            <strong>Evidence policy:</strong> Customer feedback, interviews, and support tickets may represent Voice of Customer. Past launch knowledge is organizational evidence. CPSC records are safety and regulatory intelligence. Airtable records keep the source type supplied in the table. The agents must not mix these evidence types.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_intelligence_tab() -> None:
    report = st.session_state.gemini_report
    frame = st.session_state.evidence_frame
    analyzed_frame = _frame_with_analysis(frame)

    st.markdown('<div class="section-title">Customer Intelligence</div>', unsafe_allow_html=True)
    if report is None:
        st.info("Run the full pipeline once. The Intelligence Agent and Governance Reviewer will run automatically.")
        return

    st.markdown(
        f'<div class="soft-card"><h3>Executive summary</h3><p>{html.escape(report.executive_summary)}</p></div>',
        unsafe_allow_html=True,
    )

    _render_segmentation_layer(analyzed_frame)

    st.markdown(
        '<div class="section-title">Strategic insights</div>',
        unsafe_allow_html=True,
    )
    for index, insight in enumerate(report.insights, start=1):
        confidence_class = {
            "high": "green",
            "medium": "yellow",
            "low": "red",
        }.get(insight.confidence_level, "")
        st.markdown(
            f"""
            <div class="insight-card">
                <span class="status-pill">Insight {index}</span>
                <span class="status-pill {confidence_class}">{html.escape(insight.confidence_level.title())} confidence</span>
                <h3>{html.escape(insight.title)}</h3>
                <p><strong>Customer problem:</strong> {html.escape(insight.customer_problem)}</p>
                <p><strong>PMM implication:</strong> {html.escape(insight.pmm_implication)}</p>
                <p><strong>Recommendation:</strong> {html.escape(insight.recommendation)}</p>
                <p><strong>Next action:</strong> {html.escape(insight.next_action)}</p>
                <p><strong>Guardrail:</strong> {html.escape(insight.guardrail)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("Evidence, segments, and uncertainty"):
            st.write("**Affected segments:** " + ", ".join(insight.affected_segments))
            st.write("**Evidence synthesis:** " + insight.evidence_summary)
            st.write("**Counter-evidence or uncertainty:** " + insight.counter_evidence_or_uncertainty)
            st.write("**Confidence rationale:** " + insight.confidence_rationale)
            valid_ids = [row_id for row_id in insight.evidence_row_ids if row_id in frame.index]
            if valid_ids:
                st.dataframe(
                    frame.loc[
                        valid_ids,
                        ["source", "source_type", "created_at", "rating", "text", "url"],
                    ],
                    use_container_width=True,
                )

    with st.expander("Missing evidence and recommended research"):
        st.markdown("**Missing evidence**")
        for item in report.missing_evidence:
            st.write(f"- {item}")
        st.markdown("**Research questions**")
        for item in report.recommended_research_questions:
            st.write(f"- {item}")


def render_governance_tab() -> None:
    review = st.session_state.governance_review
    st.markdown('<div class="section-title">Governance Review</div>', unsafe_allow_html=True)
    if review is None:
        st.info("Run the full pipeline once. Governance runs automatically after intelligence generation.")
        return

    verdict_label = review.overall_verdict.replace("_", " ").title()
    st.markdown(
        f'<div class="soft-card"><span class="status-pill">{html.escape(verdict_label)}</span><h3>Executive assessment</h3><p>{html.escape(review.executive_assessment)}</p></div>',
        unsafe_allow_html=True,
    )

    for item in review.insight_reviews:
        st.markdown(
            f"""
            <div class="governance-card {item.verdict}">
                <span class="status-pill">{html.escape(item.verdict.title())}</span>
                <span class="status-pill">{html.escape(item.evidence_alignment.title())} alignment</span>
                <h3>{html.escape(item.insight_title)}</h3>
                <p>{html.escape(item.reviewer_rationale)}</p>
                <p><strong>Revised recommendation:</strong> {html.escape(item.revised_recommendation)}</p>
                <p><strong>Human review:</strong> {'Required' if item.human_review_required else 'Not required'}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if item.issues:
            with st.expander(f"Review issues · {item.insight_title}"):
                for issue in item.issues:
                    st.write(
                        f"**{issue.severity.title()} · {issue.category.replace('_', ' ').title()}** — {issue.explanation}"
                    )

    left, right = st.columns(2)
    with left:
        st.markdown("### Cross-cutting risks")
        for risk in review.cross_cutting_risks:
            st.write(f"- {risk}")
    with right:
        st.markdown("### Required human escalations")
        for escalation in review.required_human_escalations:
            st.write(f"- {escalation}")

    st.info(review.audit_summary)


def render_evidence_tab() -> None:
    frame = _frame_with_analysis(st.session_state.evidence_frame)
    st.markdown('<div class="section-title">Evidence & Audit</div>', unsafe_allow_html=True)
    st.caption("Every recommendation can be traced back to the normalized signal records used by the agents.")

    if frame.empty:
        st.warning("No evidence is available.")
        return

    source_types = frame["source_type"].nunique()
    source_count = frame["source"].nunique()
    duplicates_removed = 0
    cols = st.columns(4)
    cols[0].metric("Normalized records", len(frame))
    cols[1].metric("Sources", source_count)
    cols[2].metric("Source types", source_types)
    cols[3].metric("Duplicate fingerprints", duplicates_removed)

    display_columns = [
        "source",
        "source_type",
        "created_at",
        "rating",
        "sentiment",
        "segment",
        "theme",
        "text",
        "url",
        "fingerprint",
    ]
    st.dataframe(frame[display_columns], use_container_width=True, hide_index=False)

    st.markdown(
        """
        <div class="source-note">
            <strong>Data note:</strong> The Klarna customer feedback, interview, and support records are synthetic paraphrases inspired by recurring public themes. Official eBay pages are used only for product and launch facts. The app does not present the synthetic records as verbatim customer quotes or as a representative sentiment study.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_agent_configuration_tab() -> None:
    st.markdown('<div class="section-title">Agent Configuration</div>', unsafe_allow_html=True)
    st.caption("PMMs control business behavior through structured fields. They do not edit raw system prompts.")

    intelligence_tab, governance_tab, runtime_tab, prompt_tab = st.tabs(
        [
            "Customer Intelligence",
            "Governance Reviewer",
            "Scale & Runtime",
            "Prompt Operations",
        ]
    )

    with intelligence_tab:
        with st.form("intelligence_config_dashboard"):
            left, right = st.columns(2)
            with left:
                st.selectbox(
                    "Analysis objective",
                    [
                        "Launch adoption and readiness",
                        "Customer problem discovery",
                        "Positioning and messaging",
                        "Audience and segmentation",
                        "Post-launch optimization",
                    ],
                    key="intel_analysis_objective",
                )
                st.selectbox(
                    "Output depth",
                    ["Executive", "Balanced", "Deep dive"],
                    key="intel_output_depth",
                )
                st.slider(
                    "Target strategic insights",
                    2,
                    6,
                    key="intel_max_insights",
                )
                st.number_input(
                    "Minimum supporting evidence records",
                    1,
                    10,
                    step=1,
                    key="intel_min_evidence_records",
                )
            with right:
                st.selectbox(
                    "Segment focus",
                    [
                        "All evidence-supported segments",
                        "Buyers",
                        "Sellers",
                        "New users",
                        "Power users",
                    ],
                    key="intel_segment_focus",
                )
                st.selectbox(
                    "Confidence policy",
                    ["Conservative", "Balanced", "Exploratory"],
                    key="intel_confidence_policy",
                )
                st.checkbox(
                    "Require counter-evidence or uncertainty",
                    key="intel_require_counter_evidence",
                )
                st.checkbox(
                    "Require a guardrail for every recommendation",
                    key="intel_require_guardrails",
                )
            saved = st.form_submit_button("Save Intelligence configuration", type="primary")
        if saved:
            _reset_pipeline_results()
            st.success("Saved. Run the full pipeline to apply the configuration.")

    with governance_tab:
        with st.form("governance_config_dashboard"):
            left, right = st.columns(2)
            with left:
                st.selectbox(
                    "Review strictness",
                    ["Standard", "High", "Maximum"],
                    key="governance_strictness",
                )
                st.selectbox(
                    "Required evidence alignment",
                    ["Partial", "Strong"],
                    key="governance_required_alignment",
                )
                st.checkbox(
                    "Downgrade confidence when evidence is narrow",
                    key="governance_downgrade_overconfidence",
                )
            with right:
                st.selectbox(
                    "Human-review threshold",
                    [
                        "Critical issues only",
                        "High-risk or unsupported claims",
                        "Any material revision",
                    ],
                    key="governance_human_review_threshold",
                )
                st.multiselect(
                    "Escalation categories",
                    [
                        "PMM",
                        "Product",
                        "Research",
                        "Legal",
                        "Trust & Safety",
                        "Privacy",
                        "Brand",
                        "Compliance",
                    ],
                    key="governance_escalation_categories",
                )
            saved = st.form_submit_button("Save Governance configuration", type="primary")
        if saved:
            _reset_pipeline_results()
            st.success("Saved. Run the full pipeline to apply the configuration.")

    with runtime_tab:
        st.warning(
            "This is the intended production policy. The current prototype uses a small bounded evidence packet rather than production-scale RAG."
        )
        with st.form("runtime_config_dashboard"):
            st.selectbox(
                "Preprocessing policy",
                [
                    "Rules + lightweight ML",
                    "Lightweight ML only",
                    "LLM-first — not recommended at scale",
                ],
                key="runtime_preprocessing_policy",
            )
            st.multiselect(
                "Evidence-bucket dimensions",
                [
                    "Sentiment",
                    "Topic",
                    "Segment",
                    "Region",
                    "Product version",
                    "Recency",
                    "Severity",
                    "Journey stage",
                ],
                key="runtime_bucket_dimensions",
            )
            st.selectbox(
                "Retrieval architecture",
                [
                    "RAG over evidence buckets and representative records",
                    "Direct bounded context — current MVP",
                ],
                key="runtime_retrieval_policy",
            )
            st.selectbox(
                "Model routing",
                [
                    "Low-cost tagging models; reasoning model for synthesis",
                    "Single model for every task",
                ],
                key="runtime_model_routing",
            )
            st.selectbox(
                "Optimization priority",
                [
                    "Balanced quality, latency, and cost",
                    "Maximum quality",
                    "Lowest cost",
                    "Lowest latency",
                ],
                key="runtime_optimization_priority",
            )
            st.form_submit_button("Save Runtime policy", type="primary")

    with prompt_tab:
        st.info(
            "Current MVP: prompt contracts are defined in Python. Production target: externally stored, versioned templates with evaluation and rollback."
        )
        left, right = st.columns(2)
        with left:
            st.markdown(
                """
                <div class="soft-card">
                    <h3>Customer Intelligence prompt</h3>
                    <p><strong>Prompt ID:</strong> intelligence-agent</p>
                    <p><strong>Active version:</strong> v1.2</p>
                    <p><strong>Owner:</strong> PMM Capabilities</p>
                    <p><strong>Regression suite:</strong> Evidence citation, confidence, uncertainty, guardrails</p>
                    <p><strong>Rollback:</strong> v1.1</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with right:
            st.markdown(
                """
                <div class="soft-card">
                    <h3>Governance Reviewer prompt</h3>
                    <p><strong>Prompt ID:</strong> governance-reviewer</p>
                    <p><strong>Active version:</strong> v1.1</p>
                    <p><strong>Owner:</strong> AI Governance / PMM Capabilities</p>
                    <p><strong>Regression suite:</strong> Unsupported claims, source misuse, confidence, escalation</p>
                    <p><strong>Rollback:</strong> v1.0</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("### Govern prompts like product releases")
        st.write("Draft → Evaluate → Compare → Approve → Deploy → Monitor → Roll back")


def render_dashboard() -> None:
    launch = get_active_launch()
    render_pipeline_banner(st.session_state.pipeline_complete)
    render_launch_header(launch["display_name"], launch["tagline"])

    if st.session_state.pipeline_error:
        st.error(st.session_state.pipeline_error)

    overview, signals, intelligence, governance, evidence, configuration = st.tabs(
        [
            "Overview",
            "Signal Hub",
            "Intelligence",
            "Governance",
            "Evidence & Audit",
            "Agent Configuration",
        ]
    )

    with overview:
        render_overview_tab()
    with signals:
        render_signal_hub_tab()
    with intelligence:
        render_intelligence_tab()
    with governance:
        render_governance_tab()
    with evidence:
        render_evidence_tab()
    with configuration:
        render_agent_configuration_tab()
