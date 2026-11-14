import shutil
from pathlib import Path
import streamlit.file_util as file_util

# Ensure logo assets are available in Streamlit's static root
try:
    _static_dir = Path(file_util.get_static_dir())
    _src_dir = Path(__file__).resolve().parent
    _logo_300 = _src_dir / "stravalogo-300x300.png"
    _logo_fallback = _src_dir / "stravalogo.png"

    if _static_dir.exists():
        # Register stravalogo-300x300.png
        if _logo_300.exists():
            for _name in ["stravalogo-300x300.png", "logo.png", "stravalogo.png"]:
                _dest = _static_dir / _name
                if not _dest.exists() or _dest.stat().st_size != _logo_300.stat().st_size:
                    shutil.copy2(_logo_300, _dest)
        elif _logo_fallback.exists():
            for _name in ["stravalogo-300x300.png", "logo.png", "stravalogo.png"]:
                _dest = _static_dir / _name
                if not _dest.exists() or _dest.stat().st_size != _logo_fallback.stat().st_size:
                    shutil.copy2(_logo_fallback, _dest)
except Exception:
    pass

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
import requests

import styles
import about
import privacy
import contact
import home
import sync
import form


# ============================================================
# PAGE CONFIG & INDUSTRIAL TELEMETRY STYLING
# ============================================================

st.set_page_config(
    page_title="Adaptive Cycling Coach",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply precision styling
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
    "Setup Form",
    "Sync",
    "Adaptive Cycling Coach",
    "About",
    "Privacy Policy",
    "Contact"
]

NAV_LABELS = {
    "Home": "Overview Hub",
    "Sync": "Activity Synchronization",
    "Setup Form": "Sensor Calibration",
    "Adaptive Cycling Coach": "Coach & Telemetry",
    "About": "System Architecture",
    "Privacy Policy": "Privacy Protocol",
    "Contact": "Dispatch & Support"
}

# Check query parameters for authentication token (e.g. ?token=...)
auth_token = st.query_params.get("token")
if isinstance(auth_token, list):
    auth_token = auth_token[0] if auth_token else None
if auth_token:
    st.session_state["jwt"] = auth_token

# Check query parameters for direct page routing (e.g. ?page=privacy or ?p=privacy)
route_param = st.query_params.get("page") or st.query_params.get("p")
if isinstance(route_param, list):
    route_param = route_param[0] if route_param else None

if route_param:
    route_clean = str(route_param).lower().replace("-", "").replace("_", "")
    if route_clean in ["privacy", "privacypolicy"]:
        st.session_state["selected_page"] = "Privacy Policy"

if "selected_page" not in st.session_state:
    st.session_state["selected_page"] = "Home"

