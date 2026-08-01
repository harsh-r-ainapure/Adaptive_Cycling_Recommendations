import streamlit as st
import requests

BACKEND = "https://adaptive-cycling-recommendations.onrender.com"

# -------------------------
# Initialize Session
# -------------------------
if "jwt" not in st.session_state:
    st.session_state["jwt"] = None


def show_sync_page():

    st.title("Sync")

    # -------------------------
    # Read JWT safely
    # -------------------------
    jwt = st.session_state.get("jwt")

    # -------------------------
    # OAuth callback
    # -------------------------
    params = st.query_params

    token = params.get("token")

    if token:

        # query_params may return a list depending on Streamlit version
        if isinstance(token, list):
            token = token[0]

        st.session_state["jwt"] = token
        jwt = token

        if "token" in st.query_params:
            del st.query_params["token"]

        st.success(" Successfully connected to Intervals!")

    # -------------------------
    # Connection Status
    # -------------------------
    if jwt:
        st.success(" Intervals account connected.")
    else:
        st.warning(" No Intervals account connected.")

    # -------------------------
    # OAuth Button
    # -------------------------
    st.link_button(
        " Connect Intervals",
        f"{BACKEND}/api/user/signup",
        use_container_width=True,
    )

    st.write("")

    # -------------------------
    # Sync Button
    # -------------------------
    if st.button("Sync Activities", use_container_width=True):

        jwt = st.session_state.get("jwt")

        if not jwt:
            st.error("Please connect your Intervals account first.")
            st.stop()

        with st.spinner("Syncing activities..."):

            try:

                response = requests.post(
                    f"{BACKEND}/api/sync/activities",
                    headers={
                        "Authorization": f"Bearer {jwt}"
                    },
                    timeout=300,   # increase timeout while testing
                )

                response.raise_for_status()

                st.success(" Activities synced successfully!")

                try:
                    st.json(response.json())
                except Exception:
                    st.write(response.text)

            except requests.exceptions.RequestException as e:
                st.error(f"Unable to contact backend.\n\n{e}")