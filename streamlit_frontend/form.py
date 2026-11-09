import datetime
import streamlit as st
import requests

BACKEND = "https://adaptive-cycling-recommendations.onrender.com"


def show_form_page():
    jwt = st.session_state.get("jwt")
    is_connected = bool(jwt)

    # Header
    st.markdown("""
        <div style="margin-bottom: 24px;">
            <span class="badge-primary">Profile Calibration</span>
            <h1 style="margin: 8px 0 0 0; font-size: 2.2rem; font-weight: 800; color: #F8FAFC;">
                ⚙️ Athlete & Equipment Setup
            </h1>
            <p style="color: #94A3B8; font-size: 1rem; margin-top: 6px;">
                Calibrate your baseline calculations by specifying your power meter history and profile details.
            </p>
        </div>
    """, unsafe_allow_html=True)

    if not is_connected:
        st.warning("⚠️ You are not yet connected to Intervals.icu. You can fill the form, but submitting requires an active connection.")

    # Form in a modern centered card layout
    form_col1, form_col2 = st.columns([7, 3], gap="large")

    with form_col1:
        default_name = st.session_state.get("user_name", "")

        with st.form("setup_form", border=True):
            st.markdown("<h3 style='font-size: 1.15rem; font-weight: 700; color: #F8FAFC; margin-bottom: 16px;'>Rider Details</h3>", unsafe_allow_html=True)

            name = st.text_input(
                "Athlete Full Name",
                value=default_name,
                placeholder="e.g. Harsh Ainapure",
                help="Your display name used in dashboard metrics."
            )

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            power_options = ["Yes", "No", "I'm not sure"]
            default_power_idx = 1
            saved_has_power = st.session_state.get("has_power")
            if saved_has_power in power_options:
                default_power_idx = power_options.index(saved_has_power)

            has_power = st.radio(
                "Do your recorded rides contain power meter data (Watts)?",
                power_options,
                index=default_power_idx,
                help="Power meters provide true mechanical work output, which enhances ML model predictions."
            )

            start_month = None
            start_year = None

            months = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]

            if has_power == "Yes":
                st.divider()
                st.markdown(
                    "<div style='font-weight: 600; color: #F1F5F9; margin-bottom: 10px; font-size: 0.95rem;'>"
                    "📅 Approximately when did you start recording power?"
                    "</div>",
                    unsafe_allow_html=True
                )

                col_m, col_y = st.columns(2)
                current_year = datetime.datetime.now().year
                years = list(range(current_year, 2009, -1))

                saved_m_num = st.session_state.get("power_start_month")
                saved_y_val = st.session_state.get("power_start_year")

                m_idx = (saved_m_num - 1) if (saved_m_num and 1 <= saved_m_num <= 12) else 0
                y_idx = years.index(saved_y_val) if (saved_y_val and saved_y_val in years) else 0

                with col_m:
                    start_month = st.selectbox("Starting Month", months, index=m_idx)
                with col_y:
                    start_year = st.selectbox("Starting Year", years, index=y_idx)

            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

            submitted = st.form_submit_button(
                "Save Profile & Calibrate ➔",
                type="primary",
                use_container_width=True
            )

        if submitted:
            if not name.strip():
                st.error("Please enter your name.")
                st.stop()

            if not jwt:
                st.error("Please connect your Intervals.icu account on the Sync page before saving.")
                st.stop()

            month_number = None
            year_number = None

            if has_power == "Yes":
                month_number = months.index(start_month) + 1
                year_number = start_year

            payload = {
                "name": name.strip(),
                "has_power_meter": has_power == "Yes",
                "power_meter_month": month_number,
                "power_meter_year": year_number
            }

            try:
                with st.spinner("Saving athlete profile to backend..."):
                    response = requests.post(
                        f"{BACKEND}/api/user/profile",
                        json=payload,
                        headers={
                            "Authorization": f"Bearer {jwt}"
                        },
                        timeout=30
                    )
                    response.raise_for_status()

                st.success("Profile calibrated and saved successfully!")
                st.session_state["user_name"] = name.strip()
                st.session_state["has_power"] = has_power
                st.session_state["power_start_month"] = month_number
                st.session_state["power_start_year"] = year_number

                st.session_state["selected_page"] = "Sync"
                st.rerun()

            except requests.exceptions.HTTPError:
                st.error(f"Error from server: {response.text}")
            except Exception as e:
                st.error(f"Unable to save profile.\n\n{e}")

    with form_col2:
        st.markdown("""
        <div style="background: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 20px;">
            <div style="font-weight: 700; color: #F8FAFC; margin-bottom: 12px; font-size: 1rem;">
                💡 Why Calibration Matters
            </div>
            <p style="color: #94A3B8; font-size: 0.85rem; line-height: 1.5; margin-bottom: 14px;">
                Knowing when you equipped a power meter allows our Random Forest model to accurately differentiate between actual measured watts and estimated metrics.
            </p>
            <div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 12px; margin-top: 12px;">
                <div style="font-size: 0.8rem; font-weight: 600; color: #FC4C02;">Next Step:</div>
                <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 4px;">Once saved, navigate to Sync to pull your ride files into the database.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