with st.sidebar:
    st.markdown("""
        <div style="border-bottom: 1px solid #161D2B; padding-bottom: 16px; margin-bottom: 16px;">
            <div style="display: flex; align-items: baseline; gap: 8px;">
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; color: #FF4B00;">ACC</span>
                <span style="font-size: 0.88rem; font-weight: 600; color: #F8FAFC; letter-spacing: -0.01em;">TELEMETRY</span>
            </div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: #64748B; margin-top: 3px;">
                ENGINE: RF-PHYSIOLOGY v2.4
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Auth Status in Sidebar
    user_jwt = st.session_state.get("jwt")
    sync_active = st.session_state.get("sync_in_progress") or (st.session_state.get("sync_status") == "processing")
    if user_jwt:
        if sync_active:
            st.markdown(
                '<div style="margin-bottom: 16px;"><span class="tech-tag active">GARMIN: INGESTING</span></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="margin-bottom: 16px;"><span class="tech-tag live">GARMIN: AUTHENTICATED</span></div>',
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            '<div style="margin-bottom: 16px;"><span class="tech-tag">GARMIN: UNLINKED</span></div>',
            unsafe_allow_html=True
        )

    st.markdown(
        "<div style=\"font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; letter-spacing: 0.08em; color: #64748B; text-transform: uppercase; margin-bottom: 6px;\">NAV WORKSPACES</div>",
        unsafe_allow_html=True
    )

    selected_page = st.sidebar.radio(
        "Navigation",
        PAGES,
        index=PAGES.index(st.session_state["selected_page"]),
        format_func=lambda x: NAV_LABELS.get(x, x),
        label_visibility="collapsed"
    )

    st.session_state["selected_page"] = selected_page

    st.sidebar.divider()

    st.sidebar.caption("Adaptive Cycling Coach // Precision Endurance Telemetry")


# ============================================================
# HELPER: TECHNICAL PLOTLY THEME
# ============================================================

def apply_telemetry_chart_layout(fig, title="", height=400):
    fig.update_layout(
        title=dict(
            text=f"<span style='font-family: JetBrains Mono; font-size: 12px; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em;'>{title}</span>" if title else "",
            x=0.01,
            y=0.96
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0A0D15",
        font=dict(family="JetBrains Mono, monospace", color="#718096", size=11),
        margin=dict(l=40, r=20, t=44, b=40),
        height=height,
        hoverlabel=dict(
            bgcolor="#111722",
            font_size=11,
            font_family="JetBrains Mono, monospace",
            bordercolor="#202A3C"
        ),
        xaxis=dict(
            showgrid=False,
            gridcolor="#161D2B",
            linecolor="#1A2232",
            tickfont=dict(color="#64748B", size=10)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#131924",
            linecolor="#1A2232",
            tickfont=dict(color="#64748B", size=10),
            zerolinecolor="#202A3C"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10, color="#94A3B8")
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
    header_col, action_col = st.columns([5, 1])
    with header_col:
        st.markdown("""
            <div style="border-left: 2px solid #FF4B00; padding-left: 16px; margin-bottom: 22px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; letter-spacing: 0.12em; color: #FF4B00; text-transform: uppercase;">
                    ANALYTICS ENGINE
                </div>
                <h1 style="font-size: 2rem; font-weight: 700; color: #F8FAFC; margin: 4px 0 6px 0; letter-spacing: -0.02em;">
                    Work Capacity & Recovery Telemetry
                </h1>
                <p style="color: #7A889B; font-size: 0.9rem; margin: 0;">
                    Real-time baseline deviation analysis and upcoming session parameter targets computed from historical rides.
                </p>
            </div>
        """, unsafe_allow_html=True)
    with action_col:
        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
        if st.button("Re-query Cache", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # --------------------------------------------------------
    # CHECK LOGIN
    # --------------------------------------------------------

    if "jwt" not in st.session_state or not st.session_state["jwt"]:
        st.markdown("""
        <div class="telemetry-panel" style="border-left: 3px solid #F59E0B; text-align: left;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #F59E0B; text-transform: uppercase; margin-bottom: 6px;">
                SESSION UNLINKED
            </div>
            <div style="color: #CBD5E1; font-size: 0.9rem; margin-bottom: 14px;">
                No authenticated session detected. Please connect your Garmin Connect account on the Sync workspace to stream athlete activity.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Open Ingestion Workspace", type="primary"):
            st.session_state["selected_page"] = "Sync"
            st.rerun()

        st.stop()

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    try:
        with st.spinner("Streaming workout telemetry from analytics backend..."):
            df = load_data(st.session_state["jwt"])

    except requests.exceptions.RequestException as e:
        st.error(f"Backend connection fault: {e}")
        st.stop()

    except Exception as e:
        st.error(f"Telemetry parsing fault: {e}")
        st.stop()

    # --------------------------------------------------------
    # NO DATA
    # --------------------------------------------------------

    if df.empty:
        st.markdown("""
        <div class="telemetry-panel" style="border-left: 3px solid #38BDF8;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #38BDF8; text-transform: uppercase; margin-bottom: 6px;">
                ZERO RECORDS LOCATED
            </div>
            <div style="color: #CBD5E1; font-size: 0.9rem; margin-bottom: 14px;">
                Authentication confirmed, but no recorded cycling activities were retrieved from the database.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Execute Ingestion Now", type="primary"):
            st.session_state["selected_page"] = "Sync"
            st.rerun()

        st.stop()

    # Remove rows without dates
    if "activity_date" in df.columns:
        df = df.dropna(subset=["activity_date"])

    if df.empty:
        st.info("No activities with valid timestamps located in current slice.")
        st.stop()

    # ========================================================
    # LATEST RECOMMENDATION
    # ========================================================

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

    latest_date_str = latest["activity_date"].strftime("%Y-%m-%d") if pd.notna(latest["activity_date"]) else "LATEST"

    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 12px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; letter-spacing: 0.08em; color: #64748B; text-transform: uppercase;">
                PRESCRIPTION TARGETS // NEXT RIDE
            </div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #64748B;">
                ANCHOR ACTIVITY: <span style="color: #F8FAFC;">{latest_date_str}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if missing_recommendation_columns:
        st.warning(f"Recommendation vector incomplete. Missing: {', '.join(missing_recommendation_columns)}")
    else:
        baseline_distance = latest["baseline_distance"]
        baseline_elevation = latest["baseline_elevation"]
        baseline_hr = latest["prediction_baseline_hr"]

        recommended_distance = latest["recommended_distance"]
        recommended_elevation = latest["recommended_elevation"]
        recommended_hr = latest["recommended_hr"]

        rec_dist_km = round(float(recommended_distance) / 1000, 2) if pd.notna(recommended_distance) else None
        base_dist_km = round(float(baseline_distance) / 1000, 2) if pd.notna(baseline_distance) else None
        delta_dist = round(rec_dist_km - base_dist_km, 2) if (rec_dist_km is not None and base_dist_km is not None) else None

        rec_elev = round(float(recommended_elevation), 1) if pd.notna(recommended_elevation) else None
        base_elev = round(float(baseline_elevation), 1) if pd.notna(baseline_elevation) else None
        delta_elev = round(rec_elev - base_elev, 1) if (rec_elev is not None and base_elev is not None) else None

        rec_hr = round(float(recommended_hr), 1) if pd.notna(recommended_hr) else None
        base_hr = round(float(baseline_hr), 1) if pd.notna(baseline_hr) else None
        delta_hr = round(rec_hr - base_hr, 1) if (rec_hr is not None and base_hr is not None) else None

        # Render 3 Engineering HUD Metric Cards
        hud_col1, hud_col2, hud_col3 = st.columns(3)

        with hud_col1:
            styles.render_telemetry_metric(
                label="VOLUME TARGET",
                value=rec_dist_km,
                unit="km",
                baseline=base_dist_km,
                delta=delta_dist,
                delta_label="km vs base",
                tag="RECOMMENDED DISTANCE"
            )

        with hud_col2:
            styles.render_telemetry_metric(
                label="VERTICAL TARGET",
                value=rec_elev,
                unit="m",
                baseline=base_elev,
                delta=delta_elev,
                delta_label="m vs base",
                tag="RECOMMENDED ASCENT"
            )

        with hud_col3:
            styles.render_telemetry_metric(
                label="HEART RATE CEILING",
                value=rec_hr,
                unit="bpm",
                baseline=base_hr,
                delta=delta_hr,
                delta_label="bpm vs base",
                is_inverse=True,
                tag="TARGET INTENSITY"
            )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.divider()

    # ========================================================
    # TELEMETRY CHARTS IN MONOCHROME TABS
    # ========================================================

    tab_fatigue, tab_capacity, tab_power = st.tabs([
        "FATIGUE DECAY // 180-DAY",
        "CAPACITY DEVIATION MATRIX",
        "POWER OUTPUT // ACTUAL VS RF ESTIMATE"
    ])

    # --------------------------------------------------------
    # TAB 1: 6-MONTH FATIGUE TREND
    # --------------------------------------------------------
    with tab_fatigue:
        st.markdown("""
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #64748B; margin-bottom: 12px;">
            METRIC: EXPONENTIAL DECAY // HALF-LIFE FATIGUE INTEGRAL OVER 180 DAYS
        </div>
        """, unsafe_allow_html=True)

        fatigue_cols = ["activity_date", "fatigue"]
        missing_fatigue = [col for col in fatigue_cols if col not in df.columns]

        if missing_fatigue:
            st.error(f"Missing telemetry columns: {', '.join(missing_fatigue)}")
        else:
            fatigue_df = df[["activity_date", "fatigue"]].copy().dropna(subset=["activity_date"])

            if fatigue_df.empty:
                st.info("Zero fatigue records found.")
            else:
                latest_date = fatigue_df["activity_date"].max()
                six_months_ago = latest_date - timedelta(days=180)
                recent_fatigue_df = fatigue_df[fatigue_df["activity_date"] >= six_months_ago].sort_values("activity_date")

                if recent_fatigue_df.empty:
                    st.info("No recorded workouts in the previous 180-day window.")
                else:
                    fig_fatigue = go.Figure()

                    fig_fatigue.add_trace(
                        go.Scatter(
                            x=recent_fatigue_df["activity_date"],
                            y=recent_fatigue_df["fatigue"],
                            mode="lines+markers",
                            name="Fatigue Index",
                            line=dict(color="#FF4B00", width=2),
                            marker=dict(size=5, color="#FF4B00"),
                            fill="tozeroy",
                            fillcolor="rgba(255, 75, 0, 0.08)",
                            hovertemplate="DATE: %{x|%Y-%m-%d}<br>FATIGUE: %{y:.2f}<extra></extra>"
                        )
                    )

                    fig_fatigue = apply_telemetry_chart_layout(
                        fig_fatigue,
                        title="PHYSIOLOGICAL FATIGUE INDEX (EXPONENTIAL DECAY)",
                        height=410
                    )
                    fig_fatigue.update_layout(
                        hovermode="x unified",
                        yaxis_title="Fatigue Units"
                    )

                    st.plotly_chart(fig_fatigue, use_container_width=True)

    # --------------------------------------------------------
    # TAB 2: CAPACITY DEVIATION
    # --------------------------------------------------------
    with tab_capacity:
        st.markdown("""
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #64748B; margin-bottom: 12px;">
            METRIC: RESIDUAL CAPACITY DEVIATION (+SURPLUS FORM / -FATIGUE ACCUMULATION)
        </div>
        """, unsafe_allow_html=True)

        cap_cols = ["activity_date", "capacity_deviation"]
        missing_cap = [col for col in cap_cols if col not in df.columns]

        if missing_cap:
            st.error(f"Missing telemetry columns: {', '.join(missing_cap)}")
        else:
            capacity_df = df[["activity_date", "capacity_deviation"]].copy().dropna(subset=["activity_date"])

            if capacity_df.empty:
                st.info("Zero capacity deviation data available.")
            else:
                latest_date = capacity_df["activity_date"].max()
                six_months_ago = latest_date - timedelta(days=180)
                recent_cap_df = capacity_df[capacity_df["activity_date"] >= six_months_ago].sort_values("activity_date")

                if recent_cap_df.empty:
                    st.info("No recorded workouts in the previous 180-day window.")
                else:
                    fig2 = px.bar(
                        recent_cap_df,
                        x="activity_date",
                        y="capacity_deviation",
                        color="capacity_deviation",
                        color_continuous_scale=[
                            [0.0, "#F43F5E"],
                            [0.5, "#E2E8F0"],
                            [1.0, "#10B981"]
                        ]
                    )

                    fig2 = apply_telemetry_chart_layout(
                        fig2,
                        title="ATHLETE CAPACITY DEVIATION FROM ROLLING BASELINE",
                        height=410
                    )
                    fig2.update_layout(
                        coloraxis_showscale=False,
                        hovermode="x unified",
                        yaxis_title="Deviation Magnitude"
                    )

                    st.plotly_chart(fig2, use_container_width=True)

    # --------------------------------------------------------
    # TAB 3: POWER TREND & PREDICTION
    # --------------------------------------------------------
    with tab_power:
        st.markdown("""
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #64748B; margin-bottom: 12px;">
            MODEL: SUPERVISED RANDOM FOREST REGRESSOR // ACTUAL SENSOR WATTS VS ESTIMATED WATTS
        </div>
        """, unsafe_allow_html=True)

        power_cols = ["activity_date", "average_power", "estimated_power"]
        missing_power = [col for col in power_cols if col not in df.columns]

        if missing_power:
            st.error(f"Missing telemetry columns: {', '.join(missing_power)}")
        else:
            power_df = df[["activity_date", "average_power", "estimated_power"]].copy()
            power_df = power_df.dropna(subset=["activity_date", "average_power"])
            power_df = power_df[power_df["average_power"] > 0].sort_values("activity_date")

            if power_df.empty:
                st.info("No recorded power data located.")
            else:
                fig4 = go.Figure()

                fig4.add_trace(
                    go.Scatter(
                        x=power_df["activity_date"],
                        y=power_df["average_power"],
                        mode="markers",
                        name="Actual Power (Sensor)",
                        marker=dict(
                            color="#38BDF8",
                            size=6,
                            opacity=0.9
                        ),
                        hovertemplate="DATE: %{x|%Y-%m-%d}<br>ACTUAL: %{y:.1f} W<extra></extra>"
                    )
                )

                predicted_df = power_df.dropna(subset=["estimated_power"])

                if not predicted_df.empty:
                    fig4.add_trace(
                        go.Scatter(
                            x=predicted_df["activity_date"],
                            y=predicted_df["estimated_power"],
                            mode="markers",
                            name="Predicted Power (RF Model)",
                            marker=dict(
                                color="#00D084",
                                size=6,
                                symbol="diamond",
                                opacity=0.9
                            ),
                            hovertemplate="DATE: %{x|%Y-%m-%d}<br>PREDICTED: %{y:.1f} W<extra></extra>"
                        )
                    )

                fig4 = apply_telemetry_chart_layout(
                    fig4,
                    title="SENSOR OUTPUT VS RANDOM FOREST REGRESSOR",
                    height=410
                )
                fig4.update_layout(
                    hovermode="x unified",
                    yaxis=dict(
                        title="Power (Watts)",
                        showgrid=True,
                        gridcolor="#131924"
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
