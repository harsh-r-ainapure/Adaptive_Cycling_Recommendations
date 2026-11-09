import streamlit as st
from pathlib import Path

def show_homepage():
    user_name = st.session_state.get("user_name") or "Harsh"
    jwt = st.session_state.get("jwt")
    is_connected = bool(jwt)

    # Top Header Bar: Status & Logout
    top_col1, top_col2 = st.columns([6, 2])
    with top_col1:
        if is_connected:
            st.markdown(
                '<div style="display: flex; align-items: center; gap: 8px; margin-top: 6px;">'
                '<span class="status-pill online">● Intervals.icu Connected</span>'
                '</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="display: flex; align-items: center; gap: 8px; margin-top: 6px;">'
                '<span class="status-pill offline">○ No Account Connected</span>'
                '</div>',
                unsafe_allow_html=True
            )
    with top_col2:
        if is_connected:
            if st.button("Sign Out", use_container_width=True):
                st.session_state["jwt"] = None
                st.success("Signed out successfully.")
                st.rerun()
        else:
            if st.button("Reset Session", use_container_width=True):
                st.session_state["jwt"] = None
                st.info("Session reset.")
                st.rerun()

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Hero Banner
    hero_col_text, hero_col_logo = st.columns([3, 1])
    with hero_col_text:
        st.markdown(f"""
        <div class="hero-banner">
            <span class="badge-primary">AI-Powered Cycling Intelligence</span>
            <h1 class="hero-title" style="margin-top: 12px;">Welcome back, {user_name}!</h1>
            <p class="hero-subtitle">
                Adaptive training intelligence driven by machine learning and physiological fatigue modeling.
                Analyze your ride dynamics, track capacity deviations, and unlock personalized training recommendations.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with hero_col_logo:
        BASE_DIR = Path(__file__).parent
        logo_path = BASE_DIR / "stravalogo.png"
        if logo_path.exists():
            st.markdown('<div style="text-align: center; padding-top: 20px;">', unsafe_allow_html=True)
            st.image(str(logo_path), caption="Powered by Intervals & Strava", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # Section Title
    st.markdown("""
        <div class="section-title">
            <span>⚡ Quick Modules</span>
        </div>
        <div class="section-subtitle">
            Choose an action to manage your data, configure your baseline, or view AI insights.
        </div>
    """, unsafe_allow_html=True)

    # Module Cards Grid (2x2)
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div class="feature-icon" style="background: rgba(252, 76, 2, 0.15); color: #FC4C02;">🚴</div>
                <h3 style="margin: 0 0 8px 0; font-size: 1.15rem; font-weight: 700; color: #F8FAFC;">Adaptive Cycling Coach</h3>
                <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.4; margin-bottom: 16px;">
                    Review your baseline comparison, recommended distance, elevation targets, 6-month fatigue curves, and RF power predictions.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Coach Dashboard ➔", key="nav_coach", use_container_width=True):
            st.session_state["selected_page"] = "Adaptive Cycling Coach"
            st.rerun()

    with row1_col2:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div class="feature-icon" style="background: rgba(16, 185, 129, 0.15); color: #10B981;">🔄</div>
                <h3 style="margin: 0 0 8px 0; font-size: 1.15rem; font-weight: 700; color: #F8FAFC;">Sync Activities</h3>
                <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.4; margin-bottom: 16px;">
                    Connect Intervals.icu and OAuth providers to synchronize your latest workouts and trigger feature extraction pipeline.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Sync Activities ➔", key="nav_sync", use_container_width=True):
            st.session_state["selected_page"] = "Sync"
            st.rerun()

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div class="feature-icon" style="background: rgba(56, 189, 248, 0.15); color: #38BDF8;">⚙️</div>
                <h3 style="margin: 0 0 8px 0; font-size: 1.15rem; font-weight: 700; color: #F8FAFC;">Rider Setup Form</h3>
                <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.4; margin-bottom: 16px;">
                    Calibrate your athlete profile, power meter availability, and historical date tracking for accurate baseline metrics.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Edit Profile & Setup ➔", key="nav_form", use_container_width=True):
            st.session_state["selected_page"] = "Setup Form"
            st.rerun()

    with row2_col2:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div class="feature-icon" style="background: rgba(168, 85, 247, 0.15); color: #A855F7;">💡</div>
                <h3 style="margin: 0 0 8px 0; font-size: 1.15rem; font-weight: 700; color: #F8FAFC;">Methodology & Science</h3>
                <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.4; margin-bottom: 16px;">
                    Learn how the machine learning fatigue algorithm, capacity deviation, and predictive modeling optimize athlete readiness.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Learn More About System ➔", key="nav_about", use_container_width=True):
            st.session_state["selected_page"] = "About"
            st.rerun()

    st.divider()

    # Quick Feature Highlights Ribbon
    hl_col1, hl_col2, hl_col3 = st.columns(3)
    with hl_col1:
        st.markdown("""
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 14px;">
            <div style="font-weight: 700; color: #F1F5F9; font-size: 0.9rem;">📈 Fatigue Tracking</div>
            <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 4px;">6-month rolling fatigue modeling computed from normalized effort.</div>
        </div>
        """, unsafe_allow_html=True)
    with hl_col2:
        st.markdown("""
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 14px;">
            <div style="font-weight: 700; color: #F1F5F9; font-size: 0.9rem;">🎯 Next-Ride Targets</div>
            <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 4px;">Dynamic volume, climb, and heart rate targets adapted to current state.</div>
        </div>
        """, unsafe_allow_html=True)
    with hl_col3:
        st.markdown("""
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 14px;">
            <div style="font-weight: 700; color: #F1F5F9; font-size: 0.9rem;">🤖 RF Power Predictions</div>
            <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 4px;">Machine learning estimated power compared directly with actual ride output.</div>
        </div>
        """, unsafe_allow_html=True)
