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

        st.success("Authentication completed. Garmin session registered.")

    jwt = st.session_state.get("jwt")
    is_connected = bool(jwt)

    # Header
    st.markdown("""
        <div style="border-left: 2px solid #FF4B00; padding-left: 16px; margin-bottom: 22px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; letter-spacing: 0.12em; color: #FF4B00; text-transform: uppercase;">
                INGESTION & DATA PIPELINE
            </div>
            <h1 style="font-size: 2rem; font-weight: 700; color: #F8FAFC; margin: 4px 0 6px 0; letter-spacing: -0.02em;">
                Garmin Connect Synchronization
            </h1>
            <p style="color: #7A889B; font-size: 0.9rem; margin: 0;">
                Connect to Garmin Health API, import historical training archives, and manage real-time webhook ingestion.
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
                        STATUS: AUTHENTICATED // GARMIN CONNECT
                    </div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #64748B; margin-top: 2px;">
                        TOKEN: {masked}
                    </div>
                </div>
                <span class="tech-tag live">ACTIVE</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: #0B0E15; border: 1px solid #161D2B; border-left: 3px solid #F59E0B; border-radius: 6px; padding: 14px 18px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; font-weight: 600; color: #F59E0B;">
                        STATUS: UNLINKED // GARMIN CONNECT
                    </div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #64748B; margin-top: 2px;">
                        ACTION: GARMIN PKCE OAUTH2 AUTHORIZATION REQUIRED
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

    # Tabs for Data Pipeline Operations
    tab_history, tab_webhooks, tab_architecture = st.tabs([
        "01 // HISTORICAL ZIP IMPORT",
        "02 // AUTOMATIC WEBHOOK PIPELINE",
        "03 // PIPELINE ARCHITECTURE"
    ])

    # --------------------------------------------------------
    # TAB 1: FIRST-TIME HISTORICAL ZIP IMPORT
    # --------------------------------------------------------
    with tab_history:
        st.markdown("""
        <div class="telemetry-panel" style="margin-bottom: 16px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #F8FAFC; text-transform: uppercase; margin-bottom: 8px; font-weight: 600;">
                First-Time Setup: Garmin Historical Archive Package
            </div>
            <p style="color: #7A889B; font-size: 0.85rem; line-height: 1.5; margin: 0;">
                Garmin Health API streams upcoming activities in real time via webhooks. To initialize your 180-day physiological fatigue curve and train the Random Forest power regressor, upload your Garmin Connect data export archive (.zip containing .fit files).
            </p>
        </div>
        """, unsafe_allow_html=True)

        if not is_connected:
            st.markdown("""
            <div class="telemetry-panel" style="border-left: 3px solid #F59E0B;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #F59E0B; text-transform: uppercase; margin-bottom: 6px;">
                    AUTHENTICATION REQUIRED FIRST
                </div>
                <p style="color: #94A3B8; font-size: 0.85rem; margin-bottom: 12px;">
                    Please authenticate with Garmin Connect before uploading your historical data package.
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.link_button(
                "Authorize Garmin Connect via OAuth2",
                f"{BACKEND}/api/auth/garmin/signup",
                use_container_width=True,
            )
        else:
            col_upload, col_instructions = st.columns([1, 1], gap="large")

            with col_upload:
                uploaded_zip = st.file_uploader(
                    "Select Garmin Export Archive (.zip)",
                    type=["zip"],
                    help="Upload your exported Garmin data package containing raw .fit activity files."
                )

                upload_btn = st.button(
                    "Import Historical Data & Train ML Models",
                    type="primary",
                    use_container_width=True,
                    disabled=(uploaded_zip is None)
                )

                if upload_btn and uploaded_zip is not None:
                    with st.spinner("Processing archive: unpacking .fit files, preprocessing telemetry, extracting features, and training baseline ML models... (this may take up to a few minutes)"):
                        try:
                            files = {
                                "zipFile": (uploaded_zip.name, uploaded_zip.getvalue(), "application/zip")
                            }
                            headers = {
                                "Authorization": f"Bearer {jwt}"
                            }

                            res = requests.post(
                                f"{BACKEND}/api/history/upload-history",
                                headers=headers,
                                files=files,
                                timeout=600
                            )

                            if res.status_code == 200:
                                st.success("Historical data package processed successfully! Baseline models initialized.")
                                try:
                                    res_json = res.json()
                                    st.json(res_json)
                                except Exception:
                                    st.write(res.text)

                                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                                if st.button("Launch Coach Dashboard ➔", key="goto_dash_post_history"):
                                    st.session_state["selected_page"] = "Adaptive Cycling Coach"
                                    st.rerun()

                            elif res.status_code == 403:
                                st.info("Historical data already exists in database. Baseline initialized. Future rides synchronize automatically via Garmin webhooks.")
                                try:
                                    st.json(res.json())
                                except Exception:
                                    pass
                            else:
                                st.error(f"Import returned HTTP {res.status_code}: {res.text}")

                        except requests.exceptions.RequestException as e:
                            st.error(f"Upload and processing pipeline failed: {e}")

            with col_instructions:
                st.markdown("""
                <div class="telemetry-panel">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #F8FAFC; text-transform: uppercase; margin-bottom: 12px; font-weight: 600;">
                        How to Export Garmin History
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 10px; font-size: 0.82rem; color: #94A3B8;">
                        <div>
                            <strong style="color: #CBD5E1;">1. Garmin Account Settings:</strong> Log in to <a href="https://www.garmin.com/en-US/account/datamanagement/" target="_blank" style="color: #FF4B00;">Garmin Data Management</a>.
                        </div>
                        <div>
                            <strong style="color: #CBD5E1;">2. Request Export:</strong> Click <em>Export Your Data</em> &rarr; <em>Request Data Export</em>.
                        </div>
                        <div>
                            <strong style="color: #CBD5E1;">3. Download Package:</strong> Garmin will email a ZIP download link containing your DI_CONNECT activity folders.
                        </div>
                        <div>
                            <strong style="color: #CBD5E1;">4. Ingest Here:</strong> Upload the downloaded .zip directly without extracting it.
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # --------------------------------------------------------
    # TAB 2: AUTOMATIC WEBHOOK PIPELINE
    # --------------------------------------------------------
    with tab_webhooks:
        st.markdown("""
        <div class="telemetry-panel">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #F8FAFC; text-transform: uppercase; font-weight: 600;">
                    Real-Time Ingestion Listener
                </div>
                <span class="tech-tag live">ENDPOINT: /api/sync/activities</span>
            </div>
            <p style="color: #7A889B; font-size: 0.85rem; line-height: 1.6; margin-bottom: 16px;">
                Once your historical baseline has been initialized, future rides require zero manual action. When you finish and save an activity on your Garmin Edge, Forerunner, or Fenix device:
            </p>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;">
                <div style="background: #07090E; border: 1px solid #161D2B; border-radius: 6px; padding: 14px;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #FF4B00;">01 // PUSH EVENT</div>
                    <div style="font-size: 0.82rem; color: #CBD5E1; margin-top: 4px;">Garmin Health API pushes notification to webhook receiver.</div>
                </div>
                <div style="background: #07090E; border: 1px solid #161D2B; border-radius: 6px; padding: 14px;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #FF4B00;">02 // FIT DECOMPRESSION</div>
                    <div style="font-size: 0.82rem; color: #CBD5E1; margin-top: 4px;">Backend downloads, gunzips, and parses binary telemetry.</div>
                </div>
                <div style="background: #07090E; border: 1px solid #161D2B; border-radius: 6px; padding: 14px;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #FF4B00;">03 // ML RETRAINING</div>
                    <div style="font-size: 0.82rem; color: #CBD5E1; margin-top: 4px;">Fatigue half-life decays, RF models infer, recommendations update.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not is_connected:
            st.link_button(
                "Link Garmin Connect Account",
                f"{BACKEND}/api/auth/garmin/signup",
                use_container_width=True,
            )
        else:
            st.info("Garmin Connect account is linked. Automated background synchronization is active.")

    # --------------------------------------------------------
    # TAB 3: PIPELINE ARCHITECTURE
    # --------------------------------------------------------
    with tab_architecture:
        st.markdown("""
        <div class="telemetry-panel">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #F8FAFC; text-transform: uppercase; margin-bottom: 14px; font-weight: 600;">
                Garmin Integration Architecture
            </div>
            <div style="display: flex; flex-direction: column; gap: 14px;">
                <div style="border-left: 1px solid #1F2937; padding-left: 12px;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #FF4B00;">STAGE 1 // GARMIN OAUTH2 PKCE</div>
                    <div style="font-size: 0.85rem; color: #CBD5E1; font-weight: 500; margin-top: 2px;">OAuth Handshake with S256 Code Challenge</div>
                    <div style="font-size: 0.78rem; color: #64748B; margin-top: 2px;">Exchanges authorization code for Garmin access token and retrieves permanent Garmin User ID.</div>
                </div>
                <div style="border-left: 1px solid #1F2937; padding-left: 12px;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #FF4B00;">STAGE 2 // HISTORICAL PACKAGE INGESTION</div>
                    <div style="font-size: 0.85rem; color: #CBD5E1; font-weight: 500; margin-top: 2px;">Single-Zip Extraction & Multi-Script ML Initialization</div>
                    <div style="font-size: 0.78rem; color: #64748B; margin-top: 2px;">Executes preprocess, features, fatigue, capacities, and severity python engines sequentially.</div>
                </div>
                <div style="border-left: 1px solid #1F2937; padding-left: 12px;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #FF4B00;">STAGE 3 // REAL-TIME WEBHOOK INGESTION</div>
                    <div style="font-size: 0.85rem; color: #CBD5E1; font-weight: 500; margin-top: 2px;">Push Notifications for Completed Workouts</div>
                    <div style="font-size: 0.78rem; color: #64748B; margin-top: 2px;">Continuous listener at /api/sync/activities automatically updating fatigue and capacity metrics.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Configure Sensor Baseline Profile", use_container_width=True):
            st.session_state["selected_page"] = "Setup Form"
            st.rerun()
