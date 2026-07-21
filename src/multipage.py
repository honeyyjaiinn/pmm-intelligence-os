from __future__ import annotations

from datetime import datetime
import html
from pathlib import Path

import pandas as pd
import streamlit as st

from src.connectors import (
    CPSCRecallConnector,
    CSVConnector,
    NewsAPIConnector,
    RedditConnector,
)
from src.pipeline import (
    build_decision_cards,
    extract_theme_evidence,
    normalize_signals,
    summarize_themes,
)
from src.pipeline.gemini_insights import (
    generate_intelligence_report,
)
from src.pipeline.gemini_reviewer import (
    review_intelligence_report,
)
from src.ui import render_hero


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def initialize_state() -> None:
    defaults = {
        "product_name": "AI Seller Assistant",
        "launch_goal": "Increase seller adoption",
        "target_market": "US marketplace",

        "use_reviews": True,
        "use_interviews": True,
        "use_support": True,
        "use_past_launches": True,
        "use_cpsc": False,
        "use_news": False,
        "use_reddit": False,

        "cpsc_query": "battery",
        "news_query": "marketplace seller AI",
        "subreddit": "Ebay",
        "reddit_query": "seller listing",

        "evidence_frame": None,
        "selected_sources": [],
        "connector_errors": [],

        "baseline_evidence": None,
        "baseline_summary": None,
        "baseline_cards": [],

        "gemini_report": None,
        "governance_review": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _prepare_evidence():
    signals = []
    errors = []
    selected_sources = []

    def add_csv(filename, source, source_type):
        connector = CSVConnector(
            PROJECT_ROOT / "sample_data" / filename,
            source,
            source_type,
        )
        signals.extend(connector.fetch())
        selected_sources.append(source)

    if st.session_state.use_reviews:
        add_csv(
            "app_reviews.csv",
            "App reviews (sample)",
            "app_review",
        )

    if st.session_state.use_interviews:
        add_csv(
            "interviews.csv",
            "Customer interviews (sample)",
            "interview",
        )

    if st.session_state.use_support:
        add_csv(
            "support_tickets.csv",
            "Support tickets (sample)",
            "support",
        )

    if st.session_state.use_past_launches:
        add_csv(
            "past_launches.csv",
            "Past launch learnings (sample)",
            "organizational_knowledge",
        )

    if st.session_state.use_cpsc:
        try:
            signals.extend(
                CPSCRecallConnector().fetch(
                    product_name=st.session_state.cpsc_query,
                    limit=30,
                )
            )
            selected_sources.append("CPSC recalls")
        except Exception as exc:
            errors.append(f"CPSC: {exc}")

    if st.session_state.use_news:
        try:
            signals.extend(
                NewsAPIConnector().fetch(
                    query=st.session_state.news_query,
                    limit=25,
                )
            )
            selected_sources.append("NewsAPI")
        except Exception as exc:
            errors.append(f"NewsAPI: {exc}")

    if st.session_state.use_reddit:
        try:
            signals.extend(
                RedditConnector().fetch(
                    subreddit=st.session_state.subreddit,
                    query=st.session_state.reddit_query,
                    limit=40,
                )
            )
            selected_sources.append(
                f"Reddit r/{st.session_state.subreddit}"
            )
        except Exception as exc:
            errors.append(f"Reddit: {exc}")

    frame = normalize_signals(
        [signal.to_dict() for signal in signals]
    )

    return frame, errors, selected_sources


def _render_intelligence(report, frame: pd.DataFrame) -> None:
    with st.container(border=True):
        st.markdown("### Executive summary")
        st.write(report.executive_summary)

    icons = {
        "high": "🟢",
        "medium": "🟡",
        "low": "🔴",
    }

    for insight in report.insights:
        with st.container(border=True):
            content, metrics = st.columns([4, 1])

            with content:
                st.markdown(f"### {insight.title}")
                st.markdown(
                    f"**Customer problem:** "
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
                    f"**Evidence synthesis:** "
                    f"{insight.evidence_summary}"
                )

                if (
                    insight.counter_evidence_or_uncertainty
                    .strip()
                ):
                    st.markdown(
                        "**Counter-evidence or uncertainty:** "
                        f"{insight.counter_evidence_or_uncertainty}"
                    )

                st.markdown(
                    f"**PMM implication:** "
                    f"{insight.pmm_implication}"
                )
                st.markdown(
                    f"**Recommendation:** "
                    f"{insight.recommendation}"
                )
                st.markdown(
                    f"**Next action:** "
                    f"{insight.next_action}"
                )
                st.markdown(
                    f"**Guardrail:** "
                    f"{insight.guardrail}"
                )

            with metrics:
                icon = icons.get(
                    insight.confidence_level,
                    "⚪",
                )

                st.metric(
                    "Confidence",
                    f"{icon} "
                    f"{insight.confidence_level.title()}",
                )
                st.metric(
                    "Evidence records",
                    len(insight.evidence_row_ids),
                )
                st.metric(
                    "Source types",
                    len(set(insight.source_types)),
                )
                st.caption(
                    insight.confidence_rationale
                )

            valid_ids = [
                row_id
                for row_id in insight.evidence_row_ids
                if row_id in frame.index
            ]

            with st.expander("View cited evidence"):
                if valid_ids:
                    st.dataframe(
                        frame.loc[
                            valid_ids,
                            [
                                "source",
                                "source_type",
                                "created_at",
                                "rating",
                                "text",
                                "url",
                            ],
                        ],
                        width="stretch",
                    )
                else:
                    st.warning(
                        "No valid evidence rows returned."
                    )

    with st.expander(
        "Missing evidence and research questions"
    ):
        st.markdown("#### Missing evidence")

        for item in report.missing_evidence:
            st.write(f"- {item}")

        st.markdown(
            "#### Recommended research questions"
        )

        for question in (
            report.recommended_research_questions
        ):
            st.write(f"- {question}")


def _render_governance(review, frame: pd.DataFrame) -> None:
    overall_icons = {
        "approve": "🟢",
        "approve_with_revisions": "🟡",
        "reject": "🔴",
    }

    verdict_icons = {
        "approve": "🟢",
        "revise": "🟡",
        "reject": "🔴",
    }

    overall_icon = overall_icons.get(
        review.overall_verdict,
        "⚪",
    )

    with st.container(border=True):
        st.markdown(
            f"### {overall_icon} Overall verdict: "
            f"{review.overall_verdict.replace('_', ' ').title()}"
        )
        st.markdown(
            f"**Executive assessment:** "
            f"{review.executive_assessment}"
        )
        st.markdown(
            f"**Audit summary:** "
            f"{review.audit_summary}"
        )

    for item in review.insight_reviews:
        with st.container(border=True):
            content, status = st.columns([4, 1])

            with content:
                icon = verdict_icons.get(
                    item.verdict,
                    "⚪",
                )

                st.markdown(
                    f"### {icon} {item.insight_title}"
                )
                st.markdown(
                    f"**Reviewer rationale:** "
                    f"{item.reviewer_rationale}"
                )
                st.markdown(
                    "**Reviewed customer problem:** "
                    f"{item.revised_customer_problem}"
                )
                st.markdown(
                    "**Reviewed PMM implication:** "
                    f"{item.revised_pmm_implication}"
                )
                st.markdown(
                    "**Reviewed recommendation:** "
                    f"{item.revised_recommendation}"
                )
                st.markdown(
                    "**Reviewed next action:** "
                    f"{item.revised_next_action}"
                )
                st.markdown(
                    "**Reviewed guardrail:** "
                    f"{item.revised_guardrail}"
                )

            with status:
                st.metric(
                    "Verdict",
                    item.verdict.title(),
                )
                st.metric(
                    "Evidence alignment",
                    item.evidence_alignment.title(),
                )
                st.metric(
                    "Confidence",
                    item.revised_confidence_level.title(),
                )
                st.metric(
                    "Human review",
                    (
                        "Required"
                        if item.human_review_required
                        else "Not required"
                    ),
                )

            with st.expander(
                "View issues and evidence audit"
            ):
                if item.issues:
                    for issue in item.issues:
                        st.markdown(
                            f"- **{issue.severity.upper()} · "
                            f"{issue.category.replace('_', ' ').title()}**: "
                            f"{issue.explanation}"
                        )
                else:
                    st.write(
                        "No material governance issues."
                    )

                st.write(
                    "Valid supporting rows:",
                    item.valid_supporting_row_ids,
                )
                st.write(
                    "Unsupported or misused rows:",
                    item.unsupported_or_misused_row_ids,
                )

    with st.expander(
        "Cross-cutting risks and human escalations"
    ):
        st.markdown("#### Cross-cutting risks")

        for risk in review.cross_cutting_risks:
            st.write(f"- {risk}")

        st.markdown(
            "#### Required human escalations"
        )

        for escalation in (
            review.required_human_escalations
        ):
            st.write(f"- {escalation}")


def render_overview() -> None:
    render_hero()

    product = html.escape(
        str(st.session_state.product_name)
    )
    goal = html.escape(
        str(st.session_state.launch_goal)
    )
    market = html.escape(
        str(st.session_state.target_market)
    )

    st.html(
        """
        <section class="overview-section">
            <h2 class="overview-heading">Guided workflow</h2>

            <div class="workflow-grid">
                <article class="workflow-card">
                    <div class="workflow-step">Step 1</div>
                    <h3>Signal Hub</h3>
                    <p>
                        Connect and normalize customer, competitive,
                        organizational, and product-risk evidence.
                    </p>
                </article>

                <article class="workflow-card">
                    <div class="workflow-step">Step 2</div>
                    <h3>Customer Intelligence</h3>
                    <p>
                        Generate evidence-backed PMM recommendations,
                        implications, guardrails, and research gaps.
                    </p>
                </article>

                <article class="workflow-card">
                    <div class="workflow-step">Step 3</div>
                    <h3>Governance Review</h3>
                    <p>
                        Approve, revise, or reject recommendations
                        before a Product Marketer acts.
                    </p>
                </article>
            </div>
        </section>
        """
    )

    st.html(
        f"""
        <section class="overview-section launch-section">
            <h2 class="overview-heading">Current launch</h2>

            <div class="launch-grid">
                <article class="launch-card">
                    <div class="launch-label">Product</div>
                    <div class="launch-value">{product}</div>
                </article>

                <article class="launch-card">
                    <div class="launch-label">Goal</div>
                    <div class="launch-value">{goal}</div>
                </article>

                <article class="launch-card">
                    <div class="launch-label">Market</div>
                    <div class="launch-value">{market}</div>
                </article>
            </div>
        </section>
        """
    )

    st.info(
        "Start with **Signal Hub** from the sidebar."
    )


def render_signal_hub() -> None:
    st.title("Signal Hub")
    st.caption(
        "Connect, normalize, and deduplicate signals "
        "before GenAI analysis."
    )

    with st.form("signal_form"):
        left, right = st.columns(2)

        with left:
            st.checkbox(
                "Sample app reviews",
                key="use_reviews",
            )
            st.checkbox(
                "Sample customer interviews",
                key="use_interviews",
            )
            st.checkbox(
                "Sample support tickets",
                key="use_support",
            )
            st.checkbox(
                "Sample past launch learnings",
                key="use_past_launches",
            )

        with right:
            st.checkbox(
                "CPSC recalls",
                key="use_cpsc",
            )
            st.checkbox(
                "NewsAPI",
                key="use_news",
            )
            st.checkbox(
                "Reddit API",
                key="use_reddit",
            )

        settings_1, settings_2 = st.columns(2)

        with settings_1:
            st.text_input(
                "CPSC product filter",
                key="cpsc_query",
            )
            st.text_input(
                "News search",
                key="news_query",
            )

        with settings_2:
            st.text_input(
                "Subreddit",
                key="subreddit",
            )
            st.text_input(
                "Reddit search",
                key="reddit_query",
            )

        submitted = st.form_submit_button(
            "Prepare evidence",
            type="primary",
            width="stretch",
        )

    if submitted:
        with st.spinner(
            "Connecting and normalizing signals..."
        ):
            frame, errors, selected_sources = (
                _prepare_evidence()
            )

        if frame.empty:
            st.error(
                "No usable evidence returned."
            )
        else:
            baseline_evidence = (
                extract_theme_evidence(frame)
            )
            baseline_summary = summarize_themes(
                baseline_evidence
            )
            baseline_cards = build_decision_cards(
                baseline_summary
            )

            st.session_state.evidence_frame = frame
            st.session_state.connector_errors = errors
            st.session_state.selected_sources = (
                selected_sources
            )
            st.session_state.baseline_evidence = (
                baseline_evidence
            )
            st.session_state.baseline_summary = (
                baseline_summary
            )
            st.session_state.baseline_cards = (
                baseline_cards
            )

            st.session_state.gemini_report = None
            st.session_state.governance_review = None

            st.success(
                "Evidence store prepared."
            )

    for error in st.session_state.connector_errors:
        st.warning(error)

    frame = st.session_state.evidence_frame

    if frame is None or frame.empty:
        st.info(
            "Select sources and prepare the evidence."
        )
        return

    metric_1, metric_2, metric_3 = st.columns(3)

    metric_1.metric(
        "Signals",
        len(frame),
    )
    metric_2.metric(
        "Source types",
        frame["source_type"].nunique(),
    )
    metric_3.metric(
        "Connected sources",
        len(st.session_state.selected_sources),
    )

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
        ].head(20),
        width="stretch",
        hide_index=True,
    )

    st.success(
        "Evidence is ready. Open "
        "**Customer Intelligence**."
    )


