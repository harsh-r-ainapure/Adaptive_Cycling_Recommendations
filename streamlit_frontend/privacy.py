import streamlit as st

def show_privacy_page():
    st.markdown("""
        <div style="border-left: 2px solid #FF4B00; padding-left: 16px; margin-bottom: 22px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; letter-spacing: 0.12em; color: #FF4B00; text-transform: uppercase;">
                    DATA COMPLIANCE
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #64748B;">
                    REVISION: JULY 2026
                </div>
            </div>
            <h1 style="font-size: 2rem; font-weight: 700; color: #F8FAFC; margin: 4px 0 6px 0; letter-spacing: -0.02em;">
                Privacy Protocol
            </h1>
            <p style="color: #7A889B; font-size: 0.9rem; margin: 0;">
                Data handling, retention standards, and telemetry confidentiality protocols.
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div class="telemetry-panel">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #F8FAFC; text-transform: uppercase; margin-bottom: 12px; font-weight: 600;">
                Ingested Telemetry Scope
            </div>
            <p style="color: #94A3B8; font-size: 0.85rem; line-height: 1.6;">
                The platform processes the following activity attributes fetched via authorized OAuth connections:
            </p>
            <ul style="color: #CBD5E1; font-size: 0.82rem; line-height: 1.8; margin-left: -15px;">
                <li>Activity timestamp and elapsed recording duration</li>
                <li>Distance in meters and cumulative elevation gain</li>
                <li>Heart rate sensor streams and cadence channels</li>
                <li>Direct mechanical power outputs (Watts) and normalized power</li>
                <li>Athlete calibration preferences and power meter installation timeline</li>
            </ul>
            <div style="border-top: 1px solid #161D2B; padding-top: 10px; margin-top: 10px; font-size: 0.78rem; color: #64748B;">
                Note: No personal information is requested beyond the technical metrics necessary to calculate fatigue curves.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="telemetry-panel">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #F8FAFC; text-transform: uppercase; margin-bottom: 12px; font-weight: 600;">
                Computational Usage
            </div>
            <p style="color: #94A3B8; font-size: 0.85rem; line-height: 1.6;">
                Activity records are evaluated strictly for algorithmic computations:
            </p>
            <ul style="color: #CBD5E1; font-size: 0.82rem; line-height: 1.8; margin-left: -15px;">
                <li>Calculating acute and chronic training strain</li>
                <li>Deriving exponential fatigue decay curves over 180 days</li>
                <li>Evaluating capacity variance relative to rolling baseline</li>
                <li>Training the supervised Random Forest power regressor</li>
                <li>Synthesizing volume and elevation recommendations</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 10px;">
        <div class="telemetry-panel">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #F8FAFC; text-transform: uppercase; margin-bottom: 8px; font-weight: 600;">
                Zero Commercial Monetization
            </div>
            <p style="color: #7A889B; font-size: 0.82rem; line-height: 1.5; margin: 0;">
                Workout files and personal biometric telemetry are never commercialized, sold, or shared with third-party advertisers.
            </p>
        </div>
        <div class="telemetry-panel">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #F8FAFC; text-transform: uppercase; margin-bottom: 8px; font-weight: 600;">
                Secure Tokenization
            </div>
            <p style="color: #7A889B; font-size: 0.82rem; line-height: 1.5; margin: 0;">
                Communications across frontend interfaces, backend endpoints, and fitness APIs use encrypted HTTPS and standard JWT authentication.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
