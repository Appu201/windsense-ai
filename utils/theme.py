# utils/theme.py — WindSense AI Dark Theme (Refined)
import streamlit as st

DARK_CSS = """
<style>

/* ── Google Font Import ── */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Rajdhani:wght@400;600;700&display=swap');

/* ── CSS Variables ── */
:root {
    --bg-primary:    #0D1B2A;
    --bg-secondary:  #112233;
    --bg-deep:       #091520;
    --accent-teal:   #00C9B1;
    --accent-blue:   #4FC3F7;
    --accent-soft:   #89CFFE;
    --border-dim:    #1E3A5F;
    --border-bright: #00C9B1;
    --text-primary:  #E0E0E0;
    --text-secondary:#D0D8E0;
    --text-muted:    #8899AA;
    --text-faint:    #5E7A8A;
    --red:           #FF4444;
    --orange:        #FFB347;
    --yellow:        #FFD700;
}

/* ── Base ── */
.stApp,
.main,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"] {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    font-family: 'Rajdhani', sans-serif !important;
}

.main .block-container {
    background-color: var(--bg-primary) !important;
    padding: 1.5rem 2rem;
    max-width: 1400px;
}

/* ── Subtle grid texture on background ── */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(0, 201, 177, 0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 201, 177, 0.025) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a1520 0%, #0d1e30 60%, #091825 100%) !important;
    border-right: 1px solid var(--accent-teal) !important;
    box-shadow: 4px 0 20px rgba(0, 201, 177, 0.08);
}

[data-testid="stSidebar"] * {
    color: var(--text-secondary) !important;
    font-family: 'Rajdhani', sans-serif !important;
}

[data-testid="stSidebarNav"] {
    display: none;
}

/* Sidebar accent line at top */
[data-testid="stSidebar"]::before {
    content: '';
    display: block;
    height: 3px;
    background: linear-gradient(90deg, var(--accent-teal), var(--accent-blue), transparent);
    margin-bottom: 0.5rem;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background-color: var(--bg-deep) !important;
    border-bottom: 2px solid var(--accent-teal) !important;
    gap: 0.15rem;
    padding: 0 0.5rem;
}

.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    color: var(--text-muted) !important;
    border: none !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.82rem;
    letter-spacing: 0.03em;
    padding: 0.6rem 0.85rem;
    border-radius: 4px 4px 0 0;
    transition: color 0.2s, background-color 0.2s;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--accent-teal) !important;
    background-color: rgba(0, 201, 177, 0.06) !important;
}

.stTabs [aria-selected="true"] {
    background-color: var(--accent-teal) !important;
    color: var(--bg-primary) !important;
    border-bottom: 3px solid var(--accent-teal) !important;
    font-weight: 700 !important;
}

.stTabs [data-baseweb="tab-panel"] {
    background-color: var(--bg-primary) !important;
    padding: 1rem 0;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: linear-gradient(145deg, #0D1B2A 0%, #142333 60%, #1A2D3F 100%);
    border: 1px solid #1E3A4A;
    border-radius: 14px;
    padding: 1rem 1.2rem;
    box-shadow:
        0 2px 4px rgba(0,0,0,0.4),
        0 8px 24px rgba(0,0,0,0.3),
        inset 0 1px 0 rgba(0,201,177,0.08);
    transition: all 0.25s ease;
    position: relative;
    overflow: hidden;
}

[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #00C9B1, transparent);
    opacity: 0.6;
}

[data-testid="stMetric"]:hover {
    border-color: #00C9B1;
    box-shadow:
        0 4px 8px rgba(0,0,0,0.5),
        0 12px 32px rgba(0,201,177,0.15),
        inset 0 1px 0 rgba(0,201,177,0.15);
    transform: translateY(-2px);
}

[data-testid="stMetricValue"] {
    color: var(--accent-teal) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.5rem !important;
    font-weight: 600 !important;
}

[data-testid="stMetricLabel"] {
    color: var(--text-muted) !important;
    font-size: 0.82rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

[data-testid="stMetricDelta"] {
    font-size: 0.75rem !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* ── DataFrames ── */
[data-testid="stDataFrame"] > div {
    background-color: var(--bg-secondary) !important;
    border: 1px solid var(--accent-teal) !important;
    border-radius: 6px !important;
    overflow: hidden;
}

.dvn-scroller {
    background-color: var(--bg-secondary) !important;
}

.glideDataEditor {
    background-color: var(--bg-secondary) !important;
    color: var(--text-secondary) !important;
}

.dvn-scroller * {
    color: var(--text-secondary) !important;
}

[data-testid="stDataFrame"] * {
    color: var(--text-secondary) !important;
    background-color: var(--bg-secondary) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #007A6E 0%, #005580 100%) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--accent-teal) !important;
    border-radius: 6px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.04em !important;
    padding: 0.4rem 1rem !important;
    transition: all 0.2s !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent-teal) 0%, #0077B6 100%) !important;
    color: var(--bg-primary) !important;
}

.stButton > button:hover {
    opacity: 0.88 !important;
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 10px rgba(0, 201, 177, 0.25) !important;
    transform: translateY(-1px) !important;
}

.stButton > button:active {
    transform: translateY(0px) !important;
}

/* ── Text inputs / selects ── */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-dim) !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.88rem !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus,
.stNumberInput input:focus {
    border-color: var(--accent-teal) !important;
    box-shadow: 0 0 0 1px var(--accent-teal) !important;
    outline: none !important;
}

.stTextInput label,
.stTextArea label,
.stNumberInput label,
.stSelectbox label,
.stMultiSelect label,
.stSlider label,
.stDateInput label {
    color: var(--text-muted) !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.stSelectbox > div > div,
.stMultiSelect > div > div {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-dim) !important;
    border-radius: 6px !important;
    padding: 2px 8px !important;
    min-height: 38px !important;
    box-shadow: none !important;
}

.stSelectbox > div > div > div,
.stMultiSelect > div > div > div {
    color: var(--text-primary) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.92rem !important;
}

.stSelectbox label,
.stMultiSelect label {
    color: var(--text-muted) !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    margin-bottom: 4px !important;
}

/* Dropdown options */
[data-baseweb="popover"] *,
[data-baseweb="menu"] * {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
}

[data-baseweb="option"]:hover {
    background-color: rgba(0, 201, 177, 0.12) !important;
    color: var(--accent-teal) !important;
}

/* ── Sliders ── */
[data-testid="stSlider"] > div > div > div > div {
    background: var(--accent-teal) !important;
}

[data-testid="stSlider"] [role="slider"] {
    background: var(--accent-teal) !important;
    border: 2px solid var(--bg-primary) !important;
    box-shadow: 0 0 6px rgba(0, 201, 177, 0.4) !important;
}

/* ── Checkboxes & Radio ── */
[data-testid="stCheckbox"] label,
[data-testid="stRadio"] label {
    color: var(--text-secondary) !important;
}

[data-baseweb="checkbox"] span,
[data-baseweb="radio"] span {
    border-color: var(--border-dim) !important;
    background-color: var(--bg-secondary) !important;
}

/* ── Expanders ── */
.streamlit-expanderHeader {
    background-color: var(--bg-secondary) !important;
    color: var(--accent-teal) !important;
    border: 1px solid var(--border-dim) !important;
    border-radius: 6px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em;
}

.streamlit-expanderHeader:hover {
    border-color: var(--accent-teal) !important;
    background-color: rgba(0, 201, 177, 0.05) !important;
}

.streamlit-expanderContent {
    background-color: var(--bg-deep) !important;
    border: 1px solid var(--border-dim) !important;
    border-top: none !important;
    border-radius: 0 0 6px 6px !important;
}

/* ── Alert boxes ── */
[data-testid="stAlert"] {
    background-color: var(--bg-secondary) !important;
    border-radius: 8px !important;
}

[data-testid="stAlert"][data-type="success"] {
    border-left: 4px solid #00C9B1 !important;
}

[data-testid="stAlert"][data-type="error"] {
    border-left: 4px solid var(--red) !important;
}

[data-testid="stAlert"][data-type="warning"] {
    border-left: 4px solid var(--orange) !important;
}

[data-testid="stAlert"][data-type="info"] {
    border-left: 4px solid var(--accent-blue) !important;
}

/* ── Progress bars ── */
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, var(--accent-teal), var(--accent-blue)) !important;
    border-radius: 4px;
}

[data-testid="stProgressBar"] > div {
    background-color: var(--bg-secondary) !important;
    border-radius: 4px;
}

/* ── Dividers ── */
hr {
    border: none !important;
    border-top: 1px solid var(--border-dim) !important;
    margin: 1.2rem 0 !important;
}

/* ── Typography ── */
h1 {
    color: var(--accent-teal) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em;
}
h2 {
    color: var(--accent-teal) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em;
}
h3 {
    color: var(--accent-blue) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
}
h4, h5, h6 {
    color: var(--accent-soft) !important;
    font-family: 'Rajdhani', sans-serif !important;
}
p, li {
    color: var(--text-secondary) !important;
    line-height: 1.65;
}
label {
    color: var(--text-secondary) !important;
}
strong {
    color: #E8F4F8 !important;
}
code {
    background-color: var(--bg-deep) !important;
    color: var(--accent-teal) !important;
    border: 1px solid var(--border-dim) !important;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85em;
    padding: 0.1em 0.35em;
}

/* ── Caption ── */
[data-testid="stCaption"],
.stCaption {
    color: var(--text-faint) !important;
    font-size: 0.78rem !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] {
    color: var(--accent-teal) !important;
}

/* ── Toast / notification ── */
[data-testid="stToast"] {
    background-color: var(--bg-secondary) !important;
    border: 1px solid var(--accent-teal) !important;
    color: var(--text-primary) !important;
    border-radius: 8px !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: var(--accent-teal); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-blue); }
::-webkit-scrollbar-track { background: var(--bg-deep); }

/* ── Sidebar collapse button >> << ── */
[data-testid="stIconMaterial"] {
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    position: absolute !important;
}

[data-testid="stExpandSidebarButton"] button,
[data-testid="stSidebarCollapseButton"] button {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    width: 24px !important;
    height: 24px !important;
    position: relative !important;
    color: transparent !important;
    font-size: 0 !important;
}

[data-testid="stExpandSidebarButton"] button::after {
    content: '>>' !important;
    color: #00C9B1 !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    font-family: 'Rajdhani', sans-serif !important;
    position: absolute !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
}

[data-testid="stSidebarCollapseButton"] button::after {
    content: '<<' !important;
    color: #00C9B1 !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    font-family: 'Rajdhani', sans-serif !important;
    position: absolute !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
}
/* ── Markdown tables ── */
table {
    background-color: var(--bg-secondary) !important;
    border-collapse: collapse;
    width: 100%;
    border-radius: 6px;
    overflow: hidden;
}
th {
    background-color: var(--border-dim) !important;
    color: var(--accent-teal) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    font-size: 0.82rem;
    padding: 9px 14px;
    text-align: left;
    border: 1px solid #162840;
}
td {
    background-color: var(--bg-secondary) !important;
    color: var(--text-secondary) !important;
    padding: 7px 14px;
    border: 1px solid #162840;
    font-size: 0.9rem;
}
tr:hover td {
    background-color: rgba(0, 201, 177, 0.04) !important;
}

/* ── Download button ── */
[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, var(--border-dim) 0%, var(--bg-secondary) 100%) !important;
    color: var(--accent-teal) !important;
    border: 1px solid var(--accent-teal) !important;
    border-radius: 6px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
}

/* ── Plotly chart containers ── */
[data-testid="stPlotlyChart"] {
    background-color: transparent !important;
    border-radius: 8px;
    overflow: hidden;
}

.js-plotly-plot .plotly .bg {
    fill: var(--bg-secondary) !important;
}

/* ── Alert severity cards ── */
.alert-critical {
    background: linear-gradient(135deg, #1a0808 0%, #2a0f0f 100%) !important;
    border-left: 4px solid var(--red) !important;
    padding: 10px 14px;
    border-radius: 0 6px 6px 0;
    margin: 4px 0;
    color: var(--text-primary) !important;
    box-shadow: inset 0 0 20px rgba(255, 68, 68, 0.05);
}
.alert-high {
    background: linear-gradient(135deg, #1a1008 0%, #2a1a0f 100%) !important;
    border-left: 4px solid var(--orange) !important;
    padding: 10px 14px;
    border-radius: 0 6px 6px 0;
    margin: 4px 0;
    color: var(--text-primary) !important;
    box-shadow: inset 0 0 20px rgba(255, 179, 71, 0.05);
}
.alert-medium {
    background: linear-gradient(135deg, #191900 0%, #2a2a0a 100%) !important;
    border-left: 4px solid var(--yellow) !important;
    padding: 10px 14px;
    border-radius: 0 6px 6px 0;
    margin: 4px 0;
    color: var(--text-primary) !important;
    box-shadow: inset 0 0 20px rgba(255, 215, 0, 0.05);
}
.alert-low {
    background: linear-gradient(135deg, #081818 0%, #0f2525 100%) !important;
    border-left: 4px solid var(--accent-teal) !important;
    padding: 10px 14px;
    border-radius: 0 6px 6px 0;
    margin: 4px 0;
    color: var(--text-primary) !important;
}

/* ── Status badge helpers ── */
.badge-online {
    display: inline-block;
    background: rgba(0, 201, 177, 0.15);
    color: var(--accent-teal);
    border: 1px solid var(--accent-teal);
    border-radius: 12px;
    padding: 2px 10px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-family: 'JetBrains Mono', monospace;
}
.badge-offline {
    display: inline-block;
    background: rgba(255, 68, 68, 0.12);
    color: var(--red);
    border: 1px solid var(--red);
    border-radius: 12px;
    padding: 2px 10px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-family: 'JetBrains Mono', monospace;
}
.badge-warning {
    display: inline-block;
    background: rgba(255, 179, 71, 0.12);
    color: var(--orange);
    border: 1px solid var(--orange);
    border-radius: 12px;
    padding: 2px 10px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Semi-3D card hover effects ── */
.alert-critical, .alert-high, .alert-medium {
    position: relative;
    transform: perspective(800px) rotateX(0deg);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.alert-critical:hover {
    transform: perspective(800px) rotateX(1deg) translateY(-1px);
    box-shadow: 0 6px 20px rgba(255,68,68,0.35) !important;
}
.alert-high:hover {
    transform: perspective(800px) rotateX(1deg) translateY(-1px);
    box-shadow: 0 6px 20px rgba(255,136,0,0.35) !important;
}
.alert-medium:hover {
    transform: perspective(800px) rotateX(1deg) translateY(-1px);
    box-shadow: 0 6px 20px rgba(255,187,51,0.35) !important;
}

/* ── Animations ── */
@keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
}
.loading-shimmer {
    background: linear-gradient(90deg, #0D1B2A 25%, #142333 50%, #0D1B2A 75%);
    background-size: 1000px 100%;
    animation: shimmer 2s infinite linear;
    border-radius: 8px;
    height: 20px;
    margin: 4px 0;
}

@keyframes pulse-teal {
    0%, 100% { box-shadow: 0 0 0 0 rgba(0,201,177,0.4); }
    50% { box-shadow: 0 0 0 8px rgba(0,201,177,0); }
}
.pulse-active {
    animation: pulse-teal 2s ease-in-out infinite;
}

</style>
"""