def render_customer_intelligence() -> None:
    st.title("Customer Intelligence Agent")
    st.caption(
        "Transforms normalized evidence into "
        "structured PMM recommendations."
    )

    frame = st.session_state.evidence_frame

    if frame is None or frame.empty:
        st.warning(
            "Prepare the Signal Hub first."
        )
        return

    if st.button(
        "Run Customer Intelligence Agent",
        type="primary",
        width="stretch",
    ):
        try:
            with st.spinner(
                "Gemini is synthesizing evidence..."
            ):
                report = (
                    generate_intelligence_report(
                        frame=frame,
                        product_name=(
                            st.session_state.product_name
                        ),
                        launch_goal=(
                            st.session_state.launch_goal
                        ),
                        target_market=(
                            st.session_state.target_market
                        ),
                    )
                )

            st.session_state.gemini_report = report
            st.session_state.governance_review = None
            st.success(
                "Customer intelligence generated."
            )

        except Exception as exc:
            st.error(
                f"Customer Intelligence failed: {exc}"
            )

    report = st.session_state.gemini_report

    if report is None:
        st.info(
            "Run the agent to create the report."
        )
        return

    _render_intelligence(report, frame)


def render_governance() -> None:
    st.title("Reviewer and Governance Agent")
    st.caption(
        "Audits recommendations against the "
        "original evidence."
    )

    frame = st.session_state.evidence_frame
    report = st.session_state.gemini_report

    if frame is None or frame.empty:
        st.warning(
            "Prepare the Signal Hub first."
        )
        return

    if report is None:
        st.warning(
            "Run Customer Intelligence first."
        )
        return

    if st.button(
        "Run Governance Reviewer",
        type="primary",
        width="stretch",
    ):
        try:
            with st.spinner(
                "Auditing evidence and guardrails..."
            ):
                review = (
                    review_intelligence_report(
                        frame=frame,
                        draft_report=report,
                        product_name=(
                            st.session_state.product_name
                        ),
                        launch_goal=(
                            st.session_state.launch_goal
                        ),
                        target_market=(
                            st.session_state.target_market
                        ),
                    )
                )

            st.session_state.governance_review = (
                review
            )

            st.success(
                "Governance review completed."
            )

        except Exception as exc:
            st.error(
                f"Governance review failed: {exc}"
            )

    review = st.session_state.governance_review

    if review is None:
        st.info(
            "Run the reviewer to audit the draft."
        )
        return

    _render_governance(review, frame)


