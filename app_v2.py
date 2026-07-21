from __future__ import annotations

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.connectors import (
    CSVConnector,
    CPSCRecallConnector,
    RedditConnector,
    NewsAPIConnector,
)
from src.pipeline import (
    normalize_signals,
    extract_theme_evidence,
    summarize_themes,
    build_decision_cards,
)
from src.pipeline.gemini_insights import (
    generate_intelligence_report,
)


load_dotenv()
BASE_DIR = Path(__file__).parent


st.set_page_config(
    page_title="PMM Intelligence OS v2",
    page_icon="🧭",
    layout="wide",
)


st.title("PMM Intelligence OS")
st.caption(
    "Evidence-backed customer, competitive, and risk intelligence "
    "for Product Marketing teams."
)


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:
    st.header("Launch context")

    product_name = st.text_input(
        "Product",
        "AI Seller Assistant",
    )

    launch_goal = st.text_input(
        "Launch goal",
        "Increase seller adoption",
    )

    target_market = st.text_input(
        "Target market",
        "US marketplace",
    )

    st.header("Analysis mode")

    use_genai = st.checkbox(
        "Gemini strategic synthesis",
        value=True,
        help=(
            "Uses Gemini to synthesize evidence into structured "
            "Product Marketing recommendations."
        ),
    )

    st.header("Signal connectors")

    use_reviews = st.checkbox(
        "Sample app reviews",
        True,
    )

    use_interviews = st.checkbox(
        "Sample customer interviews",
        True,
    )

    use_support = st.checkbox(
        "Sample support tickets",
        True,
    )

    use_past_launches = st.checkbox(
        "Sample past launch learnings",
        True,
    )

    use_cpsc = st.checkbox(
        "CPSC recalls",
        False,
    )

    use_reddit = st.checkbox(
        "Reddit API",
        False,
    )

    use_news = st.checkbox(
        "NewsAPI",
        False,
    )

    cpsc_query = st.text_input(
        "CPSC product filter",
        "battery",
    )

    subreddit = st.text_input(
        "Subreddit",
        "Ebay",
    )

    reddit_query = st.text_input(
        "Reddit search",
        "seller listing",
    )

    news_query = st.text_input(
        "News search",
        "ecommerce seller AI",
    )

    run = st.button(
        "Generate intelligence",
        type="primary",
        use_container_width=True,
    )


if not run:
    st.info(
        "Select signal sources and click "
        "**Generate intelligence**."
    )
    st.stop()


# ---------------------------------------------------------
# Ingestion
# ---------------------------------------------------------

signals = []
connector_errors = []


def add_csv(
    filename: str,
    source: str,
    source_type: str,
) -> None:
    connector = CSVConnector(
        BASE_DIR / "sample_data" / filename,
        source,
        source_type,
    )

    signals.extend(connector.fetch())


if use_reviews:
    add_csv(
        "app_reviews.csv",
        "App reviews (sample)",
        "app_review",
    )

if use_interviews:
    add_csv(
        "interviews.csv",
        "Customer interviews (sample)",
        "interview",
    )

if use_support:
    add_csv(
        "support_tickets.csv",
        "Support tickets (sample)",
        "support",
    )

if use_past_launches:
    add_csv(
        "past_launches.csv",
        "Past launch learnings (sample)",
        "organizational_knowledge",
    )

if use_cpsc:
    try:
        signals.extend(
            CPSCRecallConnector().fetch(
                product_name=cpsc_query,
                limit=30,
            )
        )
    except Exception as exc:
        connector_errors.append(
            f"CPSC connector: {exc}"
        )

if use_reddit:
    try:
        signals.extend(
            RedditConnector().fetch(
                subreddit=subreddit,
                query=reddit_query,
                limit=40,
            )
        )
    except Exception as exc:
        connector_errors.append(
            f"Reddit connector: {exc}"
        )

