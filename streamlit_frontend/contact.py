import streamlit as st

def show_contact_page():
    st.title("Contact")
    st.divider()
    
    st.markdown("For questions regarding this Privacy Policy or data handling practices, please contact:")
    
    # Making the email a clickable link for convenience
    st.markdown("**Email:** [contact@yourdomain.com](mailto:contact@yourdomain.com)")