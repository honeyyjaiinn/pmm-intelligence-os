from __future__ import annotations

import os
from typing import Literal

import pandas as pd
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from .gemini_insights import (
    IntelligenceReport,
    build_evidence_packet,
)


class ReviewIssue(BaseModel):
    """
    One specific quality, evidence, or governance issue.
    """

    category: Literal[
        "unsupported_claim",
        "weak_evidence",
        "source_misclassification",
        "ignored_counter_evidence",
        "overconfidence",
        "product_vs_messaging",
        "safety_or_legal",
        "segment_overreach",
        "missing_context",
        "other",
    ] = Field(
        description="The category of the problem identified."
    )

    severity: Literal[
        "low",
        "medium",
        "high",
        "critical",
    ] = Field(
        description="The severity of the issue."
    )

    explanation: str = Field(
        description=(
            "A concise explanation of the issue and why it matters."
        )
    )

    affected_row_ids: list[int] = Field(
        description=(
            "Evidence ROW IDs connected to the issue. "
            "Use an empty list when no specific row applies."
        )
    )


class InsightReview(BaseModel):
    """
    Governance review for one draft strategic insight.
    """

    insight_title: str = Field(
        description=(
            "The exact title of the draft insight being reviewed."
        )
    )

    verdict: Literal[
        "approve",
        "revise",
        "reject",
    ] = Field(
        description=(
            "Approve when the insight is well supported; revise when "
            "the direction is useful but wording, confidence, or action "
            "requires correction; reject when it lacks evidence or is "
            "materially misleading."
        )
    )

    evidence_alignment: Literal[
        "strong",
        "partial",
        "weak",
    ] = Field(
        description=(
            "How strongly the original evidence supports the insight."
        )
    )

    cited_row_ids: list[int] = Field(
        description=(
            "All evidence ROW IDs considered during the review."
        )
    )

    valid_supporting_row_ids: list[int] = Field(
        description=(
            "Evidence ROW IDs that genuinely support the insight."
        )
    )

    unsupported_or_misused_row_ids: list[int] = Field(
        description=(
            "Rows that were cited incorrectly, overinterpreted, "
            "or used as the wrong evidence type."
        )
    )

    issues: list[ReviewIssue] = Field(
        description=(
            "Specific evidence, logic, confidence, or governance issues."
        )
    )

    reviewer_rationale: str = Field(
        description=(
            "The reasoning behind the approve, revise, or reject verdict."
        )
    )

    revised_customer_problem: str = Field(
        description=(
            "A corrected customer-problem statement. Preserve the "
            "original when no revision is needed."
        )
    )

    revised_pmm_implication: str = Field(
        description=(
            "A corrected Product Marketing implication."
        )
    )

    revised_recommendation: str = Field(
        description=(
            "A corrected and evidence-bounded PMM recommendation."
        )
    )

    revised_next_action: str = Field(
        description=(
            "A specific, practical, evidence-appropriate next action."
        )
    )

    revised_guardrail: str = Field(
        description=(
            "The guardrail required before acting on the recommendation."
        )
    )

    revised_confidence_level: Literal[
        "low",
        "medium",
        "high",
    ] = Field(
        description=(
            "The reviewer-adjusted qualitative confidence level."
        )
    )

    human_review_required: bool = Field(
        description=(
            "Whether the recommendation requires explicit human approval "
            "or escalation before use."
        )
    )


class GovernanceReview(BaseModel):
    """
    Complete audit of a Gemini Customer Intelligence report.
    """

    overall_verdict: Literal[
        "approve",
        "approve_with_revisions",
        "reject",
    ] = Field(
        description="Overall decision on the draft intelligence report."
    )

    executive_assessment: str = Field(
        description=(
            "A concise assessment of the report's quality, usefulness, "
            "and major limitations."
        )
    )

    insight_reviews: list[InsightReview] = Field(
        description=(
            "One review for every insight in the original report."
        )
    )

    cross_cutting_risks: list[str] = Field(
        description=(
            "Problems affecting multiple insights, such as weak sample "
            "quality, source bias, or unsupported segment conclusions."
        )
    )

    required_human_escalations: list[str] = Field(
        description=(
            "Items that should be reviewed by PMM, Product, Research, "
            "Legal, Trust, Safety, or another responsible team."
        )
    )

    audit_summary: str = Field(
        description=(
            "A concise record of what was approved, revised, or rejected."
        )
    )


