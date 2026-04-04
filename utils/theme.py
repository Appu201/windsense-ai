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

/* ── Sidebar toggle (FIXED & VISIBLE) ── */
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"] {
    position: fixed !important;
    top: 1rem !important;
    left: 0.5rem !important;
    z-index: 1000 !important;
}

[data-testid="stExpandSidebarButton"] button,
[data-testid="stSidebarCollapseButton"] button {
    background: rgba(13, 27, 42, 0.9) !important;
    border: 1px solid #00C9B1 !important;
    border-radius: 6px !important;
    width: 36px !important;
    height: 28px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0 !important;
    backdrop-filter: blur(6px);
}

[data-testid="stExpandSidebarButton"] button *,
[data-testid="stSidebarCollapseButton"] button * {
    display: none !important;
}

[data-testid="stExpandSidebarButton"] button::after {
    content: '>>';
    color: #00C9B1;
    font-weight: 700;
    font-size: 0.95rem;
}

[data-testid="stSidebarCollapseButton"] button::after {
    content: '<<';
    color: #00C9B1;
    font-weight: 700;
    font-size: 0.95rem;
}

[data-testid="stExpandSidebarButton"] button:hover,
[data-testid="stSidebarCollapseButton"] button:hover {
    box-shadow: 0 0 10px rgba(0, 201, 177, 0.4);
    border-color: #4FC3F7 !important;
}

</style>
"""

def apply_dark_theme():
    st.markdown(DARK_CSS, unsafe_allow_html=True)

def apply_theme():
    apply_dark_theme()