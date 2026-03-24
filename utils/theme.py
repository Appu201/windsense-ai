# utils/theme.py — WindSense AI Dark Theme
import streamlit as st

DARK_CSS = """
<style>

/* ── Base ── */
.stApp,
.main,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"] {
    background-color: #0D1B2A !important;
    color: #E0E0E0 !important;
}

.main .block-container {
    background-color: #0D1B2A !important;
    padding: 1.5rem 2rem;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1B2A 0%, #1a2a3a 100%) !important;
    border-right: 1px solid #00C9B1 !important;
}

[data-testid="stSidebar"] * {
    color: #D0D8E0 !important;
}

[data-testid="stSidebarNav"] {
    display: none;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background-color: #091520 !important;
    border-bottom: 2px solid #00C9B1 !important;
    gap: 0.25rem;
    padding: 0 0.5rem;
}

.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    color: #607080 !important;
    border: none !important;
    font-weight: 600;
    font-size: 0.82rem;
    padding: 0.6rem 0.8rem;
    border-radius: 4px 4px 0 0;
    transition: color 0.2s;
}

.stTabs [aria-selected="true"] {
    background-color: #00C9B1 !important;
    color: #0D1B2A !important;
    border-bottom: 3px solid #00C9B1 !important;
}

.stTabs [data-baseweb="tab-panel"] {
    background-color: #0D1B2A !important;
    padding: 1rem 0;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background-color: #112233;
    border: 1px solid #1E3A5F;
    border-radius: 8px;
    padding: 0.75rem 1rem;
}

[data-testid="stMetricValue"] {
    color: #00C9B1 !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
}

[data-testid="stMetricLabel"] {
    color: #8899AA !important;
    font-size: 0.82rem !important;
}

[data-testid="stMetricDelta"] {
    font-size: 0.75rem !important;
}

/* ── DataFrames ── */
[data-testid="stDataFrame"] > div {
    background-color: #112233 !important;
    border: 1px solid #00C9B1 !important;
}

.dvn-scroller {
    background-color: #112233 !important;
}

/* ── DataFrame text fix ── */
[data-testid="stDataFrame"] canvas {
    color: #D0D8E0 !important;
}
.glideDataEditor {
    background-color: #112233 !important;
    color: #D0D8E0 !important;
}
.dvn-scroller * {
    color: #D0D8E0 !important;
}
[data-testid="stDataFrame"] * {
    color: #D0D8E0 !important;
    background-color: #112233 !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #007A6E 0%, #005580 100%) !important;
    color: #FFFFFF !important;
    border: 1px solid #00C9B1 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #00C9B1 0%, #0077B6 100%) !important;
}

.stButton > button:hover {
    opacity: 0.88 !important;
    border-color: #4FC3F7 !important;
}

/* ── Text inputs / selects ── */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
    background-color: #112233 !important;
    color: #E0E0E0 !important;
    border: 1px solid #1E3A5F !important;
    border-radius: 6px !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: #00C9B1 !important;
    box-shadow: 0 0 0 1px #00C9B1 !important;
}

.stSelectbox > div > div {
    background-color: #112233 !important;
    color: #E0E0E0 !important;
    border: 1px solid #1E3A5F !important;
}

/* ── Expanders ── */
.streamlit-expanderHeader {
    background-color: #112233 !important;
    color: #00C9B1 !important;
    border: 1px solid #1E3A5F !important;
    border-radius: 6px !important;
}

.streamlit-expanderContent {
    background-color: #091520 !important;
    border: 1px solid #1E3A5F !important;
    border-top: none !important;
}

/* ── Alert boxes ── */
[data-testid="stAlert"] {
    background-color: #112233 !important;
    border-radius: 8px !important;
}

/* ── Dividers ── */
hr {
    border-color: #1E3A5F !important;
}

/* ── Typography ── */
h1 { color: #00C9B1 !important; font-weight: 700 !important; }
h2 { color: #00C9B1 !important; font-weight: 600 !important; }
h3 { color: #4FC3F7 !important; font-weight: 600 !important; }
h4, h5, h6 { color: #89CFFE !important; }
p, li, label { color: #D0D8E0 !important; }
strong { color: #E8F4F8 !important; }

/* ── Caption ── */
[data-testid="stCaption"],
.stCaption {
    color: #5E7A8A !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; background: #091520; }
::-webkit-scrollbar-thumb { background: #00C9B1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #4FC3F7; }

/* ── Markdown tables ── */
table {
    background-color: #112233 !important;
    border-collapse: collapse;
    width: 100%;
}
th {
    background-color: #1E3A5F !important;
    color: #00C9B1 !important;
    padding: 8px 12px;
    text-align: left;
    border: 1px solid #1E3A5F;
}
td {
    background-color: #112233 !important;
    color: #D0D8E0 !important;
    padding: 6px 12px;
    border: 1px solid #1A2A3A;
}

/* ── Download button ── */
[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, #1E3A5F 0%, #112233 100%) !important;
    color: #00C9B1 !important;
    border: 1px solid #00C9B1 !important;
}

/* ── Alert cards ── */
.alert-critical {
    background: linear-gradient(135deg, #1a0a0a 0%, #2d0f0f 100%) !important;
    border-left: 4px solid #FF4444 !important;
    padding: 10px 14px;
    border-radius: 0 6px 6px 0;
    margin: 4px 0;
    color: #E0E0E0 !important;
}
.alert-high {
    background: linear-gradient(135deg, #1a110a 0%, #2d1a0f 100%) !important;
    border-left: 4px solid #FFB347 !important;
    padding: 10px 14px;
    border-radius: 0 6px 6px 0;
    margin: 4px 0;
    color: #E0E0E0 !important;
}
.alert-medium {
    background: linear-gradient(135deg, #1a1a0a 0%, #2d2a0f 100%) !important;
    border-left: 4px solid #FFD700 !important;
    padding: 10px 14px;
    border-radius: 0 6px 6px 0;
    margin: 4px 0;
    color: #E0E0E0 !important;
}

</style>
"""


def apply_dark_theme():
    """Call this at the top of every page to apply dark theme"""
    st.markdown(DARK_CSS, unsafe_allow_html=True)


def apply_theme():
    """Alias for backward compatibility"""
    apply_dark_theme()


def main_header(title, subtitle=None):
    """Styled page header"""
    html = f"""
    <div style="
        border-bottom: 2px solid #00C9B1;
        padding: 0 0 1rem 0;
        margin-bottom: 1.5rem;
    ">
        <h1 style="color:#00C9B1; margin:0; font-size:1.9rem;">{title}</h1>
        {f'<p style="color:#4FC3F7; margin:0.2rem 0 0 0; font-size:0.9rem;">{subtitle}</p>'
         if subtitle else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)