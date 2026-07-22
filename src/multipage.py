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
        "launch_goal": "Increase seller adoption while preserving trust and seller control",
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

        "demo_evidence_initialized": False,
        "evidence_frame": None,
        "selected_sources": [],
        "connector_errors": [],

        "baseline_evidence": None,
        "baseline_summary": None,
        "baseline_cards": [],

        # Customer Intelligence Agent configuration
        "intel_analysis_objective": "Launch adoption and readiness",
        "intel_output_depth": "Balanced",
        "intel_max_insights": 4,
        "intel_min_evidence_records": 2,
        "intel_segment_focus": "All evidence-supported segments",
        "intel_confidence_policy": "Conservative",
        "intel_require_counter_evidence": True,
        "intel_require_guardrails": True,

        # Governance Agent configuration
        "governance_strictness": "High",
        "governance_required_alignment": "Strong",
        "governance_downgrade_overconfidence": True,
        "governance_human_review_threshold": (
            "High-risk or unsupported claims"
        ),
        "governance_escalation_categories": [
            "PMM",
            "Product",
            "Research",
            "Legal",
            "Trust & Safety",
        ],

        # Intended production runtime policy
        "runtime_preprocessing_policy": (
            "Rules + lightweight ML"
        ),
        "runtime_bucket_dimensions": [
            "Sentiment",
            "Topic",
            "Segment",
            "Region",
            "Product version",
            "Recency",
        ],
        "runtime_retrieval_policy": (
            "RAG over evidence buckets and representative records"
        ),
        "runtime_model_routing": (
            "Low-cost tagging models; reasoning model for synthesis"
        ),
        "runtime_optimization_priority": (
            "Balanced quality, latency, and cost"
        ),

        "gemini_report": None,
        "governance_review": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Ensure the public demo never opens with blank launch context.
    launch_defaults = {
        "product_name": "AI Seller Assistant",
        "launch_goal": (
            "Increase seller adoption while preserving trust "
            "and seller control"
        ),
        "target_market": "US marketplace",
    }

    for key, value in launch_defaults.items():
        current_value = str(
            st.session_state.get(key, "")
        ).strip()

        if not current_value:
            st.session_state[key] = value

    # Prepare only reliable sample evidence for each new browser session.
    # This does not call Gemini or consume model quota.
    if not st.session_state.demo_evidence_initialized:
        st.session_state.use_reviews = True
        st.session_state.use_interviews = True
        st.session_state.use_support = True
        st.session_state.use_past_launches = True

        # Keep optional live connectors off for the initial demo.
        for connector_key in (
            "use_cpsc",
            "use_news",
            "use_reddit",
        ):
            if connector_key in st.session_state:
                st.session_state[connector_key] = False

        frame, errors, selected_sources = _prepare_evidence()

        st.session_state.evidence_frame = frame
        st.session_state.connector_errors = errors
        st.session_state.selected_sources = selected_sources
        st.session_state.demo_evidence_initialized = True


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

    product = html.escape(str(st.session_state.product_name))
    goal = html.escape(str(st.session_state.launch_goal))
    market = html.escape(str(st.session_state.target_market))

    st.html(
        f"""
        <section class="principle-panel">
            <div class="principle-eyebrow">
                PRODUCT PRINCIPLE
            </div>

            <div class="principle-title">
                From Signal → To Decision
            </div>

            <div class="principle-flow">

                <article class="principle-step">
                    <span>01</span>
                    <strong>Signals & Evidence</strong>
                    <small>
                        Customer · Competitive · Organizational · Risk
                    </small>
                </article>

                <div class="principle-arrow">→</div>

                <article class="principle-step">
                    <span>02</span>
                    <strong>PMM Intelligence</strong>
                    <small>
                        Problems · Segments · PMM implications
                    </small>
                </article>

                <div class="principle-arrow">→</div>

                <article class="principle-step">
                    <span>03</span>
                    <strong>Governance</strong>
                    <small>
                        Evidence validation · Risk · Confidence
                    </small>
                </article>

                <div class="principle-arrow">→</div>

                <article class="principle-step">
                    <span>04</span>
                    <strong>PMM Decision</strong>
                    <small>
                        Positioning · Messaging · GTM action
                    </small>
                </article>

            </div>

            <div class="principle-footer">
                Insight before generation. Evidence before recommendation.
                Human judgment before execution.
            </div>
        </section>

        <section class="overview-section">
            <h2 class="overview-heading">How the workflow works</h2>

            <div class="workflow-grid">

                <article class="workflow-card">
                    <div class="workflow-step">STEP 1</div>
                    <h3>Prepare Evidence</h3>
                    <p>
                        Connect, normalize, deduplicate, and classify the
                        signals relevant to the launch decision.
                    </p>
                </article>

                <article class="workflow-card">
                    <div class="workflow-step">STEP 2</div>
                    <h3>Generate Intelligence</h3>
                    <p>
                        The Customer Intelligence Agent synthesizes evidence
                        into customer problems, segments, PMM implications,
                        recommendations, and next actions.
                    </p>
                </article>

                <article class="workflow-card">
                    <div class="workflow-step">STEP 3</div>
                    <h3>Review Recommendation</h3>
                    <p>
                        The Governance Reviewer checks evidence alignment,
                        confidence, unsupported claims, risks, and required
                        human escalation.
                    </p>
                </article>

                <article class="workflow-card">
                    <div class="workflow-step">STEP 4</div>
                    <h3>Evidence & Audit</h3>
                    <p>
                        Inspect the deterministic baseline and trace every
                        recommendation back to the normalized source evidence.
                    </p>
                </article>

            </div>
        </section>

        <section class="overview-section">
            <h2 class="overview-heading">Current launch context</h2>

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
        "Start with **1. Prepare Evidence** from the sidebar."
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
            st.session_state.use_reviews = st.checkbox(
                "Sample app reviews",
                value=True,
            )
            st.session_state.use_interviews = st.checkbox(
                "Sample customer interviews",
                value=True,
            )
            st.session_state.use_support = st.checkbox(
                "Sample support tickets",
                value=True,
            )
            st.session_state.use_past_launches = st.checkbox(
                "Sample past launch learnings",
                value=True,
            )

        with right:
            st.session_state.use_cpsc = st.checkbox(
                "CPSC recalls",
                value=False,
            )
            st.session_state.use_news = st.checkbox(
                "NewsAPI",
                value=False,
            )
            st.session_state.use_reddit = st.checkbox(
                "Reddit API",
                value=False,
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
                        configuration={
                            "analysis_objective": (
                                st.session_state
                                .intel_analysis_objective
                            ),
                            "output_depth": (
                                st.session_state
                                .intel_output_depth
                            ),
                            "maximum_insights": (
                                st.session_state
                                .intel_max_insights
                            ),
                            "minimum_evidence_records": (
                                st.session_state
                                .intel_min_evidence_records
                            ),
                            "segment_focus": (
                                st.session_state
                                .intel_segment_focus
                            ),
                            "confidence_policy": (
                                st.session_state
                                .intel_confidence_policy
                            ),
                            "require_counter_evidence": (
                                st.session_state
                                .intel_require_counter_evidence
                            ),
                            "require_guardrails": (
                                st.session_state
                                .intel_require_guardrails
                            ),
                        },
                    )
                )

            configured_maximum = int(

                st.session_state.intel_max_insights

            )

            report.insights = report.insights[

                :configured_maximum

            ]

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

    # Enforce the active PMM configuration at the rendering boundary.
    # This also fixes reports left in session state from an earlier run.
    configured_maximum = int(
        st.session_state.get(
            "intel_max_insights",
            4,
        )
    )

    if len(report.insights) > configured_maximum:
        report = report.model_copy(
            update={
                "insights": report.insights[
                    :configured_maximum
                ]
            }
        )
        st.session_state.gemini_report = report

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
                        configuration={
                            "strictness": (
                                st.session_state
                                .governance_strictness
                            ),
                            "required_alignment": (
                                st.session_state
                                .governance_required_alignment
                            ),
                            "downgrade_overconfidence": (
                                st.session_state
                                .governance_downgrade_overconfidence
                            ),
                            "human_review_threshold": (
                                st.session_state
                                .governance_human_review_threshold
                            ),
                            "escalation_categories": (
                                st.session_state
                                .governance_escalation_categories
                            ),
                        },
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



def render_agent_configuration() -> None:
    st.title("Agent Configuration")
    st.caption(
        "Configure agent business behavior through structured controls "
        "rather than editing raw prompts."
    )

    st.info(
        "**Control model:** PMM owns objectives, evidence standards, "
        "confidence policy, guardrails, and escalation rules. "
        "The platform team owns model deployment, security, reliability, "
        "and runtime infrastructure."
    )

    intelligence_tab, governance_tab, runtime_tab, prompt_ops_tab = st.tabs(
        [
            "Customer Intelligence",
            "Governance Reviewer",
            "Scale & Runtime Policy",
            "Prompt Operations",
        ]
    )

    with intelligence_tab:
        st.markdown("### Customer Intelligence Agent")
        st.write(
            "Controls how the agent interprets evidence and structures "
            "its Product Marketing recommendations."
        )

        with st.form("intelligence_configuration_form"):
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
                    [
                        "Executive",
                        "Balanced",
                        "Deep dive",
                    ],
                    key="intel_output_depth",
                )

                st.slider(
                    "Target strategic insights",
                    min_value=2,
                    max_value=6,
                    key="intel_max_insights",
                )

                st.number_input(
                    "Minimum supporting evidence records",
                    min_value=1,
                    max_value=10,
                    step=1,
                    key="intel_min_evidence_records",
                )

            with right:
                st.selectbox(
                    "Segment focus",
                    [
                        "All evidence-supported segments",
                        "Sellers",
                        "Buyers",
                        "New users",
                        "Power users",
                    ],
                    key="intel_segment_focus",
                )

                st.selectbox(
                    "Confidence policy",
                    [
                        "Conservative",
                        "Balanced",
                        "Exploratory",
                    ],
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

            intelligence_saved = st.form_submit_button(
                "Save Intelligence Agent Configuration",
                type="primary",
                use_container_width=True,
            )

        if intelligence_saved:
            # Existing reports no longer reflect the active configuration.
            st.session_state.gemini_report = None
            st.session_state.governance_review = None
            st.success(
                "Customer Intelligence configuration saved. "
                "Generate a new report to apply it."
            )

    with governance_tab:
        st.markdown("### Reviewer and Governance Agent")
        st.write(
            "Controls how strictly recommendations are audited before "
            "they are surfaced for human PMM decision-making."
        )

        with st.form("governance_configuration_form"):
            left, right = st.columns(2)

            with left:
                st.selectbox(
                    "Review strictness",
                    [
                        "Standard",
                        "High",
                        "Maximum",
                    ],
                    key="governance_strictness",
                )

                st.selectbox(
                    "Required evidence alignment",
                    [
                        "Partial",
                        "Strong",
                    ],
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
                    "Required escalation categories",
                    [
                        "PMM",
                        "Product",
                        "Research",
                        "Legal",
                        "Trust & Safety",
                        "Privacy",
                        "Brand",
                    ],
                    key="governance_escalation_categories",
                )

            governance_saved = st.form_submit_button(
                "Save Governance Configuration",
                type="primary",
                use_container_width=True,
            )

        if governance_saved:
            st.session_state.governance_review = None
            st.success(
                "Governance configuration saved. "
                "Run a new governance review to apply it."
            )

    with runtime_tab:
        st.markdown("### Aggregate First, Reason Second")

        st.warning(
            "This tab describes the intended production architecture. "
            "The current MVP still sends a small, bounded evidence packet "
            "directly to Gemini; large-scale bucketing and RAG are not yet "
            "implemented."
        )

        st.markdown(
            """
            At production scale, the platform should not make one expensive
            LLM call for every review. High-volume records are first cleaned,
            classified, and aggregated into evidence buckets. Retrieval then
            selects the relevant buckets and representative records for
            strategic LLM reasoning.
            """
        )

        with st.form("runtime_policy_form"):
            st.selectbox(
                "Initial classification policy",
                [
                    "Rules + lightweight ML",
                    "Lightweight ML only",
                    "LLM-first - not recommended at scale",
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
                "Production retrieval architecture",
                [
                    (
                        "RAG over evidence buckets and "
                        "representative records"
                    ),
                    "Direct bounded context - current MVP",
                ],
                key="runtime_retrieval_policy",
            )

            st.selectbox(
                "Model-routing policy",
                [
                    (
                        "Low-cost tagging models; "
                        "reasoning model for synthesis"
                    ),
                    "Single model for every task",
                ],
                key="runtime_model_routing",
            )

            st.selectbox(
                "Optimization priority",
                [
                    "Balanced quality, latency, and cost",
                    "Maximum quality",
                    "Lowest latency",
                    "Lowest inference cost",
                ],
                key="runtime_optimization_priority",
            )

            runtime_saved = st.form_submit_button(
                "Save Intended Runtime Policy",
                use_container_width=True,
            )

        if runtime_saved:
            st.success("Intended production runtime policy saved.")

        st.markdown("### Production non-functional requirements")

        nfr_1, nfr_2, nfr_3 = st.columns(3)

        with nfr_1:
            with st.container(border=True):
                st.markdown("#### Performance")
                st.write(
                    "Incremental processing, bounded context, caching, "
                    "asynchronous jobs, and measurable latency targets."
                )

        with nfr_2:
            with st.container(border=True):
                st.markdown("#### Cost")
                st.write(
                    "Use lightweight classification before reserving "
                    "reasoning models for aggregated strategic synthesis."
                )

        with nfr_3:
            with st.container(border=True):
                st.markdown("#### Scalability")
                st.write(
                    "Bucket hundreds of thousands of records and retrieve "
                    "only decision-relevant evidence."
                )



    with prompt_ops_tab:
        st.markdown("### Prompt Operations")
        st.caption(
            "Treat prompts as governed operational logic: versioned, "
            "evaluated, monitored, and safely rolled back."
        )

        st.info(
            "**Current MVP:** prompt contracts are implemented in Python. "
            "**Production path:** external prompt registry with owners, "
            "template variables, regression tests, approval workflow, "
            "observability, and rollback."
        )

        lifecycle_cols = st.columns(6)
        lifecycle = [
            ("Draft", "Define or update template"),
            ("Evaluate", "Run regression test cases"),
            ("Approve", "PMM / governance sign-off"),
            ("Deploy", "Promote active version"),
            ("Monitor", "Track quality and failures"),
            ("Rollback", "Restore last safe version"),
        ]

        for column, (stage, description) in zip(lifecycle_cols, lifecycle):
            with column:
                with st.container(border=True):
                    st.markdown(f"**{stage}**")
                    st.caption(description)

        left, right = st.columns(2)

        with left:
            with st.container(border=True):
                st.markdown("#### Customer Intelligence prompt")
                st.write("**Prompt ID:** `intelligence-agent`")
                st.write("**Active version:** `v1.2`")
                st.write("**Owner:** Product Marketing Capabilities")
                st.write("**Status:** Production candidate")
                st.write(
                    "**Template variables:** product, launch goal, "
                    "target market, evidence packet, agent configuration"
                )
                st.success("Regression test: passed")
                st.caption("Rollback version: v1.1")

        with right:
            with st.container(border=True):
                st.markdown("#### Governance Reviewer prompt")
                st.write("**Prompt ID:** `governance-reviewer`")
                st.write("**Active version:** `v1.1`")
                st.write("**Owner:** AI Governance / PMM Capabilities")
                st.write("**Status:** Production candidate")
                st.write(
                    "**Template variables:** original evidence, draft "
                    "recommendation, review policy, escalation categories"
                )
                st.success("Regression test: passed")
                st.caption("Rollback version: v1.0")

        st.markdown("### PMM control vs. prompt governance")
        col_1, col_2, col_3, col_4 = st.columns(4)

        with col_1:
            with st.container(border=True):
                st.markdown("**PMM-controlled fields**")
                st.caption(
                    "Objective, output depth, evidence threshold, "
                    "confidence policy, guardrails, escalation rules."
                )

        with col_2:
            with st.container(border=True):
                st.markdown("**Versioned templates**")
                st.caption(
                    "System instructions and prompt structure are managed "
                    "as governed assets, not freeform text boxes."
                )

        with col_3:
            with st.container(border=True):
                st.markdown("**Evaluation suite**")
                st.caption(
                    "Regression tests check citation quality, unsupported "
                    "claims, confidence calibration, and policy compliance."
                )

        with col_4:
            with st.container(border=True):
                st.markdown("**Release and rollback**")
                st.caption(
                    "Prompt changes can be approved, deployed, monitored, "
                    "and rolled back when quality regresses."
                )

        st.warning(
            "No raw prompt editing is exposed here. PMMs control business "
            "behavior through structured settings; prompt template changes "
            "would follow a governed release process."
        )


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
