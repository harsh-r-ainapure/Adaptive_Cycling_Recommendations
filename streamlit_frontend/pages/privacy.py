import streamlit as st
import sys
from pathlib import Path
import importlib.util

# Add parent directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import styles

st.set_page_config(
    page_title="Privacy Protocol - Adaptive Cycling Coach",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply engineering telemetry styling
styles.apply_custom_css()

# Sidebar Navigation
with st.sidebar:
    st.markdown("""
        <div style="border-bottom: 1px solid #161D2B; padding-bottom: 16px; margin-bottom: 16px;">
            <div style="display: flex; align-items: baseline; gap: 8px;">
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; color: #FF4B00;">ACC</span>
                <span style="font-size: 0.88rem; font-weight: 600; color: #F8FAFC; letter-spacing: -0.01em;">TELEMETRY</span>
            </div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: #64748B; margin-top: 3px;">
                ENGINE: RF-PHYSIOLOGY v2.4
            </div>
        </div>
        <div style="margin-bottom: 16px;">
            <span class="tech-tag">DIRECT ROUTE // /privacy</span>
        </div>
    """, unsafe_allow_html=True)

    st.page_link("app.py", label="Return to Overview Console")

    st.sidebar.divider()
    st.sidebar.caption("Adaptive Cycling Coach // Privacy Protocol")

# Render Privacy Protocol view from parent privacy module
spec = importlib.util.spec_from_file_location("privacy_backend_mod", root_dir / "privacy.py")
if spec and spec.loader:
    privacy_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(privacy_mod)
    privacy_mod.show_privacy_page()
