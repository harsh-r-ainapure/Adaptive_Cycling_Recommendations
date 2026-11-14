import streamlit as st
from pathlib import Path


def show_homepage():
    user_name = st.session_state.get("user_name") or "Harsh"
    jwt = st.session_state.get("jwt")
    is_connected = bool(jwt)

    # Top Telemetry Status Header (HUD)
    hud_c1, hud_c2 = st.columns([7, 2])
    with hud_c1:
        status_tag = '<span class="tech-tag live">LINKED // GARMIN CONNECT</span>' if is_connected else '<span class="tech-tag">UNLINKED // GARMIN CONNECT</span>'
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

    # Minimalist Hero Header
    header_col, logo_col = st.columns([5, 1])
    with header_col:
        st.markdown("""
        <div style="border-left: 2px solid #FF4B00; padding-left: 18px; margin-bottom: 28px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; letter-spacing: 0.12em; color: #FF4B00; text-transform: uppercase;">
                ENDURANCE TELEMETRY PLATFORM
            </div>
            <h1 style="font-size: 2.2rem; font-weight: 700; color: #F8FAFC; margin: 6px 0 8px 0; letter-spacing: -0.02em;">
                Adaptive Cycling Intelligence
            </h1>
            <p style="color: #7A889B; font-size: 0.92rem; max-width: 720px; margin: 0; line-height: 1.6;">
                Physiological fatigue modeling and machine-learned capacity reconstitution. Follow the operating protocol below to calibrate your sensor hardware, import activity records, and review adaptive training prescriptions.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with logo_col:
        BASE_DIR = Path(__file__).parent
        logo_path = BASE_DIR / "stravalogo-300x300.png"
        if not logo_path.exists():
            logo_path = BASE_DIR / "stravalogo.png"
        if logo_path.exists():
            st.image(str(logo_path), caption="Integration: Garmin Connect", use_container_width=True)

    # Clean & Modern Instructions / System Protocol
    st.markdown("""
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; letter-spacing: 0.08em; color: #64748B; text-transform: uppercase; margin-bottom: 14px;">
        OPERATING PROTOCOL // SYSTEM WORKFLOW
    </div>
    """, unsafe_allow_html=True)

    step_col1, step_col2 = st.columns(2, gap="large")

    with step_col1:
        st.markdown("""
        <div class="telemetry-panel" style="margin-bottom: 16px; min-height: 160px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #FF4B00; text-transform: uppercase; font-weight: 600;">
                    STAGE 01 // SENSOR CALIBRATION
                </div>
                <span class="tech-tag">CALIBRATION</span>
            </div>
            <div style="font-weight: 600; color: #F8FAFC; font-size: 1rem; margin-bottom: 6px;">
                Hardware & Timeline Setup
            </div>
            <p style="color: #7A889B; font-size: 0.83rem; line-height: 1.5; margin: 0;">
                Navigate to <strong>Sensor Calibration</strong> in the sidebar. Specify whether your bicycle is equipped with a strain gauge power meter and set the installation month and year. This allows the machine learning pipeline to distinguish true recorded wattage from estimated power.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="telemetry-panel" style="margin-bottom: 16px; min-height: 160px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #FF4B00; text-transform: uppercase; font-weight: 600;">
                    STAGE 03 // REAL-TIME WEBHOOK PUSH
                </div>
                <span class="tech-tag live">AUTOMATED</span>
            </div>
            <div style="font-weight: 600; color: #F8FAFC; font-size: 1rem; margin-bottom: 6px;">
                Continuous Automatic Ingestion
            </div>
            <p style="color: #7A889B; font-size: 0.83rem; line-height: 1.5; margin: 0;">
                Once your baseline archive is initialized, future rides sync with zero manual intervention. Completed activities recorded on your Garmin device automatically stream to the backend webhook listener, updating physiological decay curves in real time.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with step_col2:
        st.markdown("""
        <div class="telemetry-panel" style="margin-bottom: 16px; min-height: 160px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #FF4B00; text-transform: uppercase; font-weight: 600;">
                    STAGE 02 // HISTORICAL ARCHIVE IMPORT
                </div>
                <span class="tech-tag">INGESTION</span>
            </div>
            <div style="font-weight: 600; color: #F8FAFC; font-size: 1rem; margin-bottom: 6px;">
                Garmin OAuth & Archive Ingestion
            </div>
            <p style="color: #7A889B; font-size: 0.83rem; line-height: 1.5; margin: 0;">
                Navigate to <strong>Activity Synchronization</strong>. Authorize with Garmin Connect via OAuth2 PKCE, then upload your exported Garmin data archive (<code>.zip</code> package containing raw <code>.fit</code> files) to train the baseline Random Forest models.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="telemetry-panel" style="margin-bottom: 16px; min-height: 160px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #FF4B00; text-transform: uppercase; font-weight: 600;">
                    STAGE 04 // COACH TERMINAL
                </div>
                <span class="tech-tag active">CORE</span>
            </div>
            <div style="font-weight: 600; color: #F8FAFC; font-size: 1rem; margin-bottom: 6px;">
                Telemetry & Training Targets
            </div>
            <p style="color: #7A889B; font-size: 0.83rem; line-height: 1.5; margin: 0;">
                Open <strong>Coach & Telemetry</strong> to evaluate rolling fatigue curves, capacity variance, and training strain metrics. Review adaptive targets (distance, elevation, and heart rate ceiling) generated for your next workout session.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

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
            <div style="font-size: 0.85rem; font-weight: 600; color: #CBD5E1; margin-top: 3px;">Garmin Health API & Webhooks</div>
        </div>
        <div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #64748B; text-transform: uppercase;">SAMPLING WINDOW</div>
            <div style="font-size: 0.85rem; font-weight: 600; color: #CBD5E1; margin-top: 3px;">180-Day Rolling</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