def render_evidence() -> None:
    st.title("Evidence and Deterministic Baseline")
    st.caption(
        "Inspect source records and compare the "
        "GenAI workflow against the transparent baseline."
    )

    frame = st.session_state.evidence_frame

    if frame is None or frame.empty:
        st.warning(
            "Prepare the Signal Hub first."
        )
        return

    baseline_tab, evidence_tab = st.tabs(
        [
            "Deterministic baseline",
            "Normalized evidence",
        ]
    )

    with baseline_tab:
        cards = st.session_state.baseline_cards
        evidence = (
            st.session_state.baseline_evidence
        )
        summary = (
            st.session_state.baseline_summary
        )

        for card in cards:
            with st.container(border=True):
                st.markdown(
                    f"### {card['theme']}"
                )
                st.markdown(
                    f"**Recommendation:** "
                    f"{card['decision']}"
                )
                st.markdown(
                    f"**Next action:** "
                    f"{card['next_action']}"
                )
                st.markdown(
                    f"**Guardrail:** "
                    f"{card['risk']}"
                )

        if summary is not None and not summary.empty:
            st.bar_chart(
                summary.set_index("theme")[
                    "mentions"
                ]
            )

            st.dataframe(
                summary,
                width="stretch",
                hide_index=True,
            )

    with evidence_tab:
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
            width="stretch",
            hide_index=False,
        )
