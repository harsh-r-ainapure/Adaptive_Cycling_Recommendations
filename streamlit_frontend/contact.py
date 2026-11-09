import streamlit as st

def show_contact_page():
    st.markdown("""
        <div style="margin-bottom: 24px;">
            <span class="badge-primary">Get in Touch</span>
            <h1 style="margin: 8px 0 0 0; font-size: 2.2rem; font-weight: 800; color: #F8FAFC;">
                ✉️ Contact & Support
            </h1>
            <p style="color: #94A3B8; font-size: 1rem; margin-top: 6px;">
                Have questions regarding the platform, privacy policies, or algorithm modeling?
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1], gap="large")

    with col1:
        st.markdown("""
        <div class="modern-card">
            <h3 style="margin-top: 0; color: #F8FAFC; font-size: 1.15rem;">Support & Inquiries</h3>
            <p style="color: #94A3B8; font-size: 0.95rem; line-height: 1.6;">
                For questions regarding data handling practices, privacy inquiries, or developer collaboration, please reach out directly:
            </p>
            <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 14px 18px; margin-top: 16px; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-size: 0.8rem; color: #64748B; font-weight: 600; text-transform: uppercase;">Direct Email</div>
                    <div style="font-size: 1.05rem; font-weight: 600; color: #38BDF8; font-family: monospace;">harsh.ainapure@harshainapure.dev</div>
                </div>
                <a href="mailto:harsh.ainapure@harshainapure.dev" style="background: #1E293B; border: 1px solid rgba(255,255,255,0.15); color: #F8FAFC; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-size: 0.85rem; font-weight: 600;">
                    Send Email ➔
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 22px;">
            <div style="font-weight: 700; color: #F8FAFC; margin-bottom: 8px; font-size: 1rem;">
                🛡️ Open Privacy Inquiries
            </div>
            <p style="color: #94A3B8; font-size: 0.85rem; line-height: 1.5; margin: 0;">
                Users can request activity data exports or deletion of stored profile calibration records at any time.
            </p>
        </div>
        """, unsafe_allow_html=True)
