from __future__ import annotations

import html

import streamlit as st


EBAY_COLORS = {
    "blue": "#3665F3",
    "red": "#E53238",
    "yellow": "#F5AF02",
    "green": "#86B817",
    "ink": "#191919",
    "muted": "#707070",
    "surface": "#F7F7F7",
    "line": "#D9D9D9",
}


CSS = """
<style>
:root {
    --ebay-blue: #3665F3;
    --ebay-red: #E53238;
    --ebay-yellow: #F5AF02;
    --ebay-green: #86B817;
    --ink: #191919;
    --muted: #707070;
    --surface: #F7F7F7;
    --surface-2: #F1F3F6;
    --line: #D9D9D9;
}

html, body, [class*="css"] {
    color: var(--ink);
}

.stApp {
    background: #FFFFFF;
}

/* Keep page content below Streamlit Cloud's fixed toolbar. */
[data-testid="stAppViewContainer"] .block-container {
    max-width: 1240px;
    padding-top: 4.75rem !important;
    padding-bottom: 4rem;
}

/* Give headings safe space when the browser keeps scroll position
   while users move between dashboard tabs. */
h1, h2, h3, .launch-header, .pipeline-banner {
    scroll-margin-top: 5.5rem;
}

.decision-summary-card {
    border: 1px solid var(--line);
    border-left: 7px solid var(--ebay-yellow);
    border-radius: 17px;
    background: #FFFFFF;
    padding: 1.25rem 1.3rem;
    box-shadow: 0 5px 18px rgba(0, 0, 0, 0.04);
}

.decision-summary-card.green { border-left-color: var(--ebay-green); }
.decision-summary-card.yellow { border-left-color: var(--ebay-yellow); }
.decision-summary-card.red { border-left-color: var(--ebay-red); }

.decision-summary-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #E6E6E6;
}

.decision-eyebrow {
    color: #6F6F6F;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}

.decision-headline {
    color: var(--ink);
    font-size: 1.75rem;
    font-weight: 850;
    letter-spacing: -0.045em;
    line-height: 1.1;
}

.decision-explanation {
    color: #555555;
    line-height: 1.45;
    margin-top: 0.45rem;
    max-width: 720px;
}

.evidence-badge {
    background: #F4F6FA;
    border: 1px solid #DEE3EC;
    border-radius: 999px;
    color: #525A67;
    font-size: 0.72rem;
    font-weight: 750;
    line-height: 1.3;
    padding: 0.45rem 0.72rem;
    white-space: nowrap;
}

.decision-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1rem;
    padding-top: 1rem;
}

.decision-column {
    background: #FAFAFA;
    border-radius: 12px;
    padding: 0.85rem 0.9rem;
}

.decision-column h4 {
    color: var(--ink);
    font-size: 0.92rem;
    margin: 0 0 0.45rem 0;
}

.decision-column ul {
    margin: 0;
    padding-left: 1.05rem;
}

.decision-column li {
    color: #505050;
    font-size: 0.81rem;
    line-height: 1.45;
    margin-bottom: 0.38rem;
}

.decision-caveat {
    color: #6B6B6B;
    font-size: 0.76rem;
    line-height: 1.45;
    margin-top: 0.9rem;
}

.run-record-card {
    border: 1px solid var(--line);
    border-radius: 16px;
    background: #FFFFFF;
    padding: 1.1rem 1.2rem;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
}

.run-record-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.95rem;
}

.run-complete-dot {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    color: #FFFFFF;
    background: var(--ebay-green);
    font-weight: 850;
}

.run-record-subtitle {
    color: #6A6A6A;
    font-size: 0.8rem;
    margin-top: 0.15rem;
}

.run-detail-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.65rem;
}

.run-detail-item {
    background: #F7F7F7;
    border-radius: 10px;
    padding: 0.72rem 0.78rem;
}

.run-detail-label {
    color: #777777;
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.055em;
    text-transform: uppercase;
    margin-bottom: 0.25rem;
}

.run-detail-value {
    color: var(--ink);
    font-size: 0.8rem;
    font-weight: 700;
    line-height: 1.35;
}

@media (max-width: 900px) {
    .decision-summary-top {
        flex-direction: column;
    }

    .evidence-badge {
        white-space: normal;
    }

    .decision-grid,
    .run-detail-grid {
        grid-template-columns: 1fr;
    }

    [data-testid="stAppViewContainer"] .block-container {
        padding-top: 4.25rem !important;
    }
}

[data-testid="stSidebar"] {
    background: #F4F5F7;
    border-right: 1px solid #E2E3E5;
    min-width: 302px;
    max-width: 302px;
}

[data-testid="stSidebarContent"] {
    padding: 2rem 1.1rem 2rem 1.1rem;
}

[data-testid="stSidebar"] .stButton > button {
    width: 100%;
}

.ebay-brand {
    margin: 0 0 1.25rem 0;
}

.ebay-brand-row {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    margin-bottom: 0.35rem;
}

.ebay-dots {
    display: flex;
    gap: 0.22rem;
    align-items: center;
}

.ebay-dot {
    width: 11px;
    height: 11px;
    border-radius: 50%;
    display: inline-block;
}

.ebay-word {
    color: var(--ebay-blue);
    font-size: 1.05rem;
    font-weight: 800;
    letter-spacing: -0.04em;
}

.ebay-product-name {
    font-size: 1.22rem;
    font-weight: 800;
    line-height: 1.15;
    letter-spacing: -0.03em;
    margin: 0;
}

.ebay-prototype-note {
    margin-top: 0.35rem;
    color: #767676;
    font-size: 0.72rem;
    line-height: 1.35;
}

.pipeline-banner {
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 0.75rem 0.95rem;
    margin-bottom: 1.2rem;
    background: #FFFFFF;
    font-weight: 650;
    font-size: 0.9rem;
}

.pipeline-banner.success {
    border-left: 5px solid var(--ebay-green);
}

.pipeline-banner.ready {
    border-left: 5px solid var(--ebay-blue);
}

.launch-header {
    margin: 0.15rem 0 1.35rem 0;
}

.launch-kicker {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    color: var(--ebay-blue);
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.65rem;
}

.launch-title {
    color: var(--ink);
    font-size: clamp(2.15rem, 4vw, 3.65rem);
    line-height: 0.98;
    letter-spacing: -0.065em;
    font-weight: 850;
    margin: 0;
    max-width: 1000px;
}

.launch-subtitle {
    margin: 0.9rem 0 0 0;
    color: #676767;
    font-size: 1.02rem;
    line-height: 1.55;
    max-width: 920px;
}

.four-color-rule {
    height: 5px;
    width: 100%;
    border-radius: 999px;
    margin: 1rem 0 1.3rem 0;
    background: linear-gradient(
        90deg,
        var(--ebay-red) 0 25%,
        var(--ebay-blue) 25% 50%,
        var(--ebay-yellow) 50% 75%,
        var(--ebay-green) 75% 100%
    );
}

.launch-meta-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.75rem;
    margin-bottom: 1.2rem;
}

.launch-meta-card,
.soft-card,
.insight-card,
.governance-card,
.pipeline-card {
    border: 1px solid var(--line);
    border-radius: 16px;
    background: #FFFFFF;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.035);
}

.launch-meta-card {
    padding: 0.95rem 1rem;
}

.meta-label {
    color: #777777;
    font-size: 0.72rem;
    font-weight: 700;
    margin-bottom: 0.32rem;
    text-transform: uppercase;
    letter-spacing: 0.055em;
}

.meta-value {
    color: var(--ink);
    font-size: 0.98rem;
    font-weight: 750;
    line-height: 1.35;
}

.soft-card {
    padding: 1.2rem 1.25rem;
    height: 100%;
}

.soft-card h3,
.insight-card h3,
.governance-card h3,
.pipeline-card h3 {
    color: var(--ink);
    margin: 0 0 0.55rem 0;
    font-size: 1.15rem;
    letter-spacing: -0.025em;
}

.soft-card p,
.insight-card p,
.governance-card p {
    color: #4F4F4F;
    line-height: 1.55;
}

.pipeline-card {
    padding: 1.15rem 1.2rem;
    background: #F7F7F7;
}

.pipeline-step {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.48rem 0;
    color: #303030;
    font-size: 0.9rem;
}

.pipeline-step-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 27px;
    height: 27px;
    border-radius: 50%;
    color: #FFFFFF;
    background: var(--ebay-blue);
    font-size: 0.72rem;
    font-weight: 800;
}

.pipeline-step.done .pipeline-step-number {
    background: var(--ebay-green);
}

.section-title {
    margin: 2.1rem 0 0.75rem 0;
    font-size: 1.7rem;
    font-weight: 820;
    letter-spacing: -0.045em;
    color: var(--ink);
}

.section-caption {
    color: #6F6F6F;
    margin-bottom: 1rem;
}

.insight-card,
.governance-card {
    padding: 1.2rem 1.25rem;
    margin-bottom: 0.9rem;
}

.insight-card {
    border-top: 5px solid var(--ebay-blue);
}

.governance-card.approve {
    border-left: 6px solid var(--ebay-green);
}

.governance-card.revise {
    border-left: 6px solid var(--ebay-yellow);
}

.governance-card.reject {
    border-left: 6px solid var(--ebay-red);
}

.status-pill {
    display: inline-block;
    border-radius: 999px;
    padding: 0.28rem 0.62rem;
    font-size: 0.72rem;
    font-weight: 800;
    margin-right: 0.35rem;
    margin-bottom: 0.35rem;
    background: #EEF3FF;
    color: #1D4ED8;
}

.status-pill.green {
    background: #EEF7E7;
    color: #4C7900;
}

.status-pill.yellow {
    background: #FFF5D9;
    color: #8A6500;
}

.status-pill.red {
    background: #FFF0F0;
    color: #B42318;
}

.source-note {
    padding: 0.9rem 1rem;
    border-radius: 12px;
    background: #F7F7F7;
    color: #5E5E5E;
    font-size: 0.83rem;
    line-height: 1.5;
    border: 1px solid #E2E2E2;
}

.metric-card {
    height: 100%;
    min-height: 168px;
    border: 1px solid var(--line);
    border-top: 5px solid var(--ebay-blue);
    border-radius: 15px;
    background: #FFFFFF;
    padding: 1rem 1.05rem;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
}

.metric-card.green { border-top-color: var(--ebay-green); }
.metric-card.red { border-top-color: var(--ebay-red); }
.metric-card.yellow { border-top-color: var(--ebay-yellow); }
.metric-card.blue { border-top-color: var(--ebay-blue); }

.metric-card-label {
    color: #6F6F6F;
    font-size: 0.82rem;
    font-weight: 700;
    margin-bottom: 0.35rem;
}

.metric-card-value {
    color: var(--ink);
    font-size: 2rem;
    font-weight: 820;
    letter-spacing: -0.05em;
    line-height: 1.05;
    margin-bottom: 0.65rem;
}

.metric-card-description {
    color: #626262;
    font-size: 0.82rem;
    line-height: 1.42;
}

.segment-card-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.7rem;
}

.segment-card {
    border: 1px solid var(--line);
    border-left: 5px solid var(--ebay-blue);
    border-radius: 13px;
    background: #FFFFFF;
    padding: 0.9rem 0.95rem;
    min-height: 152px;
}

.segment-card-title {
    color: var(--ink);
    font-size: 0.98rem;
    font-weight: 800;
    line-height: 1.25;
    margin-bottom: 0.35rem;
}

.segment-card-meta {
    color: #6B6B6B;
    font-size: 0.75rem;
    line-height: 1.35;
    margin-bottom: 0.55rem;
}

.segment-card-theme,
.segment-card-need {
    color: #4F4F4F;
    font-size: 0.8rem;
    line-height: 1.42;
    margin-top: 0.35rem;
}

[data-testid="stMetric"] {
    border: 1px solid var(--line);
    border-radius: 14px;
    background: #FFFFFF;
    padding: 0.9rem 1rem;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
}

[data-testid="stMetricLabel"] {
    color: #6F6F6F;
}

[data-testid="stMetricValue"] {
    color: var(--ink);
    letter-spacing: -0.04em;
}

.stButton > button {
    min-height: 2.8rem;
    border-radius: 24px;
    font-weight: 750;
    border: 1px solid #AFAFAF;
    background: #FFFFFF;
    color: var(--ink);
}

.stButton > button[kind="primary"] {
    background: var(--ebay-blue);
    color: white;
    border: 1px solid var(--ebay-blue);
}

.stButton > button:hover {
    border-color: var(--ebay-blue);
    color: var(--ebay-blue);
}

.stButton > button[kind="primary"]:hover {
    color: white;
    background: #2854D9;
}

[data-baseweb="select"] > div,
[data-baseweb="input"] > div,
[data-testid="stTextArea"] textarea,
[data-testid="stDateInput"] > div > div {
    border-radius: 10px !important;
}

[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 1rem;
    border-bottom: 1px solid #D7D7D7;
}

[data-testid="stTabs"] [data-baseweb="tab"] {
    height: 3rem;
    padding-left: 0;
    padding-right: 0;
    color: #4E4E4E;
    font-weight: 700;
}

[data-testid="stTabs"] [aria-selected="true"] {
    color: var(--ebay-blue);
}

[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px;
}

[data-testid="stDataFrame"] {
    border: 1px solid #E0E0E0;
    border-radius: 12px;
    overflow: hidden;
}

h1, h2, h3 {
    color: var(--ink);
    letter-spacing: -0.035em;
}

hr {
    border-color: #E1E1E1;
}

@media (max-width: 900px) {
    .launch-meta-grid,
    .segment-card-grid {
        grid-template-columns: 1fr 1fr;
    }

    .metric-card {
        min-height: 145px;
    }

    [data-testid="stSidebar"] {
        min-width: auto;
        max-width: none;
    }
}
</style>
"""


