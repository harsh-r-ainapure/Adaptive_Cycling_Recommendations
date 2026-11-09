import streamlit as st

def show_privacy_page():
    st.markdown("""
        <div style="margin-bottom: 24px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="badge-primary">Data Security & Compliance</span>
                <span style="font-size: 0.8rem; color: #64748B;">Last Updated: July 2026</span>
            </div>
            <h1 style="margin: 8px 0 0 0; font-size: 2.2rem; font-weight: 800; color: #F8FAFC;">
                🔒 Privacy Policy
            </h1>
            <p style="color: #94A3B8; font-size: 1rem; margin-top: 6px;">
                Adaptive Cycling Coach respects your privacy and is dedicated to protecting your fitness metrics and activity data.
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div class="modern-card">
            <h3 style="margin-top: 0; color: #F8FAFC; font-size: 1.15rem; display: flex; align-items: center; gap: 8px;">
                <span>📊</span> Information Collected
            </h3>
            <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.6;">
                The platform may process the following activity information fetched through authorized APIs:
            </p>
            <ul style="color: #CBD5E1; font-size: 0.85rem; line-height: 1.8; margin-left: -15px;">
                <li>Activity date, duration, and elapsed time</li>
                <li>Distance and elevation gain</li>
                <li>Heart rate streams and average/max cadence</li>
                <li>Power output streams (Watts) and normalized power</li>
                <li>Rider profile calibration preferences</li>
            </ul>
            <div style="background: rgba(255,255,255,0.03); border-left: 3px solid #FC4C02; padding: 10px 14px; border-radius: 4px; margin-top: 14px; font-size: 0.82rem; color: #94A3B8;">
                <strong>Note:</strong> We do not collect unnecessary personal information beyond what is strictly required to compute fatigue models and recommendations.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="modern-card">
            <h3 style="margin-top: 0; color: #F8FAFC; font-size: 1.15rem; display: flex; align-items: center; gap: 8px;">
                <span>⚙️</span> How Data Is Used
            </h3>
            <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.6;">
                Activity data is processed exclusively for the following capabilities:
            </p>
            <ul style="color: #CBD5E1; font-size: 0.85rem; line-height: 1.8; margin-left: -15px;">
                <li>Analyze historical cycling performance and work capacity</li>
                <li>Estimate acute fatigue and recovery status over time</li>
                <li>Generate next-session personalized training targets</li>
                <li>Evaluate and calibrate ML power prediction models</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 10px;">
        <div style="background: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 20px;">
            <div style="font-weight: 700; color: #F8FAFC; margin-bottom: 8px; font-size: 1rem;">
                🛡️ No Data Selling or Sharing
            </div>
            <p style="color: #94A3B8; font-size: 0.85rem; line-height: 1.5; margin: 0;">
                User activity records and credentials are never sold, rented, or shared with third-party advertisers or data brokers.
            </p>
        </div>
        <div style="background: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 20px;">
            <div style="font-weight: 700; color: #F8FAFC; margin-bottom: 8px; font-size: 1rem;">
                🔐 Technical & Organizational Security
            </div>
            <p style="color: #94A3B8; font-size: 0.85rem; line-height: 1.5; margin: 0;">
                Industry standard tokenization and HTTPS encryption in transit protect communication between the frontend, backend APIs, and external fitness ecosystems.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
