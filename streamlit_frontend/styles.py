import streamlit as st

def apply_custom_css():
    """Injects high-precision, minimalist endurance telemetry styling."""
    custom_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Global Typography & Palette */
    html, body, [class*="css"] {
        font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .stApp {
        background-color: #07090E;
        color: #E2E8F0;
    }

    /* Minimalist Technical Header */
    header[data-testid="stHeader"] {
        background: rgba(7, 9, 14, 0.85) !important;
        backdrop-filter: blur(16px);
        border-bottom: 1px solid #161D2B;
    }

    /* Precision Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0A0D14 !important;
        border-right: 1px solid #161D2B;
    }

    section[data-testid="stSidebar"] .stRadio > div {
        gap: 3px;
    }

    section[data-testid="stSidebar"] .stRadio label {
        padding: 7px 12px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 500;
        letter-spacing: 0.02em;
        color: #7A889B;
        border: 1px solid transparent;
        transition: all 0.15s ease-in-out;
    }

    section[data-testid="stSidebar"] .stRadio label:hover {
        background-color: #101622;
        border-color: #1A2333;
        color: #F1F5F9;
    }

    /* Telemetry HUD Cards */
    .telemetry-card {
        background: #0C1017;
        border: 1px solid #171F2C;
        border-radius: 8px;
        padding: 20px 22px;
        position: relative;
        box-shadow: 0 1px 3px rgba(0,0,0,0.4);
        transition: border-color 0.2s ease, transform 0.2s ease;
    }

    .telemetry-card:hover {
        border-color: #263347;
    }

    .telemetry-meta {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #64748B;
        margin-bottom: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .telemetry-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.1rem;
        font-weight: 600;
        color: #F8FAFC;
        letter-spacing: -0.03em;
        line-height: 1;
    }

    .telemetry-unit {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.85rem;
        color: #718096;
        margin-left: 5px;
        font-weight: 500;
    }

    .telemetry-indicator {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        padding: 3px 8px;
        border-radius: 4px;
        display: inline-block;
        margin-top: 10px;
        font-weight: 500;
    }

    .telemetry-indicator.positive {
        background: rgba(16, 185, 129, 0.1);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.25);
    }

    .telemetry-indicator.negative {
        background: rgba(244, 63, 94, 0.1);
        color: #F43F5E;
        border: 1px solid rgba(244, 63, 94, 0.25);
    }

    .telemetry-indicator.neutral {
        background: rgba(148, 163, 184, 0.08);
        color: #94A3B8;
        border: 1px solid rgba(148, 163, 184, 0.2);
    }

    /* Technical Tag / Monospace Badge */
    .tech-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 3px 8px;
        border-radius: 4px;
        background: #111722;
        border: 1px solid #1E283A;
        color: #94A3B8;
        display: inline-block;
    }

    .tech-tag.active {
        background: rgba(255, 75, 0, 0.1);
        border-color: rgba(255, 75, 0, 0.35);
        color: #FF4B00;
    }

    .tech-tag.live {
        background: rgba(16, 185, 129, 0.1);
        border-color: rgba(16, 185, 129, 0.35);
        color: #10B981;
    }

    /* Streamlit Containers Border Tuning */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #161D2B !important;
        border-radius: 8px !important;
        background: #0B0E15;
    }

    /* Buttons: Minimalist Industrial */
    .stButton > button {
        border-radius: 6px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.02em !important;
        padding: 0.5rem 1rem !important;
        border: 1px solid #1E2738 !important;
        background: #0F141F !important;
        color: #E2E8F0 !important;
        transition: all 0.15s ease !important;
    }

    .stButton > button:hover {
        background: #172030 !important;
        border-color: #2F3E56 !important;
        color: #FFFFFF !important;
    }

    .stButton > button[kind="primary"] {
        background: #FF4B00 !important;
        border: 1px solid #FF5E19 !important;
        color: #FFFFFF !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.4) !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: #E04200 !important;
        border-color: #FF6E2E !important;
    }

    /* Link Button override */
    a[data-testid="stLinkButton"] {
        border-radius: 6px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.02em !important;
        background: #FF4B00 !important;
        border: 1px solid #FF5E19 !important;
        color: white !important;
        text-align: center;
        transition: all 0.15s ease !important;
    }

    a[data-testid="stLinkButton"]:hover {
        background: #E04200 !important;
        color: white !important;
    }

    /* Form Fields */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 6px !important;
        background-color: #0B0F17 !important;
        border-color: #19212E !important;
        color: #F1F5F9 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.9rem !important;
    }

    .stTextInput input:focus {
        border-color: #FF4B00 !important;
        box-shadow: none !important;
    }

    /* Minimalist Technical Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: #0A0D15;
        padding: 4px;
        border-radius: 8px;
        border: 1px solid #161D2B;
    }

    .stTabs [data-baseweb="tab"] {
        height: 38px;
        border-radius: 6px;
        color: #718096;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        letter-spacing: 0.03em;
        font-weight: 500;
        padding: 0 16px;
        border: none !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: #141B26 !important;
        color: #F8FAFC !important;
        border: 1px solid #202A3C !important;
    }

    /* Telemetry Panel Box */
    .telemetry-panel {
        background: #0B0E15;
        border: 1px solid #161D2B;
        border-radius: 8px;
        padding: 22px;
        margin-bottom: 20px;
    }

    /* Clean Code Block */
    pre, code {
        font-family: 'JetBrains Mono', monospace !important;
        background-color: #07090F !important;
        border: 1px solid #141A26 !important;
        border-radius: 6px !important;
        color: #CBD5E1 !important;
    }

    hr {
        border-color: #161D2B !important;
        margin: 24px 0 !important;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def render_telemetry_metric(label, value, unit="", baseline=None, delta=None, delta_label="vs Baseline", is_inverse=False, tag=""):
    """
    Renders an engineering telemetry metric with precision monospace output.
    Zero emojis, clean technical typography.
    """
    indicator_html = ""
    if delta is not None:
        try:
            delta_num = float(delta)
            if delta_num > 0:
                css_class = "negative" if is_inverse else "positive"
                sign = "+"
            elif delta_num < 0:
                css_class = "positive" if is_inverse else "negative"
                sign = ""
            else:
                css_class = "neutral"
                sign = ""
            
            baseline_str = f" [BASE: {baseline}]" if baseline is not None else ""
            indicator_html = f'<div class="telemetry-indicator {css_class}">{sign}{delta_num:g} {unit}{baseline_str}</div>'
        except (ValueError, TypeError):
            indicator_html = f'<div class="telemetry-indicator neutral">{delta}</div>'
    elif baseline is not None:
        indicator_html = f'<div class="telemetry-indicator neutral">BASE: {baseline} {unit}</div>'

    tag_html = f'<span class="tech-tag">{tag}</span>' if tag else ""
    val_str = str(value) if value is not None and str(value) != "" else "N/A"
    unit_str = f'<span class="telemetry-unit">{unit}</span>' if unit and val_str != "N/A" else ""

    html = f"""
    <div class="telemetry-card">
        <div class="telemetry-meta">
            <span>{label}</span>
            {tag_html}
        </div>
        <div>
            <span class="telemetry-value">{val_str}</span>
            {unit_str}
        </div>
        {indicator_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
