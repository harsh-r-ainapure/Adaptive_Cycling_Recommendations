import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
import requests
from pathlib import Path

import styles
import about
import privacy
import contact
import home
import sync
import form


# ============================================================
# PAGE CONFIG & MODERN CSS
# ============================================================

st.set_page_config(
    page_title="Adaptive Cycling Coach",
    page_icon="🚴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom UI styling
styles.apply_custom_css()


# ============================================================
# BACKEND CONFIG
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

PAGE_ICONS = {
    "Home": "🏠",
    "Sync": "🔄",
    "Setup Form": "⚙️",
    "Adaptive Cycling Coach": "🚴",
    "About": "ℹ️",
    "Privacy Policy": "🔒",
    "Contact": "✉️"
}

if "selected_page" not in st.session_state:
    st.session_state["selected_page"] = "Home"

# Sidebar Brand Header
with st.sidebar:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; padding: 12px 0 18px 0;">
            <div style="background: linear-gradient(135deg, #FC4C02 0%, #FF7A00 100%); width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; box-shadow: 0 4px 12px rgba(252,76,2,0.35);">
                ⚡
            </div>
            <div>
                <div style="font-weight: 800; font-size: 1.15rem; color: #F8FAFC; letter-spacing: -0.02em;">Adaptive Coach</div>
                <div style="font-size: 0.75rem; color: #94A3B8;">ML Cycling Intelligence</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Auth Status Pill in Sidebar
    user_jwt = st.session_state.get("jwt")
    if user_jwt:
        st.markdown(
            '<div style="margin-bottom: 18px;"><span class="status-pill online">● Intervals Connected</span></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div style="margin-bottom: 18px;"><span class="status-pill offline">○ Not Connected</span></div>',
            unsafe_allow_html=True
        )

    st.markdown("<p style='font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #64748B; margin-bottom: 6px;'>Navigation</p>", unsafe_allow_html=True)

    selected_page = st.sidebar.radio(
        "Go to",
        PAGES,
        index=PAGES.index(st.session_state["selected_page"]),
        format_func=lambda x: f"{PAGE_ICONS.get(x, '•')}  {x}",
        label_visibility="collapsed"
    )

    st.session_state["selected_page"] = selected_page

    st.sidebar.divider()

    # Quick Navigation / Help Widget in Sidebar
    st.markdown("""
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px; margin-bottom: 16px;">
            <div style="font-size: 0.8rem; font-weight: 600; color: #CBD5E1;">Quick Status</div>
            <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 4px;">Intervals.icu OAuth + Random Forest Power Model</div>
        </div>
    """, unsafe_allow_html=True)

    st.sidebar.caption("© 2026 Adaptive Cycling Coach • v2.0")


# ============================================================
# HELPER: MODERN PLOTLY THEME
# ============================================================

def apply_modern_chart_layout(fig, title="", height=400):
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(size=15, color="#F8FAFC", family="Plus Jakarta Sans, sans-serif"),
            x=0.01,
            y=0.96
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17, 24, 39, 0.45)",
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#94A3B8"),
        margin=dict(l=40, r=20, t=50, b=40),
        height=height,
        hoverlabel=dict(
            bgcolor="#1E293B",
            font_size=12,
            font_family="Plus Jakarta Sans, sans-serif",
            bordercolor="rgba(255,255,255,0.15)"
        ),
        xaxis=dict(
            showgrid=False,
            gridcolor="rgba(255,255,255,0.06)",
            linecolor="rgba(255,255,255,0.1)",
            tickfont=dict(color="#94A3B8", size=11)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.06)",
            linecolor="rgba(255,255,255,0.1)",
            tickfont=dict(color="#94A3B8", size=11),
            zerolinecolor="rgba(255,255,255,0.15)"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#CBD5E1")
        )
    )
    return fig


# ============================================================
# HOME
# ============================================================

if selected_page == "Home":
    home.show_homepage()


# ============================================================
# ADAPTIVE CYCLING COACH DASHBOARD
# ============================================================

