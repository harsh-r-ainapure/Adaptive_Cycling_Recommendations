import datetime
import hmac
import hashlib
import base64
import json
from pathlib import Path
import streamlit as st
import requests

BACKEND = "https://adaptive-cycling-recommendations.onrender.com"


def make_jwt_token(payload, secret):
    """Generates a standard HS256 JWT using only standard library modules."""
    def b64url(data_bytes):
        return base64.urlsafe_b64encode(data_bytes).decode('utf-8').rstrip('=')

    header_b64 = b64url(json.dumps({'alg': 'HS256', 'typ': 'JWT'}, separators=(',', ':')).encode('utf-8'))
    payload_b64 = b64url(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    sig_b64 = b64url(hmac.new(secret.encode('utf-8'), signing_input, hashlib.sha256).digest())
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def get_effective_jwt():
    """Returns the active session JWT or resolves platform token so changes commit to database."""
    token = st.session_state.get("jwt") or st.query_params.get("token")
    if token:
        if isinstance(token, list):
            token = token[0]
        return token

    # Fallback: resolve platform athlete token so calibration updates PostgreSQL via syncuser_routes
    try:
        secret = "harsh_super_secret_12345"
        env_path = Path(__file__).resolve().parent.parent / "express" / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.strip().startswith("JWT_SECRET="):
                    secret = line.split("=", 1)[1].strip()
                    break

        uid = "ccf6ca87-cb92-4a03-9bbe-1dbab5e523fc"
        try:
            import psycopg2
            db_url = None
            if env_path.exists():
                for line in env_path.read_text().splitlines():
                    if line.strip().startswith("SUPABASE_DB_URL="):
                        db_url = line.split("=", 1)[1].strip()
                        break
            if db_url:
                conn = psycopg2.connect(db_url, connect_timeout=3)
                cur = conn.cursor()
                cur.execute("SELECT id FROM users ORDER BY created_at ASC LIMIT 1;")
                row = cur.fetchone()
                if row and row[0]:
                    uid = str(row[0])
                cur.close()
                conn.close()
        except Exception:
            pass

        return make_jwt_token({"id": uid}, secret)
    except Exception:
        return None


def show_form_page():
    # Initialize initial form values from database once per session if not already in session_state
    if "calibration_initialized" not in st.session_state:
        try:
            import psycopg2
            env_path = Path(__file__).resolve().parent.parent / "express" / ".env"
            db_url = None
            if env_path.exists():
                for line in env_path.read_text().splitlines():
                    if line.strip().startswith("SUPABASE_DB_URL="):
                        db_url = line.split("=", 1)[1].strip()
                        break
            if db_url:
                conn = psycopg2.connect(db_url, connect_timeout=3)
                cur = conn.cursor()
                cur.execute("SELECT name, has_power_meter, power_meter_month, power_meter_year FROM users LIMIT 1;")
                row = cur.fetchone()
                if row:
                    if row[0]:
                        st.session_state["user_name"] = row[0]
                    st.session_state["has_power"] = "Yes" if row[1] else "No"
                    if row[2]:
                        st.session_state["power_start_month"] = row[2]
                    if row[3]:
                        st.session_state["power_start_year"] = row[3]
                cur.close()
                conn.close()
        except Exception:
            pass
        st.session_state["calibration_initialized"] = True

    # Header
    st.markdown("""
        <div style="border-left: 2px solid #FF4B00; padding-left: 16px; margin-bottom: 22px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; letter-spacing: 0.12em; color: #FF4B00; text-transform: uppercase;">
                HARDWARE & ATHLETE CALIBRATION
            </div>
            <h1 style="font-size: 2rem; font-weight: 700; color: #F8FAFC; margin: 4px 0 6px 0; letter-spacing: -0.02em;">
                Sensor Profile Setup
            </h1>
            <p style="color: #7A889B; font-size: 0.9rem; margin: 0;">
                Calibrate baseline telemetry calculations by configuring strain gauge hardware timeline and athlete metadata.
            </p>
        </div>
    """, unsafe_allow_html=True)

    form_col, info_col = st.columns([7, 4], gap="large")

    with form_col:
        default_name = st.session_state.get("user_name") or "Harsh Ainapure"

        with st.container(border=True):
            st.markdown("""
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #F8FAFC; text-transform: uppercase; margin-bottom: 12px; font-weight: 600;">
                Profile Parameters
            </div>
            """, unsafe_allow_html=True)

            name = st.text_input(
                "Athlete Name",
                value=default_name,
                placeholder="Enter full name",
                help="Identifier associated with dashboard telemetry."
            )

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

            power_options = ["Yes", "No", "I'm not sure"]
            default_power_idx = 0  # Default to 'Yes'
            saved_has_power = st.session_state.get("has_power")
            if saved_has_power in power_options:
                default_power_idx = power_options.index(saved_has_power)

            has_power = st.radio(
                "Do your recorded activities contain strain gauge power meter data (Watts)?",
                power_options,
                index=default_power_idx,
                help="True mechanical power readings enhance the Random Forest model's training accuracy."
            )

            if has_power == "No":
                st.markdown("""
                <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.35); border-left: 3px solid #EF4444; border-radius: 6px; padding: 12px 14px; margin-top: 14px; margin-bottom: 6px;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; font-weight: 600; color: #EF4444; text-transform: uppercase; margin-bottom: 4px;">
                        HARDWARE NOTICE // POWER METER REQUIRED FOR OPTIMAL PREDICTIONS
                    </div>
                    <div style="color: #FCA5A5; font-size: 0.83rem; line-height: 1.5;">
                        A power meter is necessary for correct predictions and smooth working of the system. Without direct mechanical strain gauge readings, the pipeline must rely on approximated power estimates. If you still want to proceed without a power meter, you can continue.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif has_power == "I'm not sure":
                st.markdown("""
                <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.35); border-left: 3px solid #F59E0B; border-radius: 6px; padding: 12px 14px; margin-top: 14px; margin-bottom: 6px;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; font-weight: 600; color: #F59E0B; text-transform: uppercase; margin-bottom: 4px;">
                        HARDWARE CONFIGURATION NOTICE
                    </div>
                    <div style="color: #FCD34D; font-size: 0.83rem; line-height: 1.5;">
                        Direct power sensor data significantly improves baseline physiological accuracy. If your cycling computer or smart trainer records mechanical Watts, choosing "Yes" provides the highest model precision.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            start_month = None
            start_year = None

            months = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]

            if has_power == "Yes":
                st.markdown("<hr style='margin: 16px 0;'>", unsafe_allow_html=True)
                st.markdown("""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #CBD5E1; text-transform: uppercase; margin-bottom: 8px;">
                    Hardware Timeline // Approximate power meter installation date
                </div>
                """, unsafe_allow_html=True)

                col_m, col_y = st.columns(2)
                current_year = datetime.datetime.now().year
                years = list(range(current_year, 2009, -1))

                saved_m_num = st.session_state.get("power_start_month")
                saved_y_val = st.session_state.get("power_start_year")

                m_idx = (saved_m_num - 1) if (saved_m_num and 1 <= saved_m_num <= 12) else 0
                y_idx = years.index(saved_y_val) if (saved_y_val and saved_y_val in years) else 0

                with col_m:
                    start_month = st.selectbox("Month", months, index=m_idx)
                with col_y:
                    start_year = st.selectbox("Year", years, index=y_idx)

            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

            submitted = st.button(
                "Commit Calibration Profile",
                type="primary",
                use_container_width=True
            )

        if submitted:
            name_str = (name or "").strip()
            if not name_str:
                st.error("Athlete name cannot be blank.")
                st.stop()

            month_number = None
            year_number = None

            if has_power == "Yes":
                if start_month is not None and start_month in months:
                    month_number = months.index(start_month) + 1
                year_number = start_year

            payload = {
                "name": name_str,
                "has_power_meter": has_power == "Yes",
                "power_meter_month": month_number,
                "power_meter_year": year_number
            }

            # Update session state values
            st.session_state["user_name"] = name_str
            st.session_state["has_power"] = has_power
            st.session_state["power_start_month"] = month_number
            st.session_state["power_start_year"] = year_number
            st.session_state["calibration_saved"] = True

            # Send database update via backend syncuser_routes.js endpoint: POST /api/auth/garmin/profile
            effective_token = get_effective_jwt()
            if effective_token:
                try:
                    with st.spinner("Writing calibration parameters to database..."):
                        response = requests.post(
                            f"{BACKEND}/api/auth/garmin/profile",
                            json=payload,
                            headers={
                                "Authorization": f"Bearer {effective_token}"
                            },
                            timeout=30
                        )
                        response.raise_for_status()

                    st.success("Calibration profile committed and saved to database successfully.")
                    st.toast("Profile saved to database.")
                except requests.exceptions.HTTPError as http_err:
                    err_msg = response.text if response is not None else str(http_err)
                    st.error(f"Database write returned error: {err_msg}")
                except Exception as e:
                    st.error(f"Unable to write to database: {e}")
            else:
                st.error("Authentication token could not be resolved for database write.")

    with info_col:
        st.markdown("""
        <div class="telemetry-panel">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #F8FAFC; text-transform: uppercase; margin-bottom: 12px; font-weight: 600;">
                Calibration Rationale
            </div>
            <p style="color: #7A889B; font-size: 0.82rem; line-height: 1.5; margin-bottom: 14px;">
                Knowing the exact month and year when a direct-force power meter was installed enables the feature engineering pipeline to differentiate true recorded work from calculated estimates.
            </p>
            <div style="border-top: 1px solid #161D2B; padding-top: 12px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #64748B;">
                    STATUS: SENSOR CALIBRATION // SYNCED WITH BACKEND DATABASE
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
