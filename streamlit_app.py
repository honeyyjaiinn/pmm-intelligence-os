from __future__ import annotations

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.dashboard import (
    initialize_dashboard_state,
    render_dashboard,
    render_new_launch_form,
    render_sidebar,
    run_full_pipeline,
)
from src.ebay_ui import apply_ebay_styles


PROJECT_ROOT = Path(__file__).parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

st.set_page_config(
    page_title="PMM Co-Pilot",
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_ebay_styles()
initialize_dashboard_state()
render_sidebar()

if st.session_state.pipeline_requested:
    run_full_pipeline()

if st.session_state.show_new_launch_form:
    render_new_launch_form()
else:
    render_dashboard()
