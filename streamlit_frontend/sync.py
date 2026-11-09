import streamlit as st
import requests

BACKEND = "https://adaptive-cycling-recommendations.onrender.com"

# -------------------------
# Initialize Session
# -------------------------
if "jwt" not in st.session_state:
    st.session_state["jwt"] = None


def show_sync_page():
    # -------------------------
    # OAuth callback token check
    # -------------------------
    params = st.query_params
    token = params.get("token")

    if token:
        if isinstance(token, list):
            token = token[0]

        st.session_state["jwt"] = token
        if "token" in st.query_params:
            del st.query_params["token"]

        st.toast("Connected to Intervals.icu successfully!", icon="✅")

    jwt = st.session_state.get("jwt")
    is_connected = bool(jwt)

    # Page Header
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
            <div>
                <h1 style="margin: 0; font-size: 2.2rem; font-weight: 800; color: #F8FAFC;">
                    🔄 Activity Synchronization
                </h1>
                <p style="color: #94A3B8; font-size: 1rem; margin-top: 6px;">
                    Integrate your Intervals.icu account to fetch workouts, fit files, and power streams.
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Status Banner
    status_col1, status_col2 = st.columns([3, 1])
    with status_col1:
        if is_connected:
            masked_token = f"{jwt[:6]}...{jwt[-4:]}" if len(jwt) > 12 else "Valid Token"
            st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 16px 20px; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="background: #10B981; width: 12px; height: 12px; border-radius: 50%; box-shadow: 0 0 10px #10B981;"></div>
                    <div>
                        <div style="font-weight: 700; color: #34D399; font-size: 0.95rem;">Intervals.icu Connected</div>
                        <div style="font-size: 0.8rem; color: #94A3B8;">Authorization Token: <code>{masked_token}</code></div>
                    </div>
                </div>
                <span class="badge-primary" style="background: rgba(16, 185, 129, 0.2); border-color: rgba(16, 185, 129, 0.4); color: #34D399;">Ready to Sync</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 16px 20px; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="background: #F59E0B; width: 12px; height: 12px; border-radius: 50%; box-shadow: 0 0 10px #F59E0B;"></div>
                    <div>
                        <div style="font-weight: 700; color: #FBBF24; font-size: 0.95rem;">No Intervals Account Linked</div>
                        <div style="font-size: 0.8rem; color: #94A3B8;">Connect your account below to begin ingestion.</div>
                    </div>
                </div>
                <span class="badge-primary" style="background: rgba(245, 158, 11, 0.2); border-color: rgba(245, 158, 11, 0.4); color: #FBBF24;">Action Required</span>
            </div>
            """, unsafe_allow_html=True)

    with status_col2:
        if is_connected:
            if st.button("Disconnect", use_container_width=True):
                st.session_state["jwt"] = None
                st.rerun()
        else:
            if st.button("Refresh State", use_container_width=True):
                st.rerun()

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 3-Step Setup / Action Workflow
    step_col1, step_col2 = st.columns([1, 1], gap="large")

    with step_col1:
        st.markdown("""
        <div style="background: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 22px;">
            <div style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC; margin-bottom: 14px; display: flex; align-items: center; gap: 8px;">
                <span>🚀</span> Setup & Connection Workflow
            </div>
            <div style="display: flex; flex-direction: column; gap: 14px;">
                <div style="display: flex; gap: 12px; align-items: flex-start;">
                    <div style="background: #1E293B; border: 1px solid rgba(255,255,255,0.1); width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem; color: #FC4C02;">1</div>
                    <div>
                        <div style="font-weight: 600; color: #F1F5F9; font-size: 0.9rem;">Create or Login to Intervals.icu</div>
                        <div style="font-size: 0.8rem; color: #94A3B8;">Connect your Strava, Garmin, or Wahoo device inside <a href="https://intervals.icu/" target="_blank" style="color: #FC4C02;">Intervals.icu</a>.</div>
                    </div>
                </div>
                <div style="display: flex; gap: 12px; align-items: flex-start;">
                    <div style="background: #1E293B; border: 1px solid rgba(255,255,255,0.1); width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem; color: #FC4C02;">2</div>
                    <div>
                        <div style="font-weight: 600; color: #F1F5F9; font-size: 0.9rem;">Authorize via OAuth</div>
                        <div style="font-size: 0.8rem; color: #94A3B8;">Grant secure access using the OAuth connection button.</div>
                    </div>
                </div>
                <div style="display: flex; gap: 12px; align-items: flex-start;">
                    <div style="background: #1E293B; border: 1px solid rgba(255,255,255,0.1); width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem; color: #FC4C02;">3</div>
                    <div>
                        <div style="font-weight: 600; color: #F1F5F9; font-size: 0.9rem;">Calibrate & Ingest</div>
                        <div style="font-size: 0.8rem; color: #94A3B8;">Complete your rider setup profile and sync your ride history.</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        if st.button("Configure Rider Profile First ➔", use_container_width=True):
            st.session_state["selected_page"] = "Setup Form"
            st.rerun()

    with step_col2:
        st.markdown("""
        <div style="background: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 22px;">
            <div style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC; margin-bottom: 14px; display: flex; align-items: center; gap: 8px;">
                <span>⚡</span> Sync Operations
            </div>
            <p style="color: #94A3B8; font-size: 0.85rem; margin-bottom: 18px;">
                Authenticate with Intervals.icu or initiate a full historical sync of your recent cycling activities.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.link_button(
            "🔗 Connect Intervals.icu via OAuth",
            f"{BACKEND}/api/user/signup",
            use_container_width=True,
        )

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        sync_clicked = st.button("⚡ Sync Activities Now", type="primary", use_container_width=True)

        if sync_clicked:
            if not jwt:
                st.error("Please connect your Intervals.icu account before syncing.")
            else:
                with st.spinner("Connecting to backend and synchronizing activities... This may take up to a few minutes for large catalogs."):
                    try:
                        response = requests.post(
                            f"{BACKEND}/api/sync/activities",
                            headers={
                                "Authorization": f"Bearer {jwt}"
                            },
                            timeout=300,
                        )
                        response.raise_for_status()

                        st.success("Activities synchronized successfully!")

                        # Show result details cleanly
                        try:
                            result_data = response.json()
                            with st.expander("📄 View Sync Response Payload", expanded=True):
                                st.json(result_data)
                        except Exception:
                            st.write(response.text)

                        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                        if st.button("View AI Dashboard Now ➔", key="goto_coach_post_sync"):
                            st.session_state["selected_page"] = "Adaptive Cycling Coach"
                            st.rerun()

                    except requests.exceptions.RequestException as e:
                        st.error(f"Unable to contact backend during sync.\n\n{e}")