def apply_dark_theme():
    """Call this at the top of every page to apply dark theme."""
    st.markdown(DARK_CSS, unsafe_allow_html=True)


def apply_theme():
    """Alias for backward compatibility."""
    apply_dark_theme()


def main_header(title: str, subtitle: str = None):
    """Styled page header with teal accent bar."""
    sub_html = (
        f'<p style="color:#4FC3F7; margin:0.25rem 0 0 0; font-size:0.92rem; '
        f'font-family:\'Rajdhani\',sans-serif; letter-spacing:0.04em;">{subtitle}</p>'
        if subtitle else ""
    )
    html = f"""
    <div style="
        border-bottom: 2px solid #00C9B1;
        padding: 0 0 1rem 0;
        margin-bottom: 1.5rem;
        position: relative;
    ">
        <div style="
            position: absolute;
            left: 0; top: 0;
            width: 4px; height: 100%;
            background: linear-gradient(180deg, #00C9B1, #0077B6);
            border-radius: 2px;
        "></div>
        <h1 style="
            color:#00C9B1;
            margin: 0 0 0 1rem;
            font-size: 1.85rem;
            font-family: 'Rajdhani', sans-serif;
            font-weight: 700;
            letter-spacing: 0.05em;
        ">{title}</h1>
        <div style="margin-left: 1rem;">{sub_html}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def section_header(title: str, icon: str = ""):
    """Smaller section header for use inside tabs."""
    html = f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 1.2rem 0 0.6rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid #1E3A5F;
    ">
        {'<span style="font-size:1.1rem;">' + icon + '</span>' if icon else ''}
        <h3 style="
            color: #4FC3F7;
            margin: 0;
            font-family: 'Rajdhani', sans-serif;
            font-weight: 600;
            font-size: 1.05rem;
            letter-spacing: 0.04em;
        ">{title}</h3>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def status_card(label: str, value: str, status: str = "normal"):
    """
    Inline status card. status: 'normal' | 'good' | 'warning' | 'critical'
    """
    color_map = {
        "good":     ("#00C9B1", "rgba(0,201,177,0.10)"),
        "warning":  ("#FFB347", "rgba(255,179,71,0.10)"),
        "critical": ("#FF4444", "rgba(255,68,68,0.10)"),
        "normal":   ("#4FC3F7", "rgba(79,195,247,0.08)"),
    }
    color, bg = color_map.get(status, color_map["normal"])
    html = f"""
    <div style="
        background: {bg};
        border: 1px solid {color};
        border-left: 4px solid {color};
        border-radius: 6px;
        padding: 0.55rem 0.9rem;
        margin: 0.3rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    ">
        <span style="color:#8899AA; font-size:0.82rem; font-family:'Rajdhani',sans-serif;
                     font-weight:600; text-transform:uppercase; letter-spacing:0.05em;">
            {label}
        </span>
        <span style="color:{color}; font-family:'JetBrains Mono',monospace;
                     font-size:0.95rem; font-weight:600;">
            {value}
        </span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_classifying_spinner(placeholder):
    """
    Renders an animated teal gauge in the given st.empty() placeholder
    while classification is running. Call before model inference, clear after.
    """
    import plotly.graph_objects as go
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=82,
        title={'text': "AI Classifying...", 'font': {'color': '#00C9B1', 'size': 14}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': '#1E3A4A'},
            'bar': {'color': '#00C9B1', 'thickness': 0.3},
            'bgcolor': '#0D1B2A',
            'bordercolor': '#1E3A4A',
            'steps': [
                {'range': [0, 40], 'color': '#0D2030'},
                {'range': [40, 75], 'color': '#0D2A3A'},
                {'range': [75, 100], 'color': '#003D35'},
            ],
        },
        number={'font': {'color': '#00C9B1', 'size': 20}, 'suffix': '%'}
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#D4EBF8'),
        height=180,
        margin=dict(l=20, r=20, t=30, b=10),
    )
    placeholder.plotly_chart(fig, use_container_width=True)