if use_news:
    try:
        signals.extend(
            NewsAPIConnector().fetch(
                query=news_query,
                limit=25,
            )
        )
    except Exception as exc:
        connector_errors.append(
            f"NewsAPI connector: {exc}"
        )


for error in connector_errors:
    st.warning(error)


records = [
    signal.to_dict()
    for signal in signals
]

frame = normalize_signals(records)


if frame.empty:
    st.error(
        "No usable evidence was returned from the selected sources."
    )
    st.stop()


# ---------------------------------------------------------
# Deterministic analysis
# ---------------------------------------------------------

baseline_evidence = extract_theme_evidence(frame)
baseline_summary = summarize_themes(
    baseline_evidence
)
baseline_cards = build_decision_cards(
    baseline_summary
)


# ---------------------------------------------------------
# Gemini analysis
# ---------------------------------------------------------

gemini_report = None
gemini_error = None


if use_genai:
    try:
        with st.spinner(
            "Gemini is synthesizing cross-source evidence..."
        ):
            gemini_report = generate_intelligence_report(
                frame=frame,
                product_name=product_name,
                launch_goal=launch_goal,
                target_market=target_market,
            )

    except Exception as exc:
        gemini_error = str(exc)
        st.warning(
            f"Gemini analysis could not run: {gemini_error}"
        )


# ---------------------------------------------------------
# Overview metrics
# ---------------------------------------------------------

metric_1, metric_2, metric_3, metric_4 = st.columns(4)


metric_1.metric(
    "Signals analyzed",
    len(frame),
)

metric_2.metric(
    "Source types",
    frame["source_type"].nunique(),
)

metric_3.metric(
    "Baseline themes",
    (
        baseline_summary["theme"].nunique()
        if not baseline_summary.empty
        else 0
    ),
)

metric_4.metric(
    "Gemini insights",
    (
        len(gemini_report.insights)
        if gemini_report
        else 0
    ),
)


st.caption(
    f"Launch: **{product_name}** · "
    f"Goal: **{launch_goal}** · "
    f"Market: **{target_market}**"
)


# ---------------------------------------------------------
# Gemini strategic synthesis
# ---------------------------------------------------------

if gemini_report:
    st.subheader(
        "Gemini strategic synthesis"
    )

    with st.container(border=True):
        st.markdown(
            "### Executive summary"
        )
        st.write(
            gemini_report.executive_summary
        )

    confidence_icons = {
        "high": "🟢",
        "medium": "🟡",
        "low": "🔴",
    }

    for insight in gemini_report.insights:
        with st.container(border=True):
            content_column, metrics_column = st.columns(
                [4, 1]
            )

            with content_column:
                st.markdown(
                    f"### {insight.title}"
                )

                st.markdown(
                    "**Customer problem:** "
                    f"{insight.customer_problem}"
                )

                if insight.affected_segments:
                    st.markdown(
                        "**Affected segments:** "
                        + ", ".join(
                            insight.affected_segments
                        )
                    )

                st.markdown(
                    "**Evidence synthesis:** "
                    f"{insight.evidence_summary}"
                )

                if (
                    insight
                    .counter_evidence_or_uncertainty
                    .strip()
                ):
                    st.markdown(
                        "**Counter-evidence or uncertainty:** "
                        f"{insight.counter_evidence_or_uncertainty}"
                    )

                st.markdown(
                    "**PMM implication:** "
                    f"{insight.pmm_implication}"
                )

                st.markdown(
                    "**Recommendation:** "
                    f"{insight.recommendation}"
                )

                st.markdown(
                    "**Next action:** "
                    f"{insight.next_action}"
                )

                st.markdown(
                    "**Guardrail:** "
                    f"{insight.guardrail}"
                )

            with metrics_column:
                confidence_icon = confidence_icons.get(
                    insight.confidence_level,
                    "⚪",
                )

                st.metric(
                    "Confidence",
                    (
                        f"{confidence_icon} "
                        f"{insight.confidence_level.title()}"
                    ),
                )

                st.metric(
                    "Evidence records",
                    len(
                        insight.evidence_row_ids
                    ),
                )

                st.metric(
                    "Source types",
                    len(
                        set(insight.source_types)
                    ),
                )

                st.caption(
                    insight.confidence_rationale
                )

            valid_row_ids = [
                row_id
                for row_id in insight.evidence_row_ids
                if row_id in frame.index
            ]

            with st.expander(
                "View Gemini-cited evidence"
            ):
                if not valid_row_ids:
                    st.warning(
                        "No valid evidence rows were returned."
                    )
                else:
                    cited_evidence = frame.loc[
                        valid_row_ids,
                        [
                            "source",
                            "source_type",
                            "created_at",
                            "rating",
                            "text",
                            "url",
                        ],
                    ]

                    st.dataframe(
                        cited_evidence,
                        use_container_width=True,
                        hide_index=False,
                    )


    with st.expander(
        "Missing evidence and recommended research"
    ):
        st.markdown(
            "#### Missing evidence"
        )

        if gemini_report.missing_evidence:
            for item in gemini_report.missing_evidence:
                st.write(f"- {item}")
        else:
            st.write(
                "No missing evidence was identified."
            )

        st.markdown(
            "#### Recommended research questions"
        )

        if (
            gemini_report
            .recommended_research_questions
        ):
            for question in (
                gemini_report
                .recommended_research_questions
            ):
                st.write(f"- {question}")
        else:
            st.write(
                "No additional questions were generated."
            )


