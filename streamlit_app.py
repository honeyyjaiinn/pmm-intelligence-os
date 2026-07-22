from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.multipage import (
    initialize_state,
    render_agent_configuration,
    render_customer_intelligence,
    render_evidence,
    render_governance,
    render_overview,
    render_signal_hub,
)
from src.ui import apply_global_styles


PROJECT_ROOT = Path(__file__).parent
load_dotenv(
    dotenv_path=PROJECT_ROOT / ".env"
)

st.set_page_config(
    page_title="PMM Intelligence OS",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_global_styles()
initialize_state()


def require_access_code() -> None:
    expected_code = os.getenv(
        "APP_PASSWORD",
        "",
    ).strip()

    if not expected_code:
        return

    if st.session_state.get(
        "authenticated"
    ):
        return

    st.markdown(
        "## Private portfolio demonstration"
    )

    entered_code = st.text_input(
        "Access code",
        type="password",
    )

    if st.button(
        "Open dashboard",
        type="primary",
    ):
        if entered_code == expected_code:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error(
                "Incorrect access code."
            )

    st.stop()


# require_access_code()


pages = {
    "PMM WORKFLOW": [
        st.Page(
            render_overview,
            title="Start Here",
            icon=":material/home:",
            default=True,
        ),
        st.Page(
            render_signal_hub,
            title="1. Prepare Evidence",
            icon=":material/database:",
        ),
        st.Page(
            render_customer_intelligence,
            title="2. Generate Intelligence",
            icon=":material/psychology:",
        ),
        st.Page(
            render_governance,
            title="3. Review Recommendation",
            icon=":material/fact_check:",
        ),
        st.Page(
            render_evidence,
            title="4. Evidence & Audit",
            icon=":material/manage_search:",
        ),
    ],
    "CONTROL PLANE": [
        st.Page(
            render_agent_configuration,
            title="Agent Configuration",
            icon=":material/tune:",
        ),
    ],
}

current_page = st.navigation(pages)


with st.sidebar:
    st.divider()
    st.markdown("### Launch context")

    st.text_input(
        "Product",
        key="product_name",
    )
    st.text_input(
        "Launch goal",
        key="launch_goal",
    )
    st.text_input(
        "Target market",
        key="target_market",
    )




current_page.run()
