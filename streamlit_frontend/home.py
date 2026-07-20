import streamlit as st

def show_homepage():
    # 1. Top Right Logout Button
    header_col1, header_col2 = st.columns([8, 1])
    with header_col2:
        if st.button("Logout", use_container_width=True):
            st.success("Logged out successfully.") 

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Centered Logo
    logo_col1, logo_col2, logo_col3 = st.columns([1, 2, 1])
    with logo_col2:
        # Changed use_container_width to use_column_width
        st.image("stravalogo.png", use_column_width=True)

    # 3. Welcome Header
    st.markdown("<h1 style='text-align: center;'>Welcome back, Harsh</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Select a module to continue</p>", unsafe_allow_html=True)
    
    st.divider()

    # 4. Main Navigation Options
    btn_col1, btn_col2, btn_col3 = st.columns(3)

    with btn_col1:
        if st.button("View Recommendations", use_container_width=True, type="primary"):
            st.info("Routing to ML Recommendations...")
            
    with btn_col2:
        if st.button("History Charts", use_container_width=True):
            st.info("Routing to Performance Dashboard...")
            
    with btn_col3:
        if st.button("Sync Strava Data", use_container_width=True):
            st.info("Fetching latest activities from API...")