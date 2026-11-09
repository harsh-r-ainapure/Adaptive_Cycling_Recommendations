import streamlit as st

def apply_custom_css():
    """Injects modern, polished CSS styles into the Streamlit application."""
    custom_css = """
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Overall Background and App Shell */
    .stApp {
        background-color: #0B0F19;
        color: #F3F4F6;
    }

    /* Top decoration bar */
    header[data-testid="stHeader"] {
        background: rgba(11, 15, 25, 0.8) !important;
        backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    section[data-testid="stSidebar"] .stRadio > div {
        gap: 6px;
    }

    section[data-testid="stSidebar"] .stRadio label {
        padding: 8px 12px;
        border-radius: 8px;
        transition: all 0.2s ease-in-out;
        font-weight: 500;
        color: #94A3B8;
    }

    section[data-testid="stSidebar"] .stRadio label:hover {
        background-color: rgba(255, 255, 255, 0.05);
        color: #F8FAFC;
    }

    /* Modern Card Containers */
    .modern-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(16px);
        margin-bottom: 20px;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }

    .modern-card:hover {
        border-color: rgba(252, 76, 2, 0.4);
        box-shadow: 0 14px 30px -4px rgba(252, 76, 2, 0.12), 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }

    .metric-card {
        background: linear-gradient(145deg, #131D31 0%, #0F172A 100%);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        padding: 20px 22px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #FC4C02, #FF7A00);
        opacity: 0.8;
    }

    .metric-card.baseline::before {
        background: linear-gradient(90deg, #38BDF8, #6366F1);
    }

    .metric-card.success::before {
        background: linear-gradient(90deg, #10B981, #059669);
    }

    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #F8FAFC;
        line-height: 1.1;
        letter-spacing: -0.02em;
    }

    .metric-unit {
        font-size: 1rem;
        font-weight: 500;
        color: #64748B;
        margin-left: 4px;
    }

    .metric-delta {
        font-size: 0.875rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 10px;
        border-radius: 9999px;
        margin-top: 10px;
    }

    .metric-delta.positive {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .metric-delta.negative {
        background-color: rgba(239, 68, 68, 0.15);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    .metric-delta.neutral {
        background-color: rgba(148, 163, 184, 0.15);
        color: #CBD5E1;
        border: 1px solid rgba(148, 163, 184, 0.3);
    }

    /* Badges & Pills */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid transparent;
    }

    .status-pill.online {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border-color: rgba(16, 185, 129, 0.3);
    }

    .status-pill.offline {
        background: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
        border-color: rgba(245, 158, 11, 0.3);
    }

    .badge-primary {
        background: linear-gradient(135deg, rgba(252, 76, 2, 0.2), rgba(255, 122, 0, 0.1));
        border: 1px solid rgba(252, 76, 2, 0.4);
        color: #FC4C02;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Streamlit Containers Border Tuning */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        background: rgba(17, 24, 39, 0.4);
        backdrop-filter: blur(8px);
    }

    /* Buttons */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        letter-spacing: 0.01em !important;
        padding: 0.5rem 1.25rem !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        background: #1E293B !important;
        color: #F8FAFC !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    .stButton > button:hover {
        background: #334155 !important;
        border-color: rgba(252, 76, 2, 0.5) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(252, 76, 2, 0.15);
        transform: translateY(-1px);
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #FC4C02 0%, #E03E00 100%) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(252, 76, 2, 0.3) !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #FF5E1E 0%, #E03E00 100%) !important;
        box-shadow: 0 6px 20px rgba(252, 76, 2, 0.4) !important;
        transform: translateY(-2px);
    }

    /* Link Button override */
    a[data-testid="stLinkButton"] {
        border-radius: 10px !important;
        font-weight: 600 !important;
        background: linear-gradient(135deg, #FC4C02 0%, #D83F00 100%) !important;
        border: none !important;
        color: white !important;
        text-align: center;
        box-shadow: 0 4px 14px rgba(252, 76, 2, 0.25) !important;
        transition: all 0.2s ease !important;
    }

    a[data-testid="stLinkButton"]:hover {
        background: linear-gradient(135deg, #FF6224 0%, #FC4C02 100%) !important;
        box-shadow: 0 6px 18px rgba(252, 76, 2, 0.4) !important;
        transform: translateY(-1px);
        color: white !important;
    }

    /* Inputs, Selectboxes & Forms */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 10px !important;
        background-color: #111827 !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
        color: #F8FAFC !important;
    }

    .stTextInput input:focus {
        border-color: #FC4C02 !important;
        box-shadow: 0 0 0 1px #FC4C02 !important;
    }

    /* Callouts / Alerts */
    div[data-testid="stAlert"] {
        border-radius: 12px !important;
        border-width: 1px !important;
        backdrop-filter: blur(8px);
    }

    /* Hero Section */
    .hero-banner {
        background: radial-gradient(circle at top right, rgba(252, 76, 2, 0.15), transparent 50%),
                    radial-gradient(circle at bottom left, rgba(56, 189, 248, 0.1), transparent 50%),
                    #111827;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 36px 32px;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
    }

    .hero-title {
        font-size: 2.25rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FFFFFF 0%, #CBD5E1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
        letter-spacing: -0.02em;
    }

    .hero-subtitle {
        font-size: 1.05rem;
        color: #94A3B8;
        line-height: 1.5;
        max-width: 650px;
        margin-bottom: 0px;
    }

    /* Section Header */
    .section-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #F8FAFC;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: 10px;
        margin-bottom: 4px;
        letter-spacing: -0.01em;
    }

    .section-subtitle {
        font-size: 0.9rem;
        color: #94A3B8;
        margin-bottom: 16px;
    }

    /* Feature card on home */
    .feature-card {
        background: #111827;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 22px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.2s ease;
    }

    .feature-card:hover {
        border-color: rgba(252, 76, 2, 0.4);
        transform: translateY(-2px);
        background: #162032;
    }

    .feature-icon {
        width: 44px;
        height: 44px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        margin-bottom: 14px;
    }

    /* Divider */
    hr {
        border-color: rgba(255, 255, 255, 0.08) !important;
        margin: 24px 0 !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(17, 24, 39, 0.6);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }

    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 8px;
        color: #94A3B8;
        font-weight: 600;
        padding: 0 16px;
        border: none !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }

    /* Code & JSON block */
    pre, code {
        font-family: 'JetBrains Mono', monospace !important;
        background-color: #0d131f !important;
        border-radius: 8px !important;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def render_metric_card(title, value, unit="", delta=None, delta_label="vs Baseline", is_inverse=False, card_type="default", icon=""):
    """
    Renders a modern, visually striking metric card.
    """
    delta_html = ""
    if delta is not None:
        try:
            delta_val = float(delta)
            if delta_val > 0:
                css_class = "negative" if is_inverse else "positive"
                arrow = "▲ +"
            elif delta_val < 0:
                css_class = "positive" if is_inverse else "negative"
                arrow = "▼ "
            else:
                css_class = "neutral"
                arrow = "="
            delta_html = f'<div class="metric-delta {css_class}">{arrow}{delta_val:g} {unit} {delta_label}</div>'
        except (ValueError, TypeError):
            delta_html = f'<div class="metric-delta neutral">{delta}</div>'

    icon_html = f'<span style="font-size: 1rem;">{icon}</span>' if icon else ""
    val_display = str(value) if value is not None and str(value) != "" else "N/A"
    unit_html = f'<span class="metric-unit">{unit}</span>' if unit and val_display != "N/A" else ""

    html = f"""
    <div class="metric-card {card_type}">
        <div class="metric-label">{icon_html} {title}</div>
        <div>
            <span class="metric-value">{val_display}</span>
            {unit_html}
        </div>
        {delta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
