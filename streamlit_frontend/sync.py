import streamlit as st
import requests

st.success("NEW CODE IS RUNNING")

BACKEND = "https://adaptive-cycling-recommendations.onrender.com"

# Initialize session state
if "jwt" not in st.session_state:
    st.session_state["jwt"] = None


def show_sync_page():

    st.title(" Sync")

    # -------------------------
    # Handle callback token
    # -------------------------
    params = st.query_params

    if "token" in params:
        st.session_state["jwt"] = params["token"]

        st.code(st.session_state["jwt"])

        # Remove token from URL after saving it
        del st.query_params["token"]

        st.success(" Successfully connected to Intervals!")

    # -------------------------
    # Connection Status
    # -------------------------
    if st.session_state["jwt"]:
        st.success(" Intervals account connected.")
    else:
        st.warning(" No Intervals account connected.")

    # -------------------------
    # OAuth Login Button
    # -------------------------
    st.link_button(
        "🔗 Connect Intervals",
        f"{BACKEND}/api/user/signup",
        use_container_width=True,
    )

    st.write("")

    # -------------------------
    # Sync Button
    # -------------------------
    if st.button(" Sync Activities", use_container_width=True):

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
                    timeout=60,
                )

                if response.ok:
                    st.success(" Activities synced successfully!")
                    try:
                        st.json(response.json())
                    except Exception:
                        st.write(response.text)
                else:
                    st.error(f"Backend returned {response.status_code}")
                    st.write(response.text)

            except requests.exceptions.RequestException as e:
                st.error(f"Unable to contact backend.\n\n{e}")