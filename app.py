from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
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

load_dotenv()
BASE_DIR = Path(__file__).parent

st.set_page_config(
    page_title="PMM Intelligence OS",
    page_icon="🧭",
    layout="wide",
)

st.title("PMM Intelligence OS")
st.caption("Evidence-backed customer and market intelligence for product marketers.")

with st.sidebar:
    st.header("Launch context")
    product_name = st.text_input("Product", "AI Seller Assistant")
    launch_goal = st.text_input("Launch goal", "Increase seller adoption")
    target_market = st.text_input("Target market", "US marketplace")

    st.header("Signal connectors")
    use_reviews = st.checkbox("Sample app reviews", True)
    use_interviews = st.checkbox("Sample customer interviews", True)
    use_support = st.checkbox("Sample support tickets", True)
    use_past_launches = st.checkbox("Sample past launch learnings", True)
    use_cpsc = st.checkbox("CPSC recalls", False)
    use_reddit = st.checkbox("Reddit API", False)
    use_news = st.checkbox("NewsAPI", False)

    cpsc_query = st.text_input("CPSC product filter", "battery")
    subreddit = st.text_input("Subreddit", "Ebay")
    reddit_query = st.text_input("Reddit search", "seller listing")
    news_query = st.text_input("News search", "ecommerce seller AI")

    run = st.button("Generate intelligence", type="primary", use_container_width=True)

if not run:
    st.info("Select signal sources and click **Generate intelligence**.")
    st.stop()

signals = []
errors = []

def add_csv(filename: str, source: str, source_type: str):
    connector = CSVConnector(BASE_DIR / "sample_data" / filename, source, source_type)
    signals.extend(connector.fetch())

if use_reviews:
    add_csv("app_reviews.csv", "App reviews (sample)", "app_review")
if use_interviews:
    add_csv("interviews.csv", "Customer interviews (sample)", "interview")
if use_support:
    add_csv("support_tickets.csv", "Support tickets (sample)", "support")
if use_past_launches:
    add_csv("past_launches.csv", "Past launches (sample)", "organizational_knowledge")

if use_cpsc:
    try:
        signals.extend(CPSCRecallConnector().fetch(product_name=cpsc_query, limit=30))
    except Exception as exc:
        errors.append(f"CPSC: {exc}")

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
        errors.append(f"Reddit: {exc}")

if use_news:
    try:
        signals.extend(NewsAPIConnector().fetch(query=news_query, limit=25))
    except Exception as exc:
        errors.append(f"NewsAPI: {exc}")

if errors:
    for error in errors:
        st.warning(error)

records = [signal.to_dict() for signal in signals]
frame = normalize_signals(records)
evidence = extract_theme_evidence(frame)
summary = summarize_themes(evidence)
cards = build_decision_cards(summary)

if frame.empty:
    st.error("No usable signals were returned.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Signals analyzed", len(frame))
c2.metric("Source types", frame["source_type"].nunique())
c3.metric("Themes detected", summary["theme"].nunique() if not summary.empty else 0)
c4.metric("Top confidence", f"{summary.iloc[0]['confidence']}%" if not summary.empty else "—")

st.subheader("Decision intelligence")
st.caption(
    f"Launch: **{product_name}** · Goal: **{launch_goal}** · Market: **{target_market}**"
)

if not cards:
    st.warning("No configured theme matched the current data.")
else:
    for card in cards:
        with st.container(border=True):
            left, right = st.columns([4, 1])
            with left:
                st.markdown(f"### {card['theme']}")
                st.markdown(f"**Recommendation:** {card['decision']}")
                st.markdown(f"**Next action:** {card['next_action']}")
                st.markdown(f"**Guardrail:** {card['risk']}")
            with right:
                st.metric("Confidence", f"{card['confidence']}%")
                st.metric("Evidence", f"{card['mentions']} signals")
                st.metric("Source diversity", card["source_types"])

            matching = evidence[evidence["theme"] == card["theme"]].head(5)
            with st.expander("View supporting evidence"):
                st.dataframe(
                    matching[["source", "source_type", "text", "url"]],
                    use_container_width=True,
                    hide_index=True,
                )

st.subheader("Cross-source theme summary")
if summary.empty:
    st.write("No themes detected.")
else:
    st.bar_chart(summary.set_index("theme")["mentions"])
    st.dataframe(summary, use_container_width=True, hide_index=True)

with st.expander("Normalized signal store"):
    st.dataframe(
        frame[["source", "source_type", "created_at", "rating", "text", "url"]],
        use_container_width=True,
        hide_index=True,
    )

st.caption(
    "Confidence is a transparent prototype heuristic based on evidence volume and "
    "source diversity; it is not a statistical probability."
)
