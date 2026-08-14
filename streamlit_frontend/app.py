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


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Performance Dashboard",
    page_icon="🚴",
    layout="centered"
)


# ============================================================
# BACKEND
# ============================================================

BACKEND_URL = "https://adaptive-cycling-recommendations.onrender.com"


# ============================================================
# LOAD DASHBOARD DATA
# ============================================================

@st.cache_data(ttl=10)
def load_data(jwt):

    response = requests.get(
        f"{BACKEND_URL}/dashboard",
        headers={
            "Authorization": f"Bearer {jwt}"
        },
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    df = pd.DataFrame(data)

    if df.empty:
        return df

    # Convert activity date safely
    if "activity_date" in df.columns:
        df["activity_date"] = pd.to_datetime(
            df["activity_date"],
            errors="coerce"
        )

    return df


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

PAGES = [
    "Home",
    "Sync",
    "Setup Form",
    "Adaptive Cycling Coach",
    "About",
    "Privacy Policy",
    "Contact"
]

if "selected_page" not in st.session_state:
    st.session_state["selected_page"] = "Home"


st.sidebar.title("Navigation")
st.sidebar.markdown("Select a page to view:")

selected_page = st.sidebar.radio(
    "Go to",
    PAGES,
    index=PAGES.index(st.session_state["selected_page"]),
    label_visibility="collapsed"
)

st.session_state["selected_page"] = selected_page

st.sidebar.divider()
st.sidebar.caption("© 2026 Adaptive Cycling Coach")


# ============================================================
# HOME
# ============================================================

if selected_page == "Home":

    home.show_homepage()


# ============================================================
# ADAPTIVE CYCLING COACH
# ============================================================

elif selected_page == "Adaptive Cycling Coach":

    st.title("Adaptive Cycling Coach")

    st.markdown(
        "Compare your current baseline metrics against "
        "recommended targets generated from your recent rides."
    )

    st.divider()

    # --------------------------------------------------------
    # CHECK LOGIN
    # --------------------------------------------------------

    if "jwt" not in st.session_state:

        st.warning(
            "Please connect your Intervals.icu account first "
            "from the Sync page."
        )

        st.stop()


    # --------------------------------------------------------
    # LOAD DATA ONCE
    # --------------------------------------------------------

    try:

        df = load_data(st.session_state["jwt"])

    except requests.exceptions.RequestException as e:

        st.error(f"Unable to connect to backend: {e}")
        st.stop()

    except Exception as e:

        st.error(f"Failed to load dashboard data: {e}")
        st.stop()


    # --------------------------------------------------------
    # NO DATA
    # --------------------------------------------------------

    if df.empty:

        st.info(
            "No ride data is available yet. "
            "Please sync your Intervals.icu activities first."
        )

        st.stop()


    # Remove rows without dates
    if "activity_date" in df.columns:

        df = df.dropna(subset=["activity_date"])

    if df.empty:

        st.info("No valid activity dates are available yet.")
        st.stop()


    # ========================================================
    # LATEST RECOMMENDATION
    # ========================================================

    st.subheader("Latest Ride Recommendation")

    # Sort so newest activity is first
    latest_df = df.sort_values(
        "activity_date",
        ascending=False
    )

    latest = latest_df.iloc[0]


    # --------------------------------------------------------
    # Check required recommendation columns
    # --------------------------------------------------------

    recommendation_columns = [
        "baseline_distance",
        "baseline_elevation",
        "prediction_baseline_hr",
        "recommended_distance",
        "recommended_elevation",
        "recommended_hr"
    ]

    missing_recommendation_columns = [
        col
        for col in recommendation_columns
        if col not in df.columns
    ]


    if missing_recommendation_columns:

        st.warning(
            "Recommendation data is not available yet. "
            f"Missing: {', '.join(missing_recommendation_columns)}"
        )

    else:

        # ----------------------------------------------------
        # Extract values safely
        # ----------------------------------------------------

        baseline_distance = latest["baseline_distance"]
        baseline_elevation = latest["baseline_elevation"]
        baseline_hr = latest["prediction_baseline_hr"]

        recommended_distance = latest["recommended_distance"]
        recommended_elevation = latest["recommended_elevation"]
        recommended_hr = latest["recommended_hr"]


        # ----------------------------------------------------
        # Display recommendation
        # ----------------------------------------------------

        col1, col2 = st.columns(2)


        # ==========================
        # CURRENT BASELINE
        # ==========================

        with col1:

            st.subheader("Current Baseline")

            with st.container(border=True):

                if pd.notna(baseline_distance):

                    st.metric(
                        "Baseline Distance (km)",
                        round(float(baseline_distance) / 1000, 2)
                    )

                else:

                    st.metric(
                        "Baseline Distance (km)",
                        "N/A"
                    )


                if pd.notna(baseline_elevation):

                    st.metric(
                        "Baseline Elevation",
                        round(float(baseline_elevation), 2)
                    )

                else:

                    st.metric(
                        "Baseline Elevation",
                        "N/A"
                    )


                if pd.notna(baseline_hr):

                    st.metric(
                        "Baseline HR",
                        round(float(baseline_hr), 2)
                    )

                else:

                    st.metric(
                        "Baseline HR",
                        "N/A"
                    )


        # ==========================
        # RECOMMENDATION
        # ==========================

        with col2:

            st.subheader("Recommendations")

            with st.container(border=True):

                # Distance
                if (
                    pd.notna(recommended_distance)
                    and pd.notna(baseline_distance)
                ):

                    recommended_distance_km = (
                        float(recommended_distance) / 1000
                    )

                    baseline_distance_km = (
                        float(baseline_distance) / 1000
                    )

                    st.metric(
                        "Recommended Distance (km)",
                        round(recommended_distance_km, 2),
                        delta=round(
                            recommended_distance_km
                            - baseline_distance_km,
                            2
                        )
                    )

                else:

                    st.metric(
                        "Recommended Distance (km)",
                        "N/A"
                    )


                # Elevation
                if (
                    pd.notna(recommended_elevation)
                    and pd.notna(baseline_elevation)
                ):

                    st.metric(
                        "Recommended Elevation",
                        round(float(recommended_elevation), 2),
                        delta=round(
                            float(recommended_elevation)
                            - float(baseline_elevation),
                            2
                        )
                    )

                else:

                    st.metric(
                        "Recommended Elevation",
                        "N/A"
                    )


                # Heart rate
                if (
                    pd.notna(recommended_hr)
                    and pd.notna(baseline_hr)
                ):

                    st.metric(
                        "Recommended HR",
                        round(float(recommended_hr), 2),
                        delta=round(
                            float(recommended_hr)
                            - float(baseline_hr),
                            2
                        ),
                        delta_color="inverse"
                    )

                else:

                    st.metric(
                        "Recommended HR",
                        "N/A"
                    )


    # ========================================================
    # 6-MONTH FATIGUE TREND
    # ========================================================

    st.divider()

    st.subheader("6-Month Fatigue Trend")

    required_columns = [
        "activity_date",
        "fatigue"
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing:

        st.error(
            f"Missing expected columns: {', '.join(missing)}"
        )

    else:

        fatigue_df = df[
            ["activity_date", "fatigue"]
        ].copy()

        fatigue_df = fatigue_df.dropna(
            subset=["activity_date"]
        )

        if fatigue_df.empty:

            st.info("No fatigue data available yet.")

        else:

            latest_date = fatigue_df["activity_date"].max()

            six_months_ago = (
                latest_date - timedelta(days=180)
            )

            recent_df = fatigue_df[
                fatigue_df["activity_date"] >= six_months_ago
            ]

            if recent_df.empty:

                st.info(
                    "No rides found in the last 6 months."
                )

            else:

                fig = px.line(
                    recent_df,
                    x="activity_date",
                    y="fatigue",
                    markers=True,
                    title="Fatigue Levels Over Recent Rides",
                    labels={
                        "activity_date": "Date of Activity",
                        "fatigue": "Calculated Fatigue"
                    }
                )

                fig.update_layout(
                    hovermode="x unified"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )


    # ========================================================
    # CAPACITY DEVIATION
    # ========================================================

    st.divider()

    st.subheader("Capacity Deviation Analysis")

    st.markdown(
        "A visual breakdown of how your capacity "
        "deviates from the baseline over time."
    )


    required_columns = [
        "activity_date",
        "capacity_deviation"
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]


    if missing:

        st.error(
            f"Missing expected columns: {', '.join(missing)}"
        )

    else:

        capacity_df = df[
            ["activity_date", "capacity_deviation"]
        ].copy()

        capacity_df = capacity_df.dropna(
            subset=["activity_date"]
        )


        if capacity_df.empty:

            st.info(
                "No capacity deviation data available yet."
            )

        else:

            latest_date = capacity_df["activity_date"].max()

            six_months_ago = (
                latest_date - timedelta(days=180)
            )

            recent_df = capacity_df[
                capacity_df["activity_date"] >= six_months_ago
            ]


            if recent_df.empty:

                st.info(
                    "No rides found in the last 6 months."
                )

            else:

                fig2 = px.bar(
                    recent_df,
                    x="activity_date",
                    y="capacity_deviation",
                    color="capacity_deviation",
                    color_continuous_scale=px.colors.diverging.RdYlGn,
                    title="Capacity Deviation",
                    labels={
                        "activity_date": "Date",
                        "capacity_deviation": "Deviation Magnitude"
                    }
                )

                fig2.update_layout(
                    template="plotly_dark",
                    xaxis_title="Activity Date",
                    yaxis_title="Deviation",
                    coloraxis_showscale=False,
                    hovermode="x unified"
                )

                st.plotly_chart(
                    fig2,
                    use_container_width=True
                )


    # ========================================================
    # POWER TREND & PREDICTION
    # ========================================================

    st.divider()

    st.subheader("Average Power Trend & Prediction")

    st.markdown(
        "Comparing recorded average power directly "
        "against our predictions, ride by ride."
    )


    required_columns = [
        "activity_date",
        "average_power",
        "estimated_power"
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]


    if missing:

        st.error(
            f"Missing expected columns: {', '.join(missing)}"
        )

    else:

        power_df = df[
            [
                "activity_date",
                "average_power",
                "estimated_power"
            ]
        ].copy()


        power_df = power_df.dropna(
            subset=[
                "activity_date",
                "average_power"
            ]
        )


        power_df = power_df[
            power_df["average_power"] > 0
        ]


        if power_df.empty:

            st.info(
                "No power data available yet."
            )

        else:

            fig4 = go.Figure()


            # Actual power
            fig4.add_trace(
                go.Scatter(
                    x=power_df["activity_date"],
                    y=power_df["average_power"],
                    mode="markers",
                    name="Actual Power (Avg Watts)",
                    marker=dict(
                        color="#87CEEB",
                        size=7,
                        opacity=0.8
                    ),
                    hoverinfo="x+y"
                )
            )


            # Predicted power
            predicted_df = power_df.dropna(
                subset=["estimated_power"]
            )


            if not predicted_df.empty:

                fig4.add_trace(
                    go.Scatter(
                        x=predicted_df["activity_date"],
                        y=predicted_df["estimated_power"],
                        mode="markers",
                        name="Predicted Power (RF Model)",
                        marker=dict(
                            color="#00E676",
                            size=7,
                            symbol="diamond",
                            opacity=0.8
                        ),
                        hoverinfo="x+y"
                    )
                )


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
                    gridcolor="rgba(255,255,255,0.1)"
                ),
                hovermode="x unified",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                margin=dict(
                    l=0,
                    r=0,
                    t=40,
                    b=0
                )
            )


            st.plotly_chart(
                fig4,
                use_container_width=True
            )


# ============================================================
# OTHER PAGES
# ============================================================

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