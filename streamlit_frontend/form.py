import datetime
import streamlit as st
import requests

BACKEND = "https://adaptive-cycling-recommendations.onrender.com"


def show_form_page():

    st.title("Tell us a bit about your setup.")

    with st.form("setup_form"):

        name = st.text_input(
            "Name",
            placeholder="Enter your full name"
        )

        has_power = st.radio(
            "Do your rides contain power data?",
            [
                "Yes",
                "No",
                "I'm not sure"
            ],
            index=1
        )

        start_month = None
        start_year = None

        months = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December"
        ]

        if has_power == "Yes":

            st.divider()

            st.markdown(
                "**Approximately when did you start recording power?**"
            )

            col1, col2 = st.columns(2)

            current_year = datetime.datetime.now().year

            years = list(
                range(current_year, 2009, -1)
            )

            with col1:
                start_month = st.selectbox(
                    "Month",
                    months
                )

            with col2:
                start_year = st.selectbox(
                    "Year",
                    years
                )

        submitted = st.form_submit_button(
            "Continue",
            type="primary",
            use_container_width=True
        )

    if submitted:

        if not name.strip():

            st.error("Please enter your name.")
            st.stop()

        jwt = st.session_state.get("jwt")

        if not jwt:

            st.error(
                "Please connect your Intervals account first."
            )
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

            response = requests.post(

                f"{BACKEND}/api/user/profile",

                json=payload,

                headers={

                    "Authorization": f"Bearer {jwt}"

                },

                timeout=30

            )

            response.raise_for_status()

            st.success("Profile saved successfully!")

            st.session_state["user_name"] = name.strip()
            st.session_state["has_power"] = has_power
            st.session_state["power_start_month"] = month_number
            st.session_state["power_start_year"] = year_number

            st.session_state["selected_page"] = "Sync"

            st.rerun()

        except requests.exceptions.HTTPError:

            st.error(response.text)

        except Exception as e:

            st.error(f"Unable to save profile.\n\n{e}")

 