def apply_ebay_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def render_sidebar_brand() -> None:
    st.markdown(
        """
        <div class="ebay-brand">
            <div class="ebay-brand-row">
                <div class="ebay-dots">
                    <span class="ebay-dot" style="background:#E53238"></span>
                    <span class="ebay-dot" style="background:#3665F3"></span>
                    <span class="ebay-dot" style="background:#F5AF02"></span>
                    <span class="ebay-dot" style="background:#86B817"></span>
                </div>
                <span class="ebay-word">eBay</span>
            </div>
            <p class="ebay-product-name">PMM Co-Pilot</p>
            <div class="ebay-prototype-note">
                Independent portfolio prototype. Not an official eBay product.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_launch_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="launch-header">
            <div class="launch-kicker">
                <span class="ebay-dots">
                    <span class="ebay-dot" style="background:#E53238"></span>
                    <span class="ebay-dot" style="background:#3665F3"></span>
                    <span class="ebay-dot" style="background:#F5AF02"></span>
                    <span class="ebay-dot" style="background:#86B817"></span>
                </span>
                PMM decision intelligence
            </div>
            <h1 class="launch-title">{html.escape(title)}</h1>
            <p class="launch-subtitle">{html.escape(subtitle)}</p>
            <div class="four-color-rule"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pipeline_banner(complete: bool) -> None:
    if complete:
        text = "✓ Pipeline run complete — intelligence and governance results are ready"
        css_class = "success"
    else:
        text = "Ready to run — one click collects signals, generates intelligence, and completes governance review"
        css_class = "ready"

    st.markdown(
        f'<div class="pipeline-banner {css_class}">{html.escape(text)}</div>',
        unsafe_allow_html=True,
    )
