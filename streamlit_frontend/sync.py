import streamlit as st
import requests
import base64
import json
import streamlit.components.v1 as components

BACKEND = "https://adaptive-cycling-recommendations.onrender.com"

# -------------------------
# Initialize Session Keys
# -------------------------
if "jwt" not in st.session_state:
    st.session_state["jwt"] = None
if "sync_in_progress" not in st.session_state:
    st.session_state["sync_in_progress"] = False
if "sync_status" not in st.session_state:
    st.session_state["sync_status"] = "idle"
if "notify_me" not in st.session_state:
    st.session_state["notify_me"] = True
if "notified_for_current_sync" not in st.session_state:
    st.session_state["notified_for_current_sync"] = False


def get_user_id_from_jwt(token):
    """Decodes user ID from JWT payload without external libraries."""
    if not token:
        return None
    try:
        parts = token.split(".")
        if len(parts) >= 2:
            payload = parts[1]
            padded = payload + "=" * ((4 - len(payload) % 4) % 4)
            data = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
            return str(data.get("id"))
    except Exception:
        pass
    return None


def request_notification_permission():
    """Requests native browser notification permission."""
    components.html("""
    <script>
    (function() {
        var notif = (window.parent && window.parent.Notification) ? window.parent.Notification : window.Notification;
        if (notif && notif.permission === "default") {
            notif.requestPermission();
        }
    })();
    </script>
    """, height=0, width=0)


def send_browser_notification(title, body):
    """Fires native browser notification when historical sync completes."""
    safe_title = title.replace('"', '\\"')
    safe_body = body.replace('"', '\\"')
    components.html(f"""
    <script>
    (function() {{
        var notif = (window.parent && window.parent.Notification) ? window.parent.Notification : window.Notification;
        if (notif) {{
            if (notif.permission === "granted") {{
                new notif("{safe_title}", {{
                    body: "{safe_body}",
                    icon: "/static/stravalogo-300x300.png"
                }});
            }} else if (notif.permission !== "denied") {{
                notif.requestPermission().then(function(perm) {{
                    if (perm === "granted") {{
                        new notif("{safe_title}", {{
                            body: "{safe_body}",
                            icon: "/static/stravalogo-300x300.png"
                        }});
                    }}
                }});
            }}
        }}
    }})();
    </script>
    """, height=0, width=0)


