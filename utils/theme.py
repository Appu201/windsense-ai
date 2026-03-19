# utils/theme.py — WindSense AI Dark Theme
import streamlit as st

WINDSENSE_CSS = """
<style>

/* ══ GLOBAL ══ */
:root {
    --bg-primary:   #0D1B2A;
    --bg-secondary: #1a2a3a;
    --bg-card:      #162233;
    --teal:         #00C9B1;
    --blue:         #4FC3F7;
    --white:        #FFFFFF;
    --grey:         #8899AA;
    --critical:     #FF4444;
    --high:         #FF8800;
    --medium:       #FFBB33;
    --success:      #4CAF50;
    --shadow-teal:  0 0 15px rgba(0,201,177,0.25);
}

.stApp { background-color: var(--bg-primary); color: var(--white); }
.main .block-container { background-color: var(--bg-primary); padding-top: 2rem; }

/* ══ SIDEBAR ══ */
[data-testid="stSidebar"] {
    background-color: var(--bg-secondary);
    border-right: 1px solid rgba(0,201,177,0.3);
}
[data-testid="stSidebar"] .stButton button {
    background-color: transparent;
    color: var(--blue);
    border: 1px solid #2a3a4a;
    text-align: left;
    border-radius: 8px;
    transition: all 0.2s ease;
    font-size: 0.9rem;
}
[data-testid="stSidebar"] .stButton button:hover {
    background-color: var(--bg-card);
    border-color: var(--teal);
    color: var(--teal);
    box-shadow: var(--shadow-teal);
}

/* ══ METRICS ══ */
[data-testid="stMetric"] {
    background: var(--bg-card);
    border: 1px solid rgba(0,201,177,0.2);
    border-radius: 10px;
    padding: 0.8rem;
}
[data-testid="stMetricValue"] { color: var(--teal) !important; font-size: 1.5rem !important; }
[data-testid="stMetricLabel"] { color: var(--blue) !important; font-size: 0.8rem !important; }

/* ══ HEADINGS ══ */
h1, h2, h3 { color: var(--teal) !important; }

/* ══ BUTTONS - PRIMARY ══ */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--teal) 0%, #00a896 100%);
    color: var(--bg-primary);
    border: none;
    font-weight: bold;
    border-radius: 8px;
    transition: all 0.2s ease;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-teal);
}

/* ══ TABS ══ */
.stTabs [data-baseweb="tab-list"] {
    background-color: var(--bg-secondary);
    border-radius: 10px;
    padding: 0.3rem;
    gap: 0.2rem;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    color: var(--grey);
    border-radius: 7px;
    font-weight: 600;
    transition: all 0.2s ease;
}
.stTabs [aria-selected="true"] {
    background-color: var(--teal) !important;
    color: var(--bg-primary) !important;
}

/* ══ INPUTS ══ */
.stTextInput input,
.stTextArea textarea,
.stSelectbox > div > div {
    background-color: var(--bg-secondary) !important;
    border: 1px solid rgba(0,201,177,0.3) !important;
    color: var(--white) !important;
    border-radius: 8px !important;
}
.stTextInput input:focus { border-color: var(--teal) !important; box-shadow: var(--shadow-teal) !important; }

/* ══ DATAFRAMES ══ */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(0,201,177,0.2);
    border-radius: 8px;
}

/* ══ EXPANDER ══ */
.streamlit-expanderHeader {
    background-color: var(--bg-card) !important;
    border: 1px solid rgba(0,201,177,0.2) !important;
    border-radius: 8px !important;
    color: var(--white) !important;
}

/* ══ DIVIDER ══ */
hr { border-color: rgba(0,201,177,0.2) !important; }

/* ══ ALERT CARDS ══ */
.alert-critical {
    background: linear-gradient(135deg, #2a0a0a, #1a0505);
    border-left: 4px solid var(--critical);
    padding: 0.8rem 1rem;
    border-radius: 8px;
    margin: 0.4rem 0;
    color: var(--white);
}
.alert-high {
    background: linear-gradient(135deg, #2a1400, #1a0c00);
    border-left: 4px solid var(--high);
    padding: 0.8rem 1rem;
    border-radius: 8px;
    margin: 0.4rem 0;
    color: var(--white);
}
.alert-medium {
    background: linear-gradient(135deg, #2a2000, #1a1500);
    border-left: 4px solid var(--medium);
    padding: 0.8rem 1rem;
    border-radius: 8px;
    margin: 0.4rem 0;
    color: var(--white);
}

/* ══ WIND CARD (reusable component) ══ */
.wind-card {
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-secondary) 100%);
    border: 1px solid rgba(0,201,177,0.25);
    border-radius: 12px;
    padding: 1.2rem;
    margin: 0.5rem 0;
    box-shadow: var(--shadow-teal);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.wind-card:hover {
    transform: translateY(-2px);
    border-color: var(--teal);
}

</style>
"""

def apply_theme():
    """Call this at the top of every page to apply dark theme"""
    st.markdown(WINDSENSE_CSS, unsafe_allow_html=True)

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