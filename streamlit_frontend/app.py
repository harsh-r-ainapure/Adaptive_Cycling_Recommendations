import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta

# Configure the page layout
st.set_page_config(page_title="Performance Dashboard", page_icon="🏃", layout="centered")

st.title("Performance Dashboard")
st.markdown("Compare your current baseline metrics against the recommended targets based on recent ML outputs.")
st.divider()

# Create two side-by-side columns
col1, col2 = st.columns(2)

with col1:
    st.subheader("Current Baseline")
    with st.container(border=True):
        st.metric(label="Baseline Distance", value="15.185")
        st.metric(label="Baseline Elevation", value="109.0")
        st.metric(label="Baseline HR", value="146.5")

with col2:
    st.subheader("Recommendations")
    with st.container(border=True):
        # The delta parameter shows the difference from the baseline
        st.metric(label="Recommended Distance", value="16.0", delta="0.815")
        st.metric(label="Recommended Elevation", value="114.0", delta="5.0")
        
        # For Heart Rate, a higher number means more exertion. 
        # delta_color="inverse" makes an increase red (harder) instead of green.
        st.metric(
            label="Recommended HR", 
            value="154.0", 
            delta="7.5",
            delta_color="inverse"
        )

@st.cache_data
def load_data():
    # Load the specific CSV file
    df = pd.read_csv('../data/final_features.csv')
    
    # Convert the Activity Date column to datetime objects
    df['Activity Date'] = pd.to_datetime(df['Activity Date'])
    
    # Sort the data chronologically just in case
    df = df.sort_values(by='Activity Date')
    return df

st.subheader("6-Month Fatigue Trend")

try:
    df = load_data()
    
    # 2. Filter for the last six months
    # Find the most recent ride in the dataset
    latest_date = df['Activity Date'].max()
    
    # Calculate the date exactly 6 months (approx 180 days) prior
    six_months_ago = latest_date - timedelta(days=180)
    
    # Slice the dataframe to only include the last 6 months
    recent_df = df[df['Activity Date'] >= six_months_ago]
    
    # 3. Plot the data using Plotly for interactivity
    fig = px.line(
        recent_df, 
        x='Activity Date', 
        y='Fatigue', 
        markers=True,
        title="Fatigue Levels Over Recent Rides",
        labels={
            'Activity Date': 'Date of Activity', 
            'Fatigue': 'Calculated Fatigue'
        }
    )
    
    # Make the hover tooltip apply to the whole vertical axis line
    fig.update_layout(hovermode="x unified")
    
    # Render the chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)

except FileNotFoundError:
    st.error("The file 'final_features.csv' was not found. Ensure it is in the same directory as this script.")
except KeyError as e:
    st.error(f"Missing expected column in the dataset: {e}")

st.divider() # Adds a clean visual separator between sections
st.subheader("Capacity Deviation Analysis")
st.markdown("A visual breakdown of how your capacity deviates from the baseline over time.")

try:
    # Assuming load_data() is already defined in your script from earlier
    # We will just load it again, and Streamlit's @st.cache_data makes it instant
    df = pd.read_csv('../data/final_features.csv')
    df['Activity Date'] = pd.to_datetime(df['Activity Date'])
    
    # Filter for the last six months
    latest_date = df['Activity Date'].max()
    six_months_ago = latest_date - timedelta(days=180)
    recent_df = df[df['Activity Date'] >= six_months_ago]
    
    # NEW DESIGN: Diverging Bar Chart with color mapping
    fig2 = px.bar(
        recent_df, 
        x='Activity Date', 
        y='Capacity_Deviation',
        color='Capacity_Deviation', # Colors the bars based on the deviation value
        color_continuous_scale=px.colors.diverging.RdYlGn, # Red (low) to Green (high)
        title="Daily Capacity Deviation",
        labels={
            'Activity Date': 'Date', 
            'Capacity_Deviation': 'Deviation Magnitude'
        }
    )
    
    # Apply a dark theme and clean up the layout
    fig2.update_layout(
        template="plotly_dark", 
        xaxis_title="Activity Date",
        yaxis_title="Deviation",
        coloraxis_showscale=False, # Hides the color legend to keep the UI clean
        hovermode="x unified"
    )
    
    st.plotly_chart(fig2, use_container_width=True)

except FileNotFoundError:
    st.error("The file '../data/final_features.csv' was not found.")
except KeyError as e:
    st.error(f"Missing expected column in the dataset: {e}")

import plotly.graph_objects as go

st.divider()
st.subheader("Average Power Trend & Prediction")
st.markdown("Comparing your recorded average power directly against the our predictions, ride by ride.")

try:
    # Load dataset
    df = pd.read_csv('../data/final_features.csv')
    
    # Ensure dates are properly formatted and sorted chronologically
    df['Activity Date'] = pd.to_datetime(df['Activity Date'])
    df = df.sort_values('Activity Date')
    
    # Filter for rows where valid actual power exists
    actual_power_col = 'Average Watts'
    prediction_col = 'Estimated Power'
    
    power_df = df[df[actual_power_col] > 0].copy()

    # Build the scatter chart (no lines)
    fig4 = go.Figure()
    
    # 1. Actual Average Power (Light Blue Dots Only)
    fig4.add_trace(go.Scatter(
        x=power_df['Activity Date'],
        y=power_df[actual_power_col],
        mode='markers', # Removed lines entirely
        name='Actual Power (Avg Watts)',
        marker=dict(color='#87CEEB', size=7, opacity=0.8), # Light blue dots
        hoverinfo='x+y'
    ))
    
    # 2. Predicted Average Power (Green Diamonds Only)
    fig4.add_trace(go.Scatter(
        x=power_df['Activity Date'],
        y=power_df[prediction_col],
        mode='markers', # Removed lines entirely
        name='Predicted Power (RF Model)',
        marker=dict(
            color='#00E676', 
            size=7, 
            symbol='diamond', # Using a diamond shape helps visibility when dots overlap
            opacity=0.8
        ), 
        hoverinfo='x+y'
    ))
    
    # Clean up the layout and enable unified x-axis snapping tooltips
    fig4.update_layout(
        template="plotly_dark",
        xaxis=dict(
            title="", 
            tickformat="%b %Y",
            showgrid=False,
            tickangle=-45 
        ),
        yaxis=dict(
            title="Power (Watts)",
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)'
        ),
        hovermode="x unified", 
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1
        ),
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    st.plotly_chart(fig4, use_container_width=True)

except FileNotFoundError:
    st.error("The file '../data/final_features.csv' was not found.")
except KeyError as e:
    st.error(f"Missing expected column in the dataset: {e}")