elif selected_page == "Adaptive Cycling Coach":

    # Page Header Banner
    header_col, action_col = st.columns([4, 1])
    with header_col:
        st.markdown("""
            <div style="margin-bottom: 20px;">
                <span class="badge-primary">AI Performance Lab</span>
                <h1 style="margin: 8px 0 0 0; font-size: 2.2rem; font-weight: 800; color: #F8FAFC;">
                    🚴 Adaptive Cycling Coach
                </h1>
                <p style="color: #94A3B8; font-size: 1rem; margin-top: 6px;">
                    Compare your current baseline metrics against AI-recommended targets generated from your historical rides.
                </p>
            </div>
        """, unsafe_allow_html=True)
    with action_col:
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # --------------------------------------------------------
    # CHECK LOGIN
    # --------------------------------------------------------

    if "jwt" not in st.session_state or not st.session_state["jwt"]:
        st.markdown("""
        <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 16px; padding: 28px; text-align: center; margin: 20px 0;">
            <div style="font-size: 2.5rem; margin-bottom: 10px;">🔒</div>
            <h3 style="color: #FBBF24; margin-bottom: 8px; font-weight: 700;">Intervals.icu Connection Required</h3>
            <p style="color: #94A3B8; max-width: 500px; margin: 0 auto 20px auto; font-size: 0.95rem;">
                Please connect your Intervals.icu account to securely retrieve your activity streams and personal recommendations.
            </p>
        </div>
        """, unsafe_allow_html=True)

        btn_c1, btn_c2, btn_c3 = st.columns([1, 2, 1])
        with btn_c2:
            if st.button("Go to Sync & Authorize ➔", type="primary", use_container_width=True):
                st.session_state["selected_page"] = "Sync"
                st.rerun()

        st.stop()

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    try:
        with st.spinner("Loading athlete performance data..."):
            df = load_data(st.session_state["jwt"])

    except requests.exceptions.RequestException as e:
        st.error(f"Unable to connect to backend server: {e}")
        st.stop()

    except Exception as e:
        st.error(f"Failed to load dashboard data: {e}")
        st.stop()

    # --------------------------------------------------------
    # NO DATA
    # --------------------------------------------------------

    if df.empty:
        st.markdown("""
        <div style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 16px; padding: 28px; text-align: center; margin: 20px 0;">
            <div style="font-size: 2.5rem; margin-bottom: 10px;">📂</div>
            <h3 style="color: #38BDF8; margin-bottom: 8px; font-weight: 700;">No Ride Activities Found</h3>
            <p style="color: #94A3B8; max-width: 500px; margin: 0 auto 20px auto; font-size: 0.95rem;">
                Your account is linked, but no cycling activities have been synchronized into the analytics database yet.
            </p>
        </div>
        """, unsafe_allow_html=True)

        b1, b2, b3 = st.columns([1, 2, 1])
        with b2:
            if st.button("Sync Activities Now ➔", type="primary", use_container_width=True):
                st.session_state["selected_page"] = "Sync"
                st.rerun()

        st.stop()

    # Remove rows without dates
    if "activity_date" in df.columns:
        df = df.dropna(subset=["activity_date"])

    if df.empty:
        st.info("No valid activity dates are available in the recorded sessions.")
        st.stop()

    # ========================================================
    # LATEST RECOMMENDATION
    # ========================================================

    # Sort so newest activity is first
    latest_df = df.sort_values("activity_date", ascending=False)
    latest = latest_df.iloc[0]

    recommendation_columns = [
        "baseline_distance",
        "baseline_elevation",
        "prediction_baseline_hr",
        "recommended_distance",
        "recommended_elevation",
        "recommended_hr"
    ]

    missing_recommendation_columns = [
        col for col in recommendation_columns if col not in df.columns
    ]

    latest_date_str = latest["activity_date"].strftime("%B %d, %Y") if pd.notna(latest["activity_date"]) else "Recent"

    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; margin-bottom: 16px;">
            <div class="section-title">
                <span>🎯 Next Ride Recommendations</span>
            </div>
            <div style="font-size: 0.85rem; color: #94A3B8; background: #111827; padding: 6px 14px; border-radius: 9999px; border: 1px solid rgba(255,255,255,0.08);">
                Based on ride: <strong style="color: #F8FAFC;">{latest_date_str}</strong>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if missing_recommendation_columns:
        st.warning(
            "Recommendation data is not available yet. "
            f"Missing fields: {', '.join(missing_recommendation_columns)}"
        )
    else:
        # Extract values safely
        baseline_distance = latest["baseline_distance"]
        baseline_elevation = latest["baseline_elevation"]
        baseline_hr = latest["prediction_baseline_hr"]

        recommended_distance = latest["recommended_distance"]
        recommended_elevation = latest["recommended_elevation"]
        recommended_hr = latest["recommended_hr"]

        # Calculate values and deltas
        rec_dist_km = round(float(recommended_distance) / 1000, 2) if pd.notna(recommended_distance) else None
        base_dist_km = round(float(baseline_distance) / 1000, 2) if pd.notna(baseline_distance) else None
        delta_dist = round(rec_dist_km - base_dist_km, 2) if (rec_dist_km is not None and base_dist_km is not None) else None

        rec_elev = round(float(recommended_elevation), 1) if pd.notna(recommended_elevation) else None
        base_elev = round(float(baseline_elevation), 1) if pd.notna(baseline_elevation) else None
        delta_elev = round(rec_elev - base_elev, 1) if (rec_elev is not None and base_elev is not None) else None

        rec_hr = round(float(recommended_hr), 1) if pd.notna(recommended_hr) else None
        base_hr = round(float(baseline_hr), 1) if pd.notna(baseline_hr) else None
        delta_hr = round(rec_hr - base_hr, 1) if (rec_hr is not None and base_hr is not None) else None

        # Display Top KPI Cards
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

        with kpi_col1:
            val_txt = f"{rec_dist_km}" if rec_dist_km is not None else "N/A"
            base_txt = f"{base_dist_km} km" if base_dist_km is not None else "N/A"
            styles.render_metric_card(
                title="Target Distance",
                value=val_txt,
                unit="km",
                delta=delta_dist,
                delta_label=f"(Baseline: {base_txt})",
                icon="🛣️",
                card_type="default"
            )

        with kpi_col2:
            val_txt = f"{rec_elev}" if rec_elev is not None else "N/A"
            base_txt = f"{base_elev} m" if base_elev is not None else "N/A"
            styles.render_metric_card(
                title="Target Elevation",
                value=val_txt,
                unit="m",
                delta=delta_elev,
                delta_label=f"(Baseline: {base_txt})",
                icon="⛰️",
                card_type="default"
            )

        with kpi_col3:
            val_txt = f"{rec_hr}" if rec_hr is not None else "N/A"
            base_txt = f"{base_hr} bpm" if base_hr is not None else "N/A"
            styles.render_metric_card(
                title="Target Heart Rate",
                value=val_txt,
                unit="bpm",
                delta=delta_hr,
                delta_label=f"(Baseline: {base_txt})",
                is_inverse=True,
                icon="❤️",
                card_type="default"
            )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    st.divider()

    # ========================================================
    # CHARTS & ANALYTICS IN MODERN TABS
    # ========================================================

    tab_fatigue, tab_capacity, tab_power = st.tabs([
        "📈 6-Month Fatigue Trend",
        "📊 Capacity Deviation Analysis",
        "⚡ Power Output & RF Predictions"
    ])

    # --------------------------------------------------------
    # TAB 1: 6-MONTH FATIGUE TREND
    # --------------------------------------------------------
    with tab_fatigue:
        st.markdown("""
            <div style="margin-bottom: 12px;">
                <h3 style="margin: 0; font-size: 1.2rem; font-weight: 700; color: #F8FAFC;">Fatigue Curve Tracking</h3>
                <p style="color: #94A3B8; font-size: 0.88rem; margin-top: 4px;">
                    Tracks cumulative physiological fatigue calculated across recent rides with exponential decay modeling.
                </p>
            </div>
        """, unsafe_allow_html=True)

        fatigue_cols = ["activity_date", "fatigue"]
        missing_fatigue = [col for col in fatigue_cols if col not in df.columns]

        if missing_fatigue:
            st.error(f"Missing expected columns: {', '.join(missing_fatigue)}")
        else:
            fatigue_df = df[["activity_date", "fatigue"]].copy().dropna(subset=["activity_date"])

            if fatigue_df.empty:
                st.info("No fatigue data available yet.")
            else:
                latest_date = fatigue_df["activity_date"].max()
                six_months_ago = latest_date - timedelta(days=180)
                recent_fatigue_df = fatigue_df[fatigue_df["activity_date"] >= six_months_ago].sort_values("activity_date")

                if recent_fatigue_df.empty:
                    st.info("No rides found in the last 6 months.")
                else:
                    fig_fatigue = go.Figure()

                    # Gradient area + spline line
                    fig_fatigue.add_trace(
                        go.Scatter(
                            x=recent_fatigue_df["activity_date"],
                            y=recent_fatigue_df["fatigue"],
                            mode="lines+markers",
                            name="Calculated Fatigue",
                            line=dict(color="#FC4C02", width=3, shape="spline"),
                            marker=dict(size=6, color="#FC4C02", line=dict(width=2, color="#FFFFFF")),
                            fill="tozeroy",
                            fillcolor="rgba(252, 76, 2, 0.12)",
                            hovertemplate="<b>Date:</b> %{x|%b %d, %Y}<br><b>Fatigue:</b> %{y:.2f}<extra></extra>"
                        )
                    )

                    fig_fatigue = apply_modern_chart_layout(
                        fig_fatigue,
                        title="Fatigue Over Recent Activities (Last 180 Days)",
                        height=420
                    )
                    fig_fatigue.update_layout(
                        hovermode="x unified",
                        yaxis_title="Fatigue Index"
                    )

                    st.plotly_chart(fig_fatigue, use_container_width=True)

    # --------------------------------------------------------
    # TAB 2: CAPACITY DEVIATION
    # --------------------------------------------------------
    with tab_capacity:
        st.markdown("""
            <div style="margin-bottom: 12px;">
                <h3 style="margin: 0; font-size: 1.2rem; font-weight: 700; color: #F8FAFC;">Capacity Deviation Dynamics</h3>
                <p style="color: #94A3B8; font-size: 0.88rem; margin-top: 4px;">
                    Visualizes how your work capacity deviates from your historical baseline. Positive indicates strong form; negative indicates fatigue load.
                </p>
            </div>
        """, unsafe_allow_html=True)

        cap_cols = ["activity_date", "capacity_deviation"]
        missing_cap = [col for col in cap_cols if col not in df.columns]

        if missing_cap:
            st.error(f"Missing expected columns: {', '.join(missing_cap)}")
        else:
            capacity_df = df[["activity_date", "capacity_deviation"]].copy().dropna(subset=["activity_date"])

            if capacity_df.empty:
                st.info("No capacity deviation data available yet.")
            else:
                latest_date = capacity_df["activity_date"].max()
                six_months_ago = latest_date - timedelta(days=180)
                recent_cap_df = capacity_df[capacity_df["activity_date"] >= six_months_ago].sort_values("activity_date")

                if recent_cap_df.empty:
                    st.info("No rides found in the last 6 months.")
                else:
                    fig2 = px.bar(
                        recent_cap_df,
                        x="activity_date",
                        y="capacity_deviation",
                        color="capacity_deviation",
                        color_continuous_scale=[
                            [0.0, "#EF4444"],
                            [0.5, "#F59E0B"],
                            [1.0, "#10B981"]
                        ],
                        labels={
                            "activity_date": "Date",
                            "capacity_deviation": "Deviation Magnitude"
                        }
                    )

                    fig2 = apply_modern_chart_layout(
                        fig2,
                        title="Athlete Capacity Deviation Over Time",
                        height=420
                    )
                    fig2.update_layout(
                        coloraxis_showscale=False,
                        hovermode="x unified",
                        yaxis_title="Capacity Deviation"
                    )

                    st.plotly_chart(fig2, use_container_width=True)

    # --------------------------------------------------------
    # TAB 3: POWER TREND & PREDICTION
    # --------------------------------------------------------
    with tab_power:
        st.markdown("""
            <div style="margin-bottom: 12px;">
                <h3 style="margin: 0; font-size: 1.2rem; font-weight: 700; color: #F8FAFC;">Average Power vs Machine Learning Prediction</h3>
                <p style="color: #94A3B8; font-size: 0.88rem; margin-top: 4px;">
                    Compares recorded average power directly against our Random Forest model predictions, ride by ride.
                </p>
            </div>
        """, unsafe_allow_html=True)

        power_cols = ["activity_date", "average_power", "estimated_power"]
        missing_power = [col for col in power_cols if col not in df.columns]

        if missing_power:
            st.error(f"Missing expected columns: {', '.join(missing_power)}")
        else:
            power_df = df[["activity_date", "average_power", "estimated_power"]].copy()
            power_df = power_df.dropna(subset=["activity_date", "average_power"])
            power_df = power_df[power_df["average_power"] > 0].sort_values("activity_date")

            if power_df.empty:
                st.info("No recorded power data available yet.")
            else:
                fig4 = go.Figure()

                # Actual power trace
                fig4.add_trace(
                    go.Scatter(
                        x=power_df["activity_date"],
                        y=power_df["average_power"],
                        mode="markers",
                        name="Actual Power (Avg Watts)",
                        marker=dict(
                            color="#38BDF8",
                            size=8,
                            opacity=0.85,
                            line=dict(width=1, color="rgba(255,255,255,0.4)")
                        ),
                        hovertemplate="<b>Date:</b> %{x|%b %d, %Y}<br><b>Actual:</b> %{y:.1f} W<extra></extra>"
                    )
                )

                # Predicted power trace
                predicted_df = power_df.dropna(subset=["estimated_power"])

                if not predicted_df.empty:
                    fig4.add_trace(
                        go.Scatter(
                            x=predicted_df["activity_date"],
                            y=predicted_df["estimated_power"],
                            mode="markers",
                            name="Predicted Power (RF Model)",
                            marker=dict(
                                color="#10B981",
                                size=8,
                                symbol="diamond",
                                opacity=0.85,
                                line=dict(width=1, color="rgba(255,255,255,0.4)")
                            ),
                            hovertemplate="<b>Date:</b> %{x|%b %d, %Y}<br><b>Predicted:</b> %{y:.1f} W<extra></extra>"
                        )
                    )

                fig4 = apply_modern_chart_layout(
                    fig4,
                    title="Actual Power vs Random Forest Model Estimates",
                    height=420
                )
                fig4.update_layout(
                    hovermode="x unified",
                    yaxis=dict(
                        title="Power (Watts)",
                        showgrid=True,
                        gridcolor="rgba(255,255,255,0.06)"
                    )
                )

                st.plotly_chart(fig4, use_container_width=True)


# ============================================================
# OTHER PAGES ROUTING
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