# ---------------------------------------------------------
# Deterministic baseline
# ---------------------------------------------------------

st.subheader(
    "Deterministic baseline"
)

st.caption(
    "The baseline uses transparent keyword classification. "
    "It remains visible so Gemini findings can be compared "
    "against a repeatable, low-cost reference."
)


if not baseline_cards:
    st.warning(
        "No configured baseline theme matched the evidence."
    )

else:
    for card in baseline_cards:
        with st.container(border=True):
            content_column, metrics_column = st.columns(
                [4, 1]
            )

            with content_column:
                st.markdown(
                    f"### {card['theme']}"
                )

                st.markdown(
                    "**Recommendation:** "
                    f"{card['decision']}"
                )

                st.markdown(
                    "**Next action:** "
                    f"{card['next_action']}"
                )

                st.markdown(
                    "**Guardrail:** "
                    f"{card['risk']}"
                )

            with metrics_column:
                st.metric(
                    "Heuristic confidence",
                    f"{card['confidence']}%",
                )

                st.metric(
                    "Evidence",
                    f"{card['mentions']} signals",
                )

                st.metric(
                    "Source diversity",
                    card["source_types"],
                )

            matching_evidence = (
                baseline_evidence[
                    baseline_evidence["theme"]
                    == card["theme"]
                ]
                .head(5)
            )

            with st.expander(
                "View baseline evidence"
            ):
                st.dataframe(
                    matching_evidence[
                        [
                            "source",
                            "source_type",
                            "text",
                            "url",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )


# ---------------------------------------------------------
# Baseline summary
# ---------------------------------------------------------

st.subheader(
    "Cross-source baseline summary"
)


if baseline_summary.empty:
    st.write(
        "No baseline themes were detected."
    )

else:
    st.bar_chart(
        baseline_summary.set_index(
            "theme"
        )["mentions"]
    )

    st.dataframe(
        baseline_summary,
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------
# Raw evidence
# ---------------------------------------------------------

with st.expander(
    "Normalized evidence store"
):
    st.dataframe(
        frame[
            [
                "source",
                "source_type",
                "created_at",
                "rating",
                "text",
                "url",
            ]
        ],
        use_container_width=True,
        hide_index=False,
    )


st.caption(
    "Gemini confidence is qualitative and based on evidence "
    "consistency and diversity. Baseline confidence is a "
    "transparent heuristic. Neither represents a calibrated "
    "statistical probability."
)