REVIEWER_INSTRUCTIONS = """
You are a skeptical enterprise AI Reviewer and Product Marketing
Governance specialist.

You are reviewing a draft Customer Intelligence report created by another
AI component.

Your responsibility is not to make the draft sound better. Your
responsibility is to determine whether each recommendation is supported,
appropriately scoped, and safe to use.

Follow these rules:

1. Use only the supplied evidence and draft report.
2. Review every draft insight exactly once.
3. Preserve each original insight title in insight_title.
4. Approve only when evidence directly supports the customer problem,
   implication, and recommendation.
5. Revise when the strategic direction is useful but the wording,
   confidence, segment claim, implication, or action overstates the evidence.
6. Reject insights that are fabricated, materially misleading, unsupported,
   or based on the wrong evidence type.
7. Do not reward polished or persuasive language.
8. Check every evidence ROW ID against the original evidence.
9. Customer reviews, interviews, support tickets, surveys, and community
   discussions may represent Voice of Customer.
10. Competitive news is market intelligence, not direct customer evidence.
11. CPSC recall data is regulatory and safety intelligence, not direct
    customer sentiment.
12. Past launch learnings are organizational knowledge, not current
    customer evidence.
13. Do not allow one source to be described as cross-source validation.
14. Identify self-selection, sample-size, recency, and representativeness
    limitations.
15. A product defect, crash, broken workflow, trust failure, or safety issue
    must not be reframed only as a messaging opportunity.
16. Revenue, performance, safety, adoption, or market claims require
    explicit evidence and may require human approval.
17. Lower confidence when evidence is narrow, contradictory, synthetic,
    outdated, or poorly segmented.
18. Human escalation is required for legal, safety, trust, compliance,
    sensitive segmentation, or unsupported business claims.
19. Revised recommendations must stay within the supplied evidence.
20. Do not invent new data, percentages, quotations, product capabilities,
    customer segments, or outcomes.
"""


def review_intelligence_report(
    frame: pd.DataFrame,
    draft_report: IntelligenceReport,
    product_name: str,
    launch_goal: str,
    target_market: str,
) -> GovernanceReview:
    """
    Independently audit a draft Customer Intelligence report against
    the normalized evidence used to create it.
    """
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing from the .env file."
        )

    model = os.getenv(
        "GEMINI_REVIEW_MODEL",
        os.getenv(
            "GEMINI_MODEL",
            "gemini-3.1-flash-lite",
        ),
    )

    evidence_packet = build_evidence_packet(frame)

    draft_json = draft_report.model_dump_json(
        indent=2
    )

    prompt = f"""
{REVIEWER_INSTRUCTIONS}

PRODUCT MARKETING CONTEXT

Product:
{product_name}

Launch goal:
{launch_goal}

Target market:
{target_market}

ORIGINAL NORMALIZED EVIDENCE

{evidence_packet}

DRAFT CUSTOMER INTELLIGENCE REPORT

{draft_json}

REVIEW TASK

Audit the complete draft report against the original evidence.

For every draft insight:

- verify whether the cited ROW IDs genuinely support it;
- identify any misclassified evidence source;
- check whether counter-evidence was ignored;
- determine whether confidence is appropriate;
- approve, revise, or reject the insight;
- provide corrected wording and actions;
- indicate whether human review is required.

Do not create additional strategic insights that were not present in the
draft. Produce exactly one InsightReview for each draft insight.
"""

    with genai.Client(api_key=api_key) as client:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GovernanceReview,
                temperature=0.1,
            ),
        )

    if not response.text:
        raise RuntimeError(
            "Gemini reviewer returned an empty response."
        )

    review = GovernanceReview.model_validate_json(
        response.text
    )

    expected_titles = sorted(
        insight.title
        for insight in draft_report.insights
    )

    reviewed_titles = sorted(
        item.insight_title
        for item in review.insight_reviews
    )

    if reviewed_titles != expected_titles:
        raise RuntimeError(
            "The reviewer did not review every draft insight exactly once. "
            f"Expected titles: {expected_titles}. "
            f"Reviewed titles: {reviewed_titles}."
        )

    valid_row_ids = set(frame.index.tolist())

    for item in review.insight_reviews:
        returned_row_ids = (
            item.cited_row_ids
            + item.valid_supporting_row_ids
            + item.unsupported_or_misused_row_ids
        )

        for issue in item.issues:
            returned_row_ids.extend(
                issue.affected_row_ids
            )

        invalid_row_ids = sorted(
            {
                row_id
                for row_id in returned_row_ids
                if row_id not in valid_row_ids
            }
        )

        if invalid_row_ids:
            raise RuntimeError(
                "The reviewer returned invalid evidence ROW IDs "
                f"for '{item.insight_title}': "
                f"{invalid_row_ids}"
            )

    return review
