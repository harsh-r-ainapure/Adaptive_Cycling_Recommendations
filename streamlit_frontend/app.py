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

# Configure the page layout
st.set_page_config(page_title="Performance Dashboard", page_icon="🏃", layout="centered")


# --- HELPER FUNCTIONS ---
@st.cache_data
def load_data():
    df = pd.read_csv('../data/final_features.csv')
    df['Activity Date'] = pd.to_datetime(df['Activity Date'])
    df = df.sort_values(by='Activity Date')
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

  
    BACKEND_URL = "https://adaptive-cycling-recommendations.onrender.com"  

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

            baseline_distance = recommendation["baseline_distance"]
            baseline_elevation = recommendation["baseline_elevation"]
            baseline_hr = recommendation["baseline_hr"]

            recommended_distance = recommendation["recommended_distance"]
            recommended_elevation = recommendation["recommended_elevation"]
            recommended_hr = recommendation["recommended_hr"]

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Current Baseline")
                with st.container(border=True):
                    st.metric(
                        "Baseline Distance",
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
                        "Recommended Distance",
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
        df = load_data()
        latest_date = df['Activity Date'].max()
        six_months_ago = latest_date - timedelta(days=180)
        recent_df = df[df['Activity Date'] >= six_months_ago]
        
        fig = px.line(
            recent_df, 
            x='Activity Date', 
            y='Fatigue', 
            markers=True,
            title="Fatigue Levels Over Recent Rides",
            labels={'Activity Date': 'Date of Activity', 'Fatigue': 'Calculated Fatigue'}
        )
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    except FileNotFoundError:
        st.error("The file '../data/final_features.csv' was not found.")
    except KeyError as e:
        st.error(f"Missing expected column in the dataset: {e}")

    # --- CAPACITY DEVIATION ANALYSIS ---
    st.divider()
    st.subheader("Capacity Deviation Analysis")
    st.markdown("A visual breakdown of how your capacity deviates from the baseline over time.")

    try:
        df = load_data()
        latest_date = df['Activity Date'].max()
        six_months_ago = latest_date - timedelta(days=180)
        recent_df = df[df['Activity Date'] >= six_months_ago]
        
        fig2 = px.bar(
            recent_df, 
            x='Activity Date', 
            y='Capacity_Deviation',
            color='Capacity_Deviation',
            color_continuous_scale=px.colors.diverging.RdYlGn,
            title="Daily Capacity Deviation",
            labels={'Activity Date': 'Date', 'Capacity_Deviation': 'Deviation Magnitude'}
        )
        fig2.update_layout(
            template="plotly_dark", 
            xaxis_title="Activity Date",
            yaxis_title="Deviation",
            coloraxis_showscale=False,
            hovermode="x unified"
        )
        st.plotly_chart(fig2, use_container_width=True)
    except FileNotFoundError:
        st.error("The file '../data/final_features.csv' was not found.")
    except KeyError as e:
        st.error(f"Missing expected column in the dataset: {e}")

    # --- POWER TREND & PREDICTION ---
    st.divider()
    st.subheader("Average Power Trend & Prediction")
    st.markdown("Comparing your recorded average power directly against our predictions, ride by ride.")

    try:
        df = load_data()
        actual_power_col = 'Average Watts'
        prediction_col = 'Estimated Power'
        power_df = df[df[actual_power_col] > 0].copy()

        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=power_df['Activity Date'], y=power_df[actual_power_col],
            mode='markers', name='Actual Power (Avg Watts)',
            marker=dict(color='#87CEEB', size=7, opacity=0.8), hoverinfo='x+y'
        ))
        fig4.add_trace(go.Scatter(
            x=power_df['Activity Date'], y=power_df[prediction_col],
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
    except FileNotFoundError:
        st.error("The file '../data/final_features.csv' was not found.")
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