@st.fragment(run_every=4)
def render_sync_status_monitor(jwt, user_id):
    """
    Background polling loop querying /api/history/sync-status/:userId every 4 seconds.
    Renders non-intrusive interactive modal, handles notification toggle, and post-sync transitions.
    """
    if not jwt:
        return

    target_id = user_id or "me"
    server_status = "idle"
    try:
        res = requests.get(
            f"{BACKEND}/api/history/sync-status/{target_id}",
            headers={"Authorization": f"Bearer {jwt}"},
            timeout=5
        )
        if res.status_code == 200:
            server_status = res.json().get("status", "idle")
    except Exception:
        server_status = st.session_state.get("sync_status", "idle")

    # Sync state transitions
    if server_status == "processing":
        st.session_state["sync_in_progress"] = True
        st.session_state["sync_status"] = "processing"
        st.session_state["notified_for_current_sync"] = False

    elif server_status == "completed":
        was_processing = st.session_state.get("sync_in_progress") or (st.session_state.get("sync_status") == "processing")
        st.session_state["sync_in_progress"] = False
        st.session_state["sync_status"] = "completed"

        if was_processing and st.session_state.get("notify_me", True) and not st.session_state.get("notified_for_current_sync", False):
            send_browser_notification(
                "Garmin Telemetry Synchronized",
                "Historical workout archive processed and baseline ML models trained. Dashboard unlocked!"
            )
            st.session_state["notified_for_current_sync"] = True

    elif server_status == "failed":
        st.session_state["sync_in_progress"] = False
        st.session_state["sync_status"] = "failed"

    # ----------------------------------------------------
    # Case 1: Active Ingestion Modal (Non-intrusive popup)
    # ----------------------------------------------------
    if st.session_state.get("sync_status") == "processing":
        st.markdown("""
        <div style="background: #0B0E15; border: 1px solid #1E283A; border-left: 4px solid #FF4B00; border-radius: 8px; padding: 20px 22px; margin-bottom: 22px; box-shadow: 0 4px 24px rgba(0,0,0,0.45);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span class="tech-tag active">PIPELINE PROCESSING</span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #94A3B8;">
                        POLLING STATUS // 4-SECOND INTERVAL
                    </span>
                </div>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #10B981; letter-spacing: 0.05em;">
                    SAFE TO NAVIGATE AWAY
                </span>
            </div>
            <div style="font-size: 1.15rem; font-weight: 600; color: #F8FAFC; margin-bottom: 6px;">
                Garmin Historical Telemetry Ingestion Active
            </div>
            <p style="color: #94A3B8; font-size: 0.85rem; line-height: 1.55; margin: 0 0 14px 0;">
                The server is extracting cycling FIT files, calculating training loads, and training your Random Forest power regressor. You can safely continue working, calibrate sensors in the sidebar, or navigate to other workspaces without interrupting execution.
            </p>
            <div style="background: #07090E; border: 1px solid #161D2B; border-radius: 6px; padding: 12px 16px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #FF4B00; text-transform: uppercase;">
                    CURRENT EXECUTION STAGE
                </div>
                <div style="font-size: 0.84rem; color: #CBD5E1; margin-top: 3px; font-weight: 500;">
                    Micro-Batch Feature Engineering & Global ML Initialization
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        ctrl_col1, ctrl_col2 = st.columns([3, 1])
        with ctrl_col1:
            notify_val = st.toggle(
                "Notify me via browser notification upon completion",
                value=st.session_state.get("notify_me", True),
                key="sync_notify_toggle"
            )
            if notify_val != st.session_state.get("notify_me"):
                st.session_state["notify_me"] = notify_val
                if notify_val:
                    request_notification_permission()

        with ctrl_col2:
            if st.button("Poll Endpoint Now", use_container_width=True, key="btn_manual_poll"):
                st.rerun(scope="fragment")

    # ----------------------------------------------------
    # Case 2: Post-Sync Transition Card
    # ----------------------------------------------------
    elif st.session_state.get("sync_status") == "completed":
        st.markdown("""
        <div style="background: #0B0E15; border: 1px solid #161D2B; border-left: 4px solid #10B981; border-radius: 8px; padding: 20px 22px; margin-bottom: 22px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span class="tech-tag live">PIPELINE COMPLETED</span>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #10B981;">
                    STATUS: READY // BASELINE MODEL TRAINED
                </span>
            </div>
            <div style="font-size: 1.15rem; font-weight: 600; color: #F8FAFC; margin-bottom: 6px;">
                Historical Baseline Calibrated Successfully
            </div>
            <p style="color: #94A3B8; font-size: 0.85rem; line-height: 1.55; margin: 0 0 16px 0;">
                All cycling workouts from your Garmin data archive have been processed. Rolling fatigue curves, baseline variance, and adaptive workout prescriptions are unlocked and ready for inspection.
            </p>
        </div>
        """, unsafe_allow_html=True)

        trans_c1, trans_c2 = st.columns([1, 1])
        with trans_c1:
            if st.button("Explore Coach & Telemetry Dashboard ➔", type="primary", use_container_width=True, key="btn_goto_dash_post_sync"):
                st.cache_data.clear()
                st.session_state["selected_page"] = "Adaptive Cycling Coach"
                st.rerun()

        with trans_c2:
            if st.button("Dismiss Status Banner", use_container_width=True, key="btn_dismiss_completed_hub"):
                st.session_state["sync_status"] = "idle"
                st.rerun()

    # ----------------------------------------------------
    # Case 3: Pipeline Failure Notice
    # ----------------------------------------------------
    elif st.session_state.get("sync_status") == "failed":
        st.markdown("""
        <div style="background: #0B0E15; border: 1px solid #161D2B; border-left: 4px solid #EF4444; border-radius: 8px; padding: 20px 22px; margin-bottom: 22px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span class="tech-tag" style="color: #EF4444; border-color: rgba(239, 68, 68, 0.35);">PIPELINE FAILED</span>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #EF4444;">
                    EXECUTION TERMINATED
                </span>
            </div>
            <div style="font-size: 1.15rem; font-weight: 600; color: #F8FAFC; margin-bottom: 6px;">
                Historical Ingestion Error
            </div>
            <p style="color: #94A3B8; font-size: 0.85rem; line-height: 1.55; margin: 0 0 14px 0;">
                The backend encountered an issue processing the uploaded package (e.g. no cycling FIT files matched summarizedActivities.json or an unexpected file format).
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Reset Status & Retry Upload", type="primary", key="btn_reset_failed_sync"):
            st.session_state["sync_status"] = "idle"
            st.session_state["sync_in_progress"] = False
            st.rerun()


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
    user_id = get_user_id_from_jwt(jwt) if jwt else None

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
            st.markdown("""
            <div style="background: #0B0E15; border: 1px solid #161D2B; border-left: 3px solid #10B981; border-radius: 6px; padding: 14px 18px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; font-weight: 600; color: #10B981;">
                        STATUS: AUTHENTICATED // GARMIN CONNECT
                    </div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #64748B; margin-top: 2px;">
                        SESSION: SECURE // HEALTH API CONNECTION ACTIVE
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
                st.session_state["sync_status"] = "idle"
                st.session_state["sync_in_progress"] = False
                st.rerun()
        else:
            if st.button("Reload Status", use_container_width=True):
                st.rerun()

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # BACKGROUND STATUS POLLING & INTERACTIVE MODAL COMPONENT
    # (Polls /api/history/sync-status/:userId every 4s)
    # --------------------------------------------------------
    if is_connected:
        render_sync_status_monitor(jwt, user_id)

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
                    disabled=(uploaded_zip is None or st.session_state.get("sync_status") == "processing")
                )

                if upload_btn and uploaded_zip is not None:
                    with st.spinner("Uploading Garmin archive package to backend pipeline..."):
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
                                timeout=120
                            )

                            if res.status_code in [200, 202]:
                                st.session_state["sync_in_progress"] = True
                                st.session_state["sync_status"] = "processing"
                                st.session_state["notified_for_current_sync"] = False
                                st.toast("Upload received! Background pipeline initiated.")
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
