import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta
import about
import privacy
import contact
import home
import sync
import plotly.graph_objects as go
import requests
import form

# Configure the page layout
st.set_page_config(page_title="Performance Dashboard", page_icon="🏃", layout="centered")


BACKEND_URL = "https://adaptive-cycling-recommendations.onrender.com"

@st.cache_data(ttl=10)
def load_data(jwt):

    response = requests.get(
        f"{BACKEND_URL}/dashboard",
        headers={
            "Authorization": f"Bearer {jwt}"
        },
        timeout=None
    )

    response.raise_for_status()

    df = pd.DataFrame(response.json())

    if not df.empty:
        df["activity_date"] = pd.to_datetime(df["activity_date"])

    return df


# --- SIDEBAR NAVIGATION ---
st.sidebar.title(" Navigation")
st.sidebar.markdown("Select a page to view:")

# Create the clickable menu
selected_page = st.sidebar.radio(
    "Go to",
    [
        "Home", 
        "Sync",
        "Setup Form"
        "Adaptive Cycling Coach", 
        "About", 
        "Privacy Policy", 
        "Contact"
    ],
    label_visibility="collapsed" 
)

st.sidebar.divider()
st.sidebar.caption("© 2026 Your Strava ML Project")

if selected_page == "Home":
    home.show_homepage()   

elif selected_page == "Adaptive Cycling Coach":
    st.title("Adaptive Cycling Coach")
    st.write("Your personalized ML recommendations will go here.")
    st.title("Performance Dashboard")
    st.markdown("Compare your current baseline metrics against the recommended targets based on recent ML outputs.")
    st.divider()

    if "jwt" not in st.session_state:
     st.warning("Please connect your Intervals account first from the Sync page.")
     st.stop()

    headers = {
    "Authorization": f"Bearer {st.session_state['jwt']}"
}

    try:
        response = requests.get(
        f"{BACKEND_URL}/recommendation",
        headers=headers,
        timeout=60,
          )

        if response.status_code == 200:
            recommendation = response.json()["recommendation"]

            baseline_distance = recommendation["baseline_distance"] / 1000
            baseline_elevation = recommendation["baseline_elevation"]
            baseline_hr = recommendation["baseline_hr"]

            recommended_distance = recommendation["recommended_distance"] / 1000
            recommended_elevation = recommendation["recommended_elevation"]
            recommended_hr = recommendation["recommended_hr"]

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Current Baseline")
                with st.container(border=True):
                    st.metric(
                        "Baseline Distance (km)",
                        round(baseline_distance, 2)
                    )

                    st.metric(
                        "Baseline Elevation",
                        round(baseline_elevation, 2)
                    )

                    st.metric(
                        "Baseline HR",
                        round(baseline_hr, 2)
                    )

            with col2:
                st.subheader("Recommendations")
                with st.container(border=True):
                    st.metric(
                        "Recommended Distance (km)",
                        round(recommended_distance, 2),
                        delta=round(
                            recommended_distance - baseline_distance,
                            2
                        )
                    )

                    st.metric(
                        "Recommended Elevation",
                        round(recommended_elevation, 2),
                        delta=round(
                            recommended_elevation - baseline_elevation,
                            2
                        )
                    )

                    st.metric(
                        "Recommended HR",
                        round(recommended_hr, 2),
                        delta=round(
                            recommended_hr - baseline_hr,
                            2
                        ),
                        delta_color="inverse"
                    )

        else:
          st.error(f"Status Code: {response.status_code}")
          st.write(response.text)

    except Exception as e:
        st.error(f"Backend error: {e}")

    # --- 6-MONTH FATIGUE TREND ---
    st.divider()
    st.subheader("6-Month Fatigue Trend")

    try:
        df = load_data(st.session_state["jwt"])
        latest_date = df['activity_date'].max()
        six_months_ago = latest_date - timedelta(days=180)
        recent_df = df[df['activity_date'] >= six_months_ago]
        
        fig = px.line(
            recent_df, 
            x='activity_date', 
            y='fatigue', 
            markers=True,
            title="Fatigue Levels Over Recent Rides",
            labels={'activity_date': 'Date of Activity', 'fatigue': 'Calculated Fatigue'}
        )
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
   
    except KeyError as e:
        st.error(f"Missing expected column in the dataset: {e}")

    # --- CAPACITY DEVIATION ANALYSIS ---
    st.divider()
    st.subheader("Capacity Deviation Analysis")
    st.markdown("A visual breakdown of how your capacity deviates from the baseline over time.")

    try:
        df = load_data(st.session_state["jwt"])
        latest_date = df['activity_date'].max()
        six_months_ago = latest_date - timedelta(days=180)
        recent_df = df[df['activity_date'] >= six_months_ago]
        
        fig2 = px.bar(
            recent_df, 
            x='activity_date', 
            y='capacity_deviation',
            color='capacity_deviation',
            color_continuous_scale=px.colors.diverging.RdYlGn,
            title="Daily Capacity Deviation",
            labels={'activity_date': 'Date', 'capacity_deviation': 'Deviation Magnitude'}
        )
        fig2.update_layout(
            template="plotly_dark", 
            xaxis_title="activity_date",
            yaxis_title="Deviation",
            coloraxis_showscale=False,
            hovermode="x unified"
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    except KeyError as e:
        st.error(f"Missing expected column in the dataset: {e}")

    # --- POWER TREND & PREDICTION ---
    st.divider()
    st.subheader("Average Power Trend & Prediction")
    st.markdown("Comparing your recorded average power directly against our predictions, ride by ride.")

    try:
        df = load_data(st.session_state["jwt"])
        actual_power_col = 'average_power'
        prediction_col = 'estimated_power'
        power_df = df[df[actual_power_col] > 0].copy()

        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=power_df['activity_date'], y=power_df[actual_power_col],
            mode='markers', name='Actual Power (Avg Watts)',
            marker=dict(color='#87CEEB', size=7, opacity=0.8), hoverinfo='x+y'
        ))
        fig4.add_trace(go.Scatter(
            x=power_df['activity_date'], y=power_df[prediction_col],
            mode='markers', name='Predicted Power (RF Model)',
            marker=dict(color='#00E676', size=7, symbol='diamond', opacity=0.8), hoverinfo='x+y'
        ))
        fig4.update_layout(
            template="plotly_dark",
            xaxis=dict(title="", tickformat="%b %Y", showgrid=False, tickangle=-45),
            yaxis=dict(title="Power (Watts)", showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig4, use_container_width=True)
   
    except KeyError as e:
        st.error(f"Missing expected column in the dataset: {e}")

elif selected_page == "About":
    about.show_about_page()

elif selected_page == "Privacy Policy":
    privacy.show_privacy_page()

elif selected_page == "Contact":
    contact.show_contact_page()

elif selected_page == "Sync":
    sync.show_sync_page()
elif selected_page == "Setup Form":  
    form.show_form_page()