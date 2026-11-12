import streamlit as st
from pathlib import Path

def show_homepage():
    user_name = st.session_state.get("user_name") or "Harsh"
    jwt = st.session_state.get("jwt")
    is_connected = bool(jwt)

    # Top Telemetry Status Header
    hud_c1, hud_c2 = st.columns([7, 2])
    with hud_c1:
        status_tag = '<span class="tech-tag live">LINKED // INTERVALS.ICU</span>' if is_connected else '<span class="tech-tag">UNLINKED // INTERVALS.ICU</span>'
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 12px; margin-top: 4px;">
            <span class="tech-tag">ATHLETE: {user_name.upper()}</span>
            {status_tag}
            <span class="tech-tag">ENGINE: RF-PREDICTIVE</span>
        </div>
        """, unsafe_allow_html=True)
    with hud_c2:
        if is_connected:
            if st.button("Disconnect Session", use_container_width=True):
                st.session_state["jwt"] = None
                st.rerun()
        else:
            if st.button("Reset Session State", use_container_width=True):
                st.session_state["jwt"] = None
                st.rerun()

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Minimalist Header Section
    header_col, logo_col = st.columns([5, 1])
    with header_col:
        st.markdown("""
        <div style="border-left: 2px solid #FF4B00; padding-left: 18px; margin-bottom: 28px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; letter-spacing: 0.12em; color: #FF4B00; text-transform: uppercase;">
                ENDURANCE TELEMETRY PLATFORM
            </div>
            <h1 style="font-size: 2.2rem; font-weight: 700; color: #F8FAFC; margin: 6px 0 8px 0; letter-spacing: -0.02em;">
                Adaptive Cycling Intelligence
            </h1>
            <p style="color: #7A889B; font-size: 0.92rem; max-width: 680px; margin: 0; line-height: 1.5;">
                Physiological fatigue modeling and machine-learned capacity reconstitution. Select an operational module below to inspect telemetry or trigger activity ingestion.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with logo_col:
        BASE_DIR = Path(__file__).parent
        logo_path = BASE_DIR / "stravalogo-300x300.png"
        if not logo_path.exists():
            logo_path = BASE_DIR / "stravalogo.png"
        if logo_path.exists():
            st.image(str(logo_path), caption="Integration: Intervals & Strava", use_container_width=True)

    # Modular Workspace Grid
    st.markdown("""
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; letter-spacing: 0.08em; color: #64748B; text-transform: uppercase; margin-bottom: 12px;">
        OPERATIONAL MODULES
    </div>
    """, unsafe_allow_html=True)

    m1, m2 = st.columns(2, gap="medium")

    with m1:
        st.markdown("""
        <div class="telemetry-panel" style="margin-bottom: 12px; height: 160px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 600; color: #F8FAFC; font-size: 1rem;">Work Capacity & Recovery Coach</span>
                    <span class="tech-tag active">CORE</span>
                </div>
                <p style="color: #7A889B; font-size: 0.82rem; line-height: 1.45; margin: 0;">
                    Inspect rolling fatigue decay curves, baseline variance, and target prescriptions (distance, elevation, and heart rate caps) for upcoming training sessions.
                </p>
            </div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #64748B;">
                STATUS: READY // 3 TELEMETRY TRACKS
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Launch Coach Terminal", key="btn_coach", type="primary", use_container_width=True):
            st.session_state["selected_page"] = "Adaptive Cycling Coach"
            st.rerun()

    with m2:
        st.markdown("""
        <div class="telemetry-panel" style="margin-bottom: 12px; height: 160px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 600; color: #F8FAFC; font-size: 1rem;">Data Pipeline & Activity Sync</span>
                    <span class="tech-tag">INGEST</span>
                </div>
                <p style="color: #7A889B; font-size: 0.82rem; line-height: 1.45; margin: 0;">
                    Authenticate with Intervals.icu to fetch raw workout streams, sensor channels, and power streams for feature extraction.
                </p>
            </div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #64748B;">
                PROTOCOL: OAUTH2 // REST INGESTION
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Ingestion Hub", key="btn_sync", use_container_width=True):
            st.session_state["selected_page"] = "Sync"
            st.rerun()

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    m3, m4 = st.columns(2, gap="medium")

    with m3:
        st.markdown("""
        <div class="telemetry-panel" style="margin-bottom: 12px; height: 160px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 600; color: #F8FAFC; font-size: 1rem;">Athlete Calibration & Sensors</span>
                    <span class="tech-tag">CALIBRATE</span>
                </div>
                <p style="color: #7A889B; font-size: 0.82rem; line-height: 1.45; margin: 0;">
                    Configure power meter hardware availability, installation timestamp, and athlete profile specifications for clean ML baseline labeling.
                </p>
            </div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #64748B;">
                HARDWARE: STRAIN GAUGE CONFIG
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Calibrate Parameters", key="btn_form", use_container_width=True):
            st.session_state["selected_page"] = "Setup Form"
            st.rerun()

    with m4:
        st.markdown("""
        <div class="telemetry-panel" style="margin-bottom: 12px; height: 160px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 600; color: #F8FAFC; font-size: 1rem;">System Architecture & Spec</span>
                    <span class="tech-tag">DOCS</span>
                </div>
                <p style="color: #7A889B; font-size: 0.82rem; line-height: 1.45; margin: 0;">
                    Technical documentation detailing the exponential decay fatigue engine, capacity deviation math, and Random Forest power regression.
                </p>
            </div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #64748B;">
                SPEC: MATHEMATICAL MODELING
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Read Technical Spec", key="btn_about", use_container_width=True):
            st.session_state["selected_page"] = "About"
            st.rerun()

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Technical Specs Ribbon
    st.markdown("""
    <div style="border-top: 1px solid #161D2B; padding-top: 18px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;">
        <div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #64748B; text-transform: uppercase;">MODEL RUNTIME</div>
            <div style="font-size: 0.85rem; font-weight: 600; color: #CBD5E1; margin-top: 3px;">Scikit-Learn RF</div>
        </div>
        <div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #64748B; text-transform: uppercase;">FATIGUE METRIC</div>
            <div style="font-size: 0.85rem; font-weight: 600; color: #CBD5E1; margin-top: 3px;">Exponential Half-Life</div>
        </div>
        <div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #64748B; text-transform: uppercase;">INGESTION SOURCE</div>
            <div style="font-size: 0.85rem; font-weight: 600; color: #CBD5E1; margin-top: 3px;">Intervals.icu API</div>
        </div>
        <div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #64748B; text-transform: uppercase;">SAMPLING WINDOW</div>
            <div style="font-size: 0.85rem; font-weight: 600; color: #CBD5E1; margin-top: 3px;">180-Day Rolling</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
