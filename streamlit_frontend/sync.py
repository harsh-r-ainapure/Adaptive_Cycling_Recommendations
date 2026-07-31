import streamlit as st
import requests
import webbrowser

BACKEND = "https://adaptive-cycling-recommendations.onrender.com"


def show_sync_page():

    st.title("Sync")

    if st.button("Connect Intervals"):

        webbrowser.open(
            f"{BACKEND}/api/user/signup"
        )

    params = st.query_params

    if "token" in params:

        st.session_state["jwt"] = params["token"]

        st.success("Connected to Intervals")

    if st.button("Sync Activities"):

        response = requests.post(
            f"{BACKEND}/api/sync/activities",
            headers={
                "Authorization": f"Bearer {st.session_state['jwt']}"
            }
        )

        st.write(response.json())