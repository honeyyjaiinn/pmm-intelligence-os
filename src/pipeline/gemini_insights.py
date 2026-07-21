from __future__ import annotations

import os
from typing import Literal

import pandas as pd
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


class StrategicInsight(BaseModel):
    """
    One evidence-backed Product Marketing insight.
    """

    title: str = Field(
        description="A concise strategic title for the insight."
    )

    customer_problem: str = Field(
        description=(
            "The underlying customer problem supported by the evidence."
        )
    )

    affected_segments: list[str] = Field(
        description=(
            "Customer segments affected by this problem. "
            "Use only segments supported by the evidence."
        )
    )

    evidence_summary: str = Field(
        description=(
            "A concise synthesis of the records supporting the insight."
        )
    )

    evidence_row_ids: list[int] = Field(
        description=(
            "The exact ROW IDs from the supplied evidence packet that "
            "support this insight."
        )
    )

    source_types: list[str] = Field(
        description=(
            "The source types represented in the supporting evidence."
        )
    )

    counter_evidence_or_uncertainty: str = Field(
        description=(
            "Any disagreement, uncertainty, limitation, or counter-evidence."
        )
    )

    pmm_implication: str = Field(
        description=(
            "What this evidence means for segmentation, positioning, "
            "messaging, launch readiness, or GTM strategy."
        )
    )

    recommendation: str = Field(
        description="The recommended Product Marketing decision."
    )

    next_action: str = Field(
        description=(
            "A specific next action a Product Marketing Manager should take."
        )
    )

    guardrail: str = Field(
        description=(
            "A legal, brand, evidence, product-quality, safety, or "
            "human-review guardrail."
        )
    )

    confidence_level: Literal["low", "medium", "high"] = Field(
        description=(
            "A qualitative confidence level based on evidence consistency "
            "and source diversity. This is not a probability."
        )
    )

    confidence_rationale: str = Field(
        description=(
            "Why the confidence level was selected."
        )
    )


class IntelligenceReport(BaseModel):
    """
    Structured Customer Intelligence report for a PMM.
    """

    executive_summary: str = Field(
        description=(
            "A concise summary of the most decision-relevant findings."
        )
    )

    insights: list[StrategicInsight] = Field(
        description="Three to five high-value strategic insights."
    )

    missing_evidence: list[str] = Field(
        description=(
            "Information still needed before making a final GTM decision."
        )
    )

    recommended_research_questions: list[str] = Field(
        description=(
            "Specific research questions that would reduce uncertainty."
        )
    )


SYSTEM_INSTRUCTIONS = """
You are a senior Customer Intelligence and Product Marketing analyst.

Your responsibility is to transform multi-source evidence into defensible
Product Marketing decisions.

Follow these rules:

1. Use only the evidence supplied in the prompt.
2. Never invent statistics, quotations, product capabilities, customer
   segments, sources, outcomes, or business results.
3. Cite the exact evidence ROW IDs supporting every insight.
4. Separate current customer evidence from organizational knowledge.
5. Do not treat past launch learnings as current customer feedback.
6. Identify patterns supported by more than one record whenever possible.
7. Include counter-evidence, disagreements, uncertainty, and missing evidence.
8. Distinguish product-quality problems from messaging problems.
9. Do not recommend marketing language as a substitute for fixing a broken
   customer experience.
10. Recommend human escalation for legal, safety, trust, unsupported claims,
    or sensitive customer decisions.
11. Focus recommendations on PMM decisions such as segmentation,
    positioning, messaging, launch readiness, GTM, and research.
12. Avoid generic language such as revolutionize, game-changing, or
    AI-powered unless it is directly relevant.
13. Produce three to five strategic insights.
14. Confidence must be qualitative: low, medium, or high. It must not be
    represented as a statistical probability.
"""


def _clean_value(value: object) -> str:
    """
    Convert dataframe values into safe, compact strings.
    """
    if value is None:
        return ""

    text = str(value).replace("\n", " ").strip()

    if text.lower() == "nan":
        return ""

    return text


def build_evidence_packet(
    frame: pd.DataFrame,
    max_records: int = 35,
    max_characters_per_record: int = 650,
) -> str:
    """
    Convert normalized signals into a compact, numbered evidence packet.

    The row number allows the model to cite evidence that the application
    can later display to the PMM.
    """
    if frame.empty:
        raise ValueError("The normalized signal dataframe is empty.")

    selected_frame = frame.head(max_records)
    records: list[str] = []

    for row_id, row in selected_frame.iterrows():
        source = _clean_value(row.get("source"))
        source_type = _clean_value(row.get("source_type"))
        created_at = _clean_value(row.get("created_at"))
        text = _clean_value(row.get("text"))[
            :max_characters_per_record
        ]

        segment = ""
        metadata = row.get("metadata")

        if isinstance(metadata, dict):
            segment = _clean_value(metadata.get("segment"))

        record = (
            f"[ROW {row_id}] | "
            f"source={source} | "
            f"source_type={source_type} | "
            f"date={created_at} | "
            f"segment={segment} | "
            f"text={text}"
        )

        records.append(record)

    return "\n".join(records)


def generate_intelligence_report(
    frame: pd.DataFrame,
    product_name: str,
    launch_goal: str,
    target_market: str,
) -> IntelligenceReport:
    """
    Generate a structured, evidence-backed PMM intelligence report.
    """
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing from the .env file."
        )

    model = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.1-flash-lite",
    )

    evidence_packet = build_evidence_packet(frame)

    prompt = f"""
{SYSTEM_INSTRUCTIONS}

PRODUCT MARKETING CONTEXT

Product:
{product_name}

Launch goal:
{launch_goal}

Target market:
{target_market}

NORMALIZED EVIDENCE

{evidence_packet}

TASK

Produce a structured Customer Intelligence report.

The report must:

- contain three to five strategic insights;
- cite valid ROW IDs for every insight;
- explain what the evidence means for Product Marketing;
- distinguish customer evidence from past launch knowledge;
- include counter-evidence or uncertainty;
- identify missing evidence;
- provide practical recommendations, next actions, and guardrails;
- avoid all unsupported statistics and claims.
"""

    with genai.Client(api_key=api_key) as client:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=IntelligenceReport,
            ),
        )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    report = IntelligenceReport.model_validate_json(
        response.text
    )

    valid_row_ids = set(frame.index.tolist())

    for insight in report.insights:
        invalid_ids = [
            row_id
            for row_id in insight.evidence_row_ids
            if row_id not in valid_row_ids
        ]

        if invalid_ids:
            raise RuntimeError(
                "Gemini returned invalid evidence row IDs: "
                f"{invalid_ids}"
            )

    return report
