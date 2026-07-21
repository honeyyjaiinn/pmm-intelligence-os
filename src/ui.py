from __future__ import annotations

import streamlit as st


CSS = """
<style>
.block-container {
    max-width: 1320px;
    padding-top: 4.5rem;
    padding-bottom: 4rem;
}

[data-testid="stSidebar"] {
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

[data-testid="stSidebarContent"] {
    padding-top: 4.5rem;
}

[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    letter-spacing: -0.02em;
}

.pmm-hero {
    padding: 2rem 2.2rem;
    margin-bottom: 1.4rem;
    border-radius: 22px;
    border: 1px solid rgba(255, 255, 255, 0.10);
    background:
        radial-gradient(
            circle at top right,
            rgba(244, 91, 105, 0.20),
            transparent 32%
        ),
        linear-gradient(
            135deg,
            rgba(25, 35, 59, 0.97),
            rgba(11, 17, 32, 0.98)
        );
    box-shadow: 0 18px 60px rgba(0, 0, 0, 0.28);
}

.pmm-eyebrow {
    color: #FF8E99;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    margin-bottom: 0.55rem;
}

.pmm-title {
    color: #FFFFFF;
    font-size: clamp(1.9rem, 4vw, 3rem);
    line-height: 1.03;
    letter-spacing: -0.055em;
    font-weight: 780;
    margin: 0;
}

.pmm-subtitle {
    color: #B8C1D5;
    max-width: 820px;
    font-size: 1.02rem;
    line-height: 1.65;
    margin-top: 0.9rem;
    margin-bottom: 1.2rem;
}

.pmm-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
}

.pmm-badge {
    display: inline-block;
    padding: 0.38rem 0.72rem;
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    background: rgba(255, 255, 255, 0.06);
    color: #D7DDEC;
    font-size: 0.78rem;
    font-weight: 600;
}

[data-testid="stMetric"] {
    padding: 1rem 1.1rem;
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 16px;
    background: rgba(19, 27, 46, 0.82);
    box-shadow: 0 10px 32px rgba(0, 0, 0, 0.16);
}

[data-testid="stMetricLabel"] {
    color: #99A5BC;
}

[data-testid="stMetricValue"] {
    letter-spacing: -0.035em;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 18px;
    border-color: rgba(255, 255, 255, 0.10);
    background: rgba(17, 24, 42, 0.72);
    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.14);
}

.stButton > button {
    min-height: 2.8rem;
    border-radius: 12px;
    font-weight: 700;
    border: 0;
    box-shadow: 0 8px 25px rgba(244, 91, 105, 0.20);
}

[data-baseweb="input"] > div,
[data-baseweb="select"] > div {
    border-radius: 11px;
}

[data-testid="stExpander"] {
    border-radius: 13px;
    border-color: rgba(255, 255, 255, 0.08);
    background: rgba(13, 20, 35, 0.55);
}

[data-testid="stDataFrame"] {
    border-radius: 13px;
    overflow: hidden;
}

h1,
h2,
h3 {
    letter-spacing: -0.035em;
}

h2 {
    margin-top: 2.4rem !important;
}

hr {
    border-color: rgba(255, 255, 255, 0.08);
}

/* Multipage content typography */
[data-testid="stMainBlockContainer"] h2 {
    font-size: 1.8rem !important;
    line-height: 1.2 !important;
    margin-bottom: 1rem !important;
}

/* Workflow-card headings */
[data-testid="stMainBlockContainer"]
[data-testid="stVerticalBlockBorderWrapper"] h3 {
    font-size: 1.15rem !important;
    line-height: 1.28 !important;
    letter-spacing: -0.02em !important;
    margin-top: 0 !important;
    margin-bottom: 0.55rem !important;
}

/* Workflow-card descriptions */
[data-testid="stMainBlockContainer"]
[data-testid="stVerticalBlockBorderWrapper"] p {
    font-size: 0.91rem !important;
    line-height: 1.5 !important;
    margin-bottom: 0 !important;
}

/* Sidebar section headings */
[data-testid="stSidebar"] h3 {
    font-size: 1.05rem !important;
    line-height: 1.25 !important;
}


/* Overview multipage cards */
.overview-section {
    margin-top: 2.2rem;
}

.overview-heading {
    margin: 0 0 1rem 0;
    font-size: 1.65rem;
    line-height: 1.2;
    letter-spacing: -0.035em;
    color: #F5F7FA;
}

.workflow-grid,
.launch-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1rem;
    align-items: stretch;
}

.workflow-card {
    min-height: 150px;
    height: 100%;
    padding: 1.15rem 1.2rem;
    border-radius: 15px;
    border: 1px solid rgba(255, 255, 255, 0.13);
    background: rgba(12, 18, 32, 0.72);
    box-sizing: border-box;
}

.workflow-step {
    margin-bottom: 0.45rem;
    color: #FF8792;
    font-size: 0.7rem;
    font-weight: 750;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.workflow-card h3 {
    margin: 0 0 0.55rem 0;
    color: #F7F8FC;
    font-size: 1.12rem;
    line-height: 1.25;
    letter-spacing: -0.025em;
}

.workflow-card p {
    margin: 0;
    color: #BAC3D6;
    font-size: 0.87rem;
    line-height: 1.5;
}

.launch-section {
    margin-top: 2.6rem;
}

.launch-card {
    min-height: 105px;
    padding: 1.1rem 1.15rem;
    border-radius: 15px;
    border: 1px solid rgba(255, 255, 255, 0.09);
    background: rgba(20, 29, 50, 0.85);
    box-sizing: border-box;
}

.launch-label {
    margin-bottom: 0.45rem;
    color: #98A5BC;
    font-size: 0.73rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}

.launch-value {
    color: #F5F7FA;
    font-size: 1.18rem;
    line-height: 1.3;
    font-weight: 650;
    letter-spacing: -0.025em;
    overflow-wrap: anywhere;
}

@media (max-width: 900px) {
    .workflow-grid,
    .launch-grid {
        grid-template-columns: 1fr;
    }

    .workflow-card,
    .launch-card {
        min-height: auto;
    }
}

</style>
"""


HERO = """
<section class="pmm-hero">
<div class="pmm-eyebrow">Product Marketing Decision Intelligence</div>
<h1 class="pmm-title">PMM Intelligence OS</h1>
<p class="pmm-subtitle">Transform fragmented customer, competitive, organizational, and product-risk signals into evidence-backed Product Marketing recommendations—with governance and human oversight built in.</p>
<div class="pmm-badges">
<span class="pmm-badge">Voice of Customer</span>
<span class="pmm-badge">Competitive Intelligence</span>
<span class="pmm-badge">Evidence Traceability</span>
<span class="pmm-badge">GenAI Synthesis</span>
<span class="pmm-badge">Governance Review</span>
<span class="pmm-badge">Human in the Loop</span>
</div>
</section>
"""


def apply_global_styles() -> None:
    """Apply shared CSS without displaying the homepage hero."""
    st.html(CSS)


def render_hero() -> None:
    """Display the hero only on the Overview page."""
    st.html(HERO)


def apply_ui() -> None:
    """Keep app_v4.py working."""
    apply_global_styles()
    render_hero()
