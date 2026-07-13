import streamlit as st

def show_privacy_page():
    st.title("Privacy Policy")
    st.caption("Last Updated: July 2026")
    st.divider()

    st.markdown("Adaptive Cycling Coach respects your privacy and is committed to protecting your personal data.")

    st.subheader("Information Collected")
    st.markdown("The platform may process cycling activity information such as:")
    st.markdown("""
    * Activity date and duration
    * Distance
    * Elevation gain
    * Heart rate
    * Power
    * Cadence
    * Speed
    * Other ride metrics provided by the user or connected fitness services
    """)
    
    st.markdown("> **Note:** The platform does not intentionally collect unnecessary personal information beyond what is required to provide cycling analytics and recommendations.")

    st.subheader("How Data Is Used")
    st.markdown("Activity data is used solely to:")
    st.markdown("""
    * Analyze historical cycling performance
    * Estimate fatigue and current performance capacity
    * Generate personalized ride recommendations
    * Improve the accuracy of the recommendation algorithms
    """)

    st.subheader("Data Sharing")
    st.markdown("User activity data is not sold or shared with advertisers.")
    st.markdown("If third-party fitness platforms are connected in the future, activity data will only be accessed after explicit user authorization and only for the purpose of providing the requested analytics.")

    st.subheader("Data Security")
    st.markdown("Reasonable technical and organizational measures are implemented to protect user data from unauthorized access or disclosure.")

    st.subheader("Third-Party Services")
    st.markdown("Future versions of Adaptive Cycling Coach may integrate with third-party fitness platforms and wearable device ecosystems. Such integrations will only occur after user consent and will comply with the respective platform's developer policies.")