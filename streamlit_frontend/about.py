import streamlit as st

def show_about_page():
    # Header
    st.markdown("""
        <div style="margin-bottom: 24px;">
            <span class="badge-primary">System Architecture</span>
            <h1 style="margin: 8px 0 0 0; font-size: 2.2rem; font-weight: 800; color: #F8FAFC;">
                ℹ️ About Adaptive Cycling Coach
            </h1>
            <p style="color: #94A3B8; font-size: 1rem; margin-top: 6px;">
                Personalized cycling performance analysis powered by physiology models and machine learning.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Mission Statement Card
    st.markdown("""
    <div class="modern-card">
        <h3 style="margin-top: 0; color: #F8FAFC; font-size: 1.25rem;">Project Overview</h3>
        <p style="color: #94A3B8; font-size: 0.95rem; line-height: 1.6;">
            <strong>Adaptive Cycling Coach</strong> is an independent software project focused on personalized cycling performance analysis and training recommendations.
            The platform analyzes historical cycling activities to estimate rider fatigue, current performance capacity, and recovery status. Using these insights, it generates personalized recommendations for the rider's next session, including suggested distance, elevation gain, and target heart rate.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ML Advantage Callout
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(252, 76, 2, 0.12), rgba(255, 122, 0, 0.05)); border: 1px solid rgba(252, 76, 2, 0.35); border-radius: 14px; padding: 22px 24px; margin-bottom: 24px;">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
            <span style="font-size: 1.3rem;">🧠</span>
            <span style="font-weight: 700; color: #FC4C02; font-size: 1.1rem;">The Machine Learning Advantage</span>
        </div>
        <p style="color: #E2E8F0; font-size: 0.92rem; line-height: 1.6; margin: 0;">
            Unlike applications that rely solely on historical statistics or basic weekly mileage averages, 
            <strong>Adaptive Cycling Coach</strong> incorporates machine learning alongside a physiology-inspired fatigue 
            model to estimate changes in rider capacity over time. The objective is to help cyclists 
            train more consistently while reducing unnecessary fatigue and improving long-term performance.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Features and Roadmap
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div style="background: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 22px; height: 100%;">
            <div style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                <span>✨</span> Core Features
            </div>
            <ul style="color: #94A3B8; font-size: 0.9rem; line-height: 1.8; margin-left: -15px;">
                <li><strong style="color: #F1F5F9;">Ride Performance Visualization:</strong> Interactive elevation, distance, and intensity metrics.</li>
                <li><strong style="color: #F1F5F9;">Fatigue Trend Analysis:</strong> 6-month exponential decay fatigue curve estimation.</li>
                <li><strong style="color: #F1F5F9;">Capacity Deviation Tracking:</strong> Detects overreaching and baseline deviations.</li>
                <li><strong style="color: #F1F5F9;">Average Power Prediction:</strong> Supervised Random Forest modeling.</li>
                <li><strong style="color: #F1F5F9;">Personalized Recommendations:</strong> Target distance, elevation, and HR for optimal adaptation.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 22px; height: 100%;">
            <div style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                <span>🚀</span> Development Roadmap
            </div>
            <ul style="color: #94A3B8; font-size: 0.9rem; line-height: 1.8; margin-left: -15px;">
                <li><strong style="color: #F1F5F9;">Automated Ingestion:</strong> Continuous webhook sync with Intervals.icu & Strava.</li>
                <li><strong style="color: #F1F5F9;">Expanded Biometrics:</strong> HRV (Heart Rate Variability) and sleep integration.</li>
                <li><strong style="color: #F1F5F9;">Multi-Sport Expansion:</strong> Running and gravel endurance support.</li>
                <li><strong style="color: #F1F5F9;">WKO5 / CP Curves:</strong> Power-duration curve modeling and Critical Power tracking.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
