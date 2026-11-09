import streamlit as st

def show_about_page():
    st.markdown("""
        <div style="border-left: 2px solid #FF4B00; padding-left: 16px; margin-bottom: 22px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; letter-spacing: 0.12em; color: #FF4B00; text-transform: uppercase;">
                TECHNICAL SPECIFICATION
            </div>
            <h1 style="font-size: 2rem; font-weight: 700; color: #F8FAFC; margin: 4px 0 6px 0; letter-spacing: -0.02em;">
                System Architecture & Modeling
            </h1>
            <p style="color: #7A889B; font-size: 0.9rem; margin: 0;">
                Mathematical and computational foundations of the Adaptive Cycling Coach platform.
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="telemetry-panel">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #FF4B00; text-transform: uppercase; margin-bottom: 8px;">
            01 // PROJECT SCOPE
        </div>
        <p style="color: #CBD5E1; font-size: 0.9rem; line-height: 1.6; margin: 0;">
            Adaptive Cycling Coach is an independent endurance engineering system focused on precision training telemetry and physiological strain estimation. By continuously analyzing historical workout files, it models acute and chronic fatigue half-life, evaluates work capacity variance, and calculates target outputs (distance, total ascent, and heart rate ceiling) for upcoming rides.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="telemetry-panel" style="border-left: 3px solid #FF4B00;">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #FF4B00; text-transform: uppercase; margin-bottom: 8px;">
            02 // MACHINE LEARNING ADVANTAGE
        </div>
        <p style="color: #CBD5E1; font-size: 0.9rem; line-height: 1.6; margin: 0;">
            Conventional training applications rely on simple moving averages or static weekly mileage rules that disregard non-linear physiological recovery. Adaptive Cycling Coach combines an exponential decay fatigue model with a supervised Random Forest regressor. This dual architecture evaluates individual athlete recovery kinetics, minimizing overtraining injury risk while ensuring progressive stimulus overload.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div class="telemetry-panel" style="height: 100%;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #F8FAFC; text-transform: uppercase; margin-bottom: 14px; font-weight: 600;">
                Telemetry Capabilities
            </div>
            <ul style="color: #94A3B8; font-size: 0.85rem; line-height: 1.8; margin-left: -15px;">
                <li><strong style="color: #F1F5F9;">Multivariate Telemetry:</strong> Ingestion of cadence, power, elevation gain, and elapsed time.</li>
                <li><strong style="color: #F1F5F9;">Exponential Fatigue Decay:</strong> Continuous half-life modeling computed from normalized training stress.</li>
                <li><strong style="color: #F1F5F9;">Capacity Deviation:</strong> Tracks positive and negative work capacity deltas against athlete baseline.</li>
                <li><strong style="color: #F1F5F9;">RF Power Estimation:</strong> Ensemble tree regressor predicting power output under variable terrain.</li>
                <li><strong style="color: #F1F5F9;">Target Synthesis:</strong> Generates next-session distance, elevation, and intensity bounds.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="telemetry-panel" style="height: 100%;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #F8FAFC; text-transform: uppercase; margin-bottom: 14px; font-weight: 600;">
                Pipeline Architecture
            </div>
            <ul style="color: #94A3B8; font-size: 0.85rem; line-height: 1.8; margin-left: -15px;">
                <li><strong style="color: #F1F5F9;">Ingestion Layer:</strong> REST-based tokenized sync with Intervals.icu and Strava.</li>
                <li><strong style="color: #F1F5F9;">Feature Engineering:</strong> Preprocessing of raw sensor time-series and outlier clipping.</li>
                <li><strong style="color: #F1F5F9;">Baseline Computation:</strong> Multi-week rolling averages for heart rate, elevation, and volume.</li>
                <li><strong style="color: #F1F5F9;">Serving Layer:</strong> Streamlit wide telemetry dashboard coupled to Express API backend.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
