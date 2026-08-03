import datetime
import streamlit as st
import requests


def show_form_page():
    st.title("Tell us a bit about your setup.")

    with st.form(key="setup_form", clear_on_submit=False):

        # Name Input
        name = st.text_input("Name", placeholder="Enter your full name")

        # Power Data Radio Button
        has_power = st.radio(
            "Do your rides contain power data?",
            ["Yes", "No", "I'm not sure"],
            index=1,
        )

        start_month = None
        start_year = None

        # Conditional section if 'Yes' is selected
        if has_power == "Yes":
            st.divider()
            st.markdown(
                "**Approximately when did you start recording power?**"
            )

            col1, col2 = st.columns(2)

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
                "December",
            ]

            # Dynamic list of years (current year down to 2010)
            current_year = datetime.datetime.now().year
            years = list(range(current_year, 2009, -1))

            with col1:
                start_month = st.selectbox("Month", options=months)

            with col2:
                start_year = st.selectbox("Year", options=years)

        st.write("")

        # Submit Button
        submitted = st.form_submit_button(
            "Continue", use_container_width=True, type="primary"
        )

        if submitted:
            if not name.strip():
                st.error("Please enter your name to proceed.")
            else:
                # Save outputs to Streamlit session_state
                st.session_state["user_name"] = name.strip()
                st.session_state["has_power"] = has_power

                if has_power == "Yes":
                    st.session_state["power_start_month"] = start_month
                    st.session_state["power_start_year"] = start_year

                    BACKEND = "https://adaptive-cycling-recommendations.onrender.com"

                    jwt = st.session_state.get("jwt")

                    month_number = None

                    if has_power == "Yes":
                        month_number = months.index(start_month) + 1

                    payload = {
                            "name": name.strip(),
                            "has_power_meter": has_power == "Yes",
                            "power_meter_month": month_number,
                            "power_meter_year": start_year if has_power == "Yes" else None,
                            }





                    response = requests.post(
                          f"{BACKEND}/api/user/profile",
                          json=payload,
                          headers={
                          "Authorization": f"Bearer {jwt}"
                           },
                         timeout=30,
                                           )

                    if response.ok:
                      st.success("Profile saved successfully!")
                    else:
                       st.error(response.text)
                

 