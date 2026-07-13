import streamlit as st

def show_about_page():
    st.title(" About")
    st.divider()
    
    st.markdown("""
    **Adaptive Cycling Coach** is an independent software project focused on personalized cycling performance analysis and training recommendations.
    
    The platform analyzes historical cycling activities to estimate rider fatigue, current performance capacity, and recovery status. Using these insights, it generates personalized recommendations for the rider's next session, including suggested distance, elevation gain, and target heart rate.
    """)
    
    # Using st.info creates a nice highlighted box for your main value proposition
    st.info(
        " **The ML Advantage:** Unlike applications that rely solely on historical statistics, "
        "Adaptive Cycling Coach incorporates machine learning and a physiology-inspired fatigue "
        "model to estimate changes in rider capacity over time. The objective is to help cyclists "
        "train more consistently while reducing unnecessary fatigue and improving long-term performance."
    )
    
    st.markdown("<br>", unsafe_allow_html=True) # Adds a little breathing room
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Current Features")
        st.markdown("""
        *  **Ride performance visualization**
        *  **Fatigue trend analysis**
        *  **Capacity deviation tracking**
        *  **Average power prediction** using machine learning
        * **Personalized ride recommendations**
        """)
        
    st.divider()
    
    # Using st.warning draws attention to the fact that it is a living project
    st.warning(
        "**Active Development** \n\n"
        "This project is currently under active development. Future updates include: \n"
        "* Secure activity synchronization \n"
        "* Automated ride ingestion \n"
        "* Expanded analytics \n"
        "* Support for additional cycling data sources"
    )