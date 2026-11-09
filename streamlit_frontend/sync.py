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

        st.success("Authentication completed. Token registered in session.")

    jwt = st.session_state.get("jwt")
    is_connected = bool(jwt)

    # Header
    st.markdown("""
        <div style="border-left: 2px solid #FF4B00; padding-left: 16px; margin-bottom: 22px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; letter-spacing: 0.12em; color: #FF4B00; text-transform: uppercase;">
                INGESTION PIPELINE
            </div>
            <h1 style="font-size: 2rem; font-weight: 700; color: #F8FAFC; margin: 4px 0 6px 0; letter-spacing: -0.02em;">
                Activity Synchronization
            </h1>
            <p style="color: #7A889B; font-size: 0.9rem; margin: 0;">
                Connect to Intervals.icu to stream cycling activities, power curves, and sensor channels into the analytics database.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Status Monitor
    stat_c1, stat_c2 = st.columns([5, 2])
    with stat_c1:
        if is_connected:
            masked = f"{jwt[:8]}...{jwt[-6:]}" if len(jwt) > 16 else "VALID_SESSION"
            st.markdown(f"""
            <div style="background: #0B0E15; border: 1px solid #161D2B; border-left: 3px solid #10B981; border-radius: 6px; padding: 14px 18px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; font-weight: 600; color: #10B981;">
                        STATUS: AUTHENTICATED
                    </div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #64748B; margin-top: 2px;">
                        TOKEN: {masked}
                    </div>
                </div>
                <span class="tech-tag live">READY</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: #0B0E15; border: 1px solid #161D2B; border-left: 3px solid #F59E0B; border-radius: 6px; padding: 14px 18px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; font-weight: 600; color: #F59E0B;">
                        STATUS: UNLINKED
                    </div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #64748B; margin-top: 2px;">
                        ACTION: OAUTH AUTHORIZATION REQUIRED
                    </div>
                </div>
                <span class="tech-tag">PENDING</span>
            </div>
            """, unsafe_allow_html=True)

    with stat_c2:
        if is_connected:
            if st.button("Revoke Session", use_container_width=True):
                st.session_state["jwt"] = None
                st.rerun()
        else:
            if st.button("Reload Status", use_container_width=True):
                st.rerun()

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Ingestion Controls & Protocol Specification
    col_flow, col_actions = st.columns([1, 1], gap="large")

    with col_flow:
        st.markdown("""
        <div class="telemetry-panel">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #F8FAFC; text-transform: uppercase; margin-bottom: 14px; font-weight: 600;">
                Pipeline Architecture
            </div>
            <div style="display: flex; flex-direction: column; gap: 14px;">
                <div style="border-left: 1px solid #1F2937; padding-left: 12px;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #FF4B00;">01 // AUTHENTICATION</div>
                    <div style="font-size: 0.85rem; color: #CBD5E1; font-weight: 500; margin-top: 2px;">Handshake with Intervals.icu</div>
                    <div style="font-size: 0.78rem; color: #64748B; margin-top: 2px;">Ensure Strava/Garmin devices are authorized inside Intervals.icu.</div>
                </div>
                <div style="border-left: 1px solid #1F2937; padding-left: 12px;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #FF4B00;">02 // CALIBRATION</div>
                    <div style="font-size: 0.85rem; color: #CBD5E1; font-weight: 500; margin-top: 2px;">Hardware & Power Sensor Mapping</div>
                    <div style="font-size: 0.78rem; color: #64748B; margin-top: 2px;">Verify strain gauge installation month to separate raw from estimated metrics.</div>
                </div>
                <div style="border-left: 1px solid #1F2937; padding-left: 12px;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #FF4B00;">03 // INGESTION</div>
                    <div style="font-size: 0.85rem; color: #CBD5E1; font-weight: 500; margin-top: 2px;">Stream Pull & Feature Extraction</div>
                    <div style="font-size: 0.78rem; color: #64748B; margin-top: 2px;">Ingest workouts, derive exponential fatigue, and recalculate target baseline.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Edit Sensor Profile", use_container_width=True):
            st.session_state["selected_page"] = "Setup Form"
            st.rerun()

    with col_actions:
        st.markdown("""
        <div class="telemetry-panel">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #F8FAFC; text-transform: uppercase; margin-bottom: 14px; font-weight: 600;">
                Ingestion Triggers
            </div>
            <p style="color: #7A889B; font-size: 0.82rem; margin-bottom: 16px; line-height: 1.5;">
                Trigger OAuth credential exchange or dispatch a synchronous ingestion request to the backend worker.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.link_button(
            "Connect Intervals.icu via OAuth",
            f"{BACKEND}/api/user/signup",
            use_container_width=True,
        )

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        sync_triggered = st.button("Initiate Activity Ingestion", type="primary", use_container_width=True)

        if sync_triggered:
            if not jwt:
                st.error("Authentication required. Please connect your Intervals.icu account above.")
            else:
                with st.spinner("Executing pipeline: fetching activity streams, calculating fatigue index, and updating model..."):
                    try:
                        response = requests.post(
                            f"{BACKEND}/api/sync/activities",
                            headers={
                                "Authorization": f"Bearer {jwt}"
                            },
                            timeout=300,
                        )
                        response.raise_for_status()

                        st.success("Activity ingestion completed successfully.")

                        try:
                            payload = response.json()
                            with st.expander("Inspection: Raw Pipeline Response", expanded=True):
                                st.json(payload)
                        except Exception:
                            st.code(response.text)

                        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                        if st.button("Open Telemetry Dashboard", key="btn_to_dashboard"):
                            st.session_state["selected_page"] = "Adaptive Cycling Coach"
                            st.rerun()

                    except requests.exceptions.RequestException as e:
                        st.error(f"Ingestion pipeline failed: {e}")
