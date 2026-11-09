import streamlit as st

def show_contact_page():
    st.markdown("""
        <div style="border-left: 2px solid #FF4B00; padding-left: 16px; margin-bottom: 22px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; letter-spacing: 0.12em; color: #FF4B00; text-transform: uppercase;">
                DISPATCH & INQUIRIES
            </div>
            <h1 style="font-size: 2rem; font-weight: 700; color: #F8FAFC; margin: 4px 0 6px 0; letter-spacing: -0.02em;">
                Contact & Support
            </h1>
            <p style="color: #7A889B; font-size: 0.9rem; margin: 0;">
                Direct inquiries concerning telemetry processing, privacy protocols, or model algorithms.
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1], gap="large")

    with col1:
        st.markdown("""
        <div class="telemetry-panel">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #F8FAFC; text-transform: uppercase; margin-bottom: 12px; font-weight: 600;">
                Developer Inquiries
            </div>
            <p style="color: #94A3B8; font-size: 0.88rem; line-height: 1.6; margin-bottom: 18px;">
                For technical issues, data correction, or privacy inquiries regarding your profile, contact the maintainer directly:
            </p>
            <div style="background: #07090E; border: 1px solid #161D2B; border-radius: 6px; padding: 14px 18px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #64748B; text-transform: uppercase;">Direct Contact</div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.92rem; color: #38BDF8; margin-top: 2px;">harsh.ainapure@harshainapure.dev</div>
                </div>
                <a href="mailto:harsh.ainapure@harshainapure.dev" style="background: #111722; border: 1px solid #1E283A; color: #F8FAFC; padding: 6px 14px; border-radius: 4px; text-decoration: none; font-size: 0.8rem; font-weight: 500;">
                    Compose Email
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="telemetry-panel">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #F8FAFC; text-transform: uppercase; margin-bottom: 12px; font-weight: 600;">
                Data Deletion Requests
            </div>
            <p style="color: #94A3B8; font-size: 0.82rem; line-height: 1.5; margin: 0;">
                Athletes retain full rights to request complete purging of their synchronized activity telemetry and calibrated sensor configurations.
            </p>
        </div>
        """, unsafe_allow_html=True)
