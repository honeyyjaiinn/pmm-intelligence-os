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
    font-size: clamp(2.15rem, 5vw, 3.65rem);
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


def apply_ui() -> None:
    """Apply presentation styling without changing product logic."""
    st.html(CSS)
    st.html(HERO)
