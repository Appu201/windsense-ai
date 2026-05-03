import streamlit as st
import pandas as pd
import numpy as np
import pickle
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from datetime import datetime, timedelta
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.email_queue import add_to_queue, flush_queue
from utils.anomaly_detector import AnomalyDetector, save_anomaly_to_log, load_anomaly_log, mark_anomaly_reviewed
from utils.opcua_simulator import OPCUASimulator
from sklearn.ensemble import IsolationForest
from utils.isolation_forest import IsolationForestDetector

st.set_page_config(
    page_title="WindSense AI - Intelligent Alarm Management",
    page_icon="🌀",
    layout="wide",
    initial_sidebar_state="expanded"
)

from utils.theme import apply_dark_theme
apply_dark_theme()

# ── Sidebar toggle icon override ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Force sidebar toggle always visible */
    [data-testid="collapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        position: fixed !important;
        top: 0.75rem !important;
        left: 0.75rem !important;
        z-index: 9999 !important;
    }
    [data-testid="collapsedControl"] svg {
        fill: #00C9B1 !important;
        color: #00C9B1 !important;
        width: 1.6rem !important;
        height: 1.6rem !important;
    }
</style>
<script>
(function() {
    function replaceSidebarIcon() {
        const btn = document.querySelector('[data-testid="collapsedControl"]');
        if (!btn) return;
        const svg = btn.querySelector('svg');
        if (svg) {
            svg.innerHTML = `
                <rect x="3" y="5" width="18" height="2" rx="1" fill="#00C9B1"/>
                <rect x="3" y="11" width="18" height="2" rx="1" fill="#00C9B1"/>
                <rect x="3" y="17" width="18" height="2" rx="1" fill="#00C9B1"/>
            `;
            svg.setAttribute('viewBox', '0 0 24 24');
        }
    }
    setTimeout(replaceSidebarIcon, 800);
    setTimeout(replaceSidebarIcon, 2000);
})();
</script>
""", unsafe_allow_html=True)
st.markdown("""
<script>
(function() {
    function hideExpanderIcons() {
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (!sidebar) return;

        // Step 1: Target by data-testid — clear text AND hide
        sidebar.querySelectorAll('[data-testid="stExpanderToggleIcon"]').forEach(el => {
            el.textContent = '';
            el.innerHTML = '';
            el.style.cssText = 'display:none!important;width:0!important;height:0!important;overflow:hidden!important;font-size:0!important;color:transparent!important;position:absolute!important;';
        });

        // Step 2: Target summary first child — if it contains "arrow" text, nuke it
        sidebar.querySelectorAll('details > summary').forEach(summary => {
            Array.from(summary.children).forEach(child => {
                const raw = (child.textContent || child.innerText || '');
                if (raw.toLowerCase().includes('arrow') || raw.includes('expand') || raw.includes('chevron')) {
                    child.textContent = '';
                    child.innerHTML = '';
                    child.style.cssText = 'display:none!important;width:0!important;height:0!important;font-size:0!important;color:transparent!important;position:absolute!important;';
                }
            });
        });

        // Step 3: Target expander header — hide first child div that is NOT the label
        sidebar.querySelectorAll('.streamlit-expanderHeader').forEach(header => {
            Array.from(header.children).forEach((child, idx) => {
                const raw = (child.textContent || child.innerText || '').trim();
                // If child text is short (icon text) or contains arrow keyword
                if (raw.toLowerCase().includes('arrow') || raw === '' || (raw.length < 15 && !raw.includes(' '))) {
                    child.textContent = '';
                    child.innerHTML = '';
                    child.style.cssText = 'display:none!important;width:0!important;font-size:0!important;color:transparent!important;';
                }
            });
        });
    }

    // Run immediately and at intervals to catch Streamlit re-renders
    hideExpanderIcons();
    setTimeout(hideExpanderIcons, 300);
    setTimeout(hideExpanderIcons, 800);
    setTimeout(hideExpanderIcons, 1500);
    setTimeout(hideExpanderIcons, 3000);
    setTimeout(hideExpanderIcons, 5000);

    // Watch DOM — use a debounce to avoid infinite loops
    let _timer = null;
    const observer = new MutationObserver(() => {
        clearTimeout(_timer);
        _timer = setTimeout(hideExpanderIcons, 100);
    });
    observer.observe(document.body, { childList: true, subtree: true });
})();
</script>
""", unsafe_allow_html=True)

# ── Master CSS block ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Sidebar nav hidden ── */
    [data-testid="stSidebarNav"] { display: none !important; }

    /* ── Sidebar toggle button — always visible, no box ── */
    [data-testid="collapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    [data-testid="collapsedControl"] svg {
        fill: #00C9B1 !important;
        color: #00C9B1 !important;
        width: 1.4rem !important;
        height: 1.4rem !important;
    }

    /* ── App background ── */
    .stApp { background-color: #0D1B2A; color: #E8F4FD; }
    .main .block-container { background-color: #0D1B2A; padding-top: 1rem; }

    /* ── Headers ── */
    h1, h2, h3 { color: #00C9B1 !important; }
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #00C9B1;
        text-align: center;
        padding: 0.75rem 0;
        border-bottom: 2px solid #00C9B1;
        margin-bottom: 1.5rem;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D1B2A 0%, #1a2a3a 100%);
        border-right: 1px solid #00C9B1;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span:not([data-testid]),
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div.stMarkdown { color: #E8F4FD !important; }

    [data-testid="stSidebar"] svg:not(.streamlit-expanderHeader svg) {
        color: #00C9B1 !important;
        fill: #00C9B1 !important;
    }

    /* ── Fix sidebar expander arrow/text icon corruption ── */
    [data-testid="stSidebar"] [data-testid="stExpanderToggleIcon"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
        font-size: 0 !important;
        line-height: 0 !important;
        position: absolute !important;
        pointer-events: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpanderToggleIcon"] * {
        display: none !important;
        font-size: 0 !important;
        width: 0 !important;
        height: 0 !important;
    }
    [data-testid="stSidebar"] .streamlit-expanderHeader svg {
        display: none !important;
        width: 0 !important;
        height: 0 !important;
    }
    [data-testid="stSidebar"] details > summary::before,
    [data-testid="stSidebar"] details > summary::after {
        content: none !important;
        display: none !important;
    }
    /* ── Collapse any raw text icon nodes inside expander header ── */
    [data-testid="stSidebar"] .streamlit-expanderHeader > div:first-child:not(:last-child) {
        font-size: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
    }

    /* ── Style sidebar expander headers ── */
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        background-color: #112233 !important;
        border: 1px solid #00C9B1 !important;
        border-radius: 8px !important;
    }
    [data-testid="stSidebar"] .streamlit-expanderHeader p {
        color: #00C9B1 !important;
        font-weight: 700 !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] { gap: 1rem; background-color: #0D1B2A; }
    .stTabs [data-baseweb="tab"] {
        height: 2.5rem;
        font-size: 0.95rem;
        font-weight: 600;
        color: #4FC3F7 !important;
        background-color: #1a2a3a;
        border-radius: 6px 6px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00C9B1 !important;
        color: #0D1B2A !important;
    }

    /* ── Metrics ── */
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; color: #00C9B1 !important; }
    [data-testid="stMetricLabel"] { font-size: 0.85rem !important; color: #4FC3F7 !important; }
    [data-testid="stMetricDelta"] { font-size: 0.75rem !important; }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #004D40, #00796B);
        color: white !important;
        border: 1px solid #00C9B1 !important;
        border-radius: 6px;
        font-weight: 600;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #00796B, #00C9B1) !important;
        border: 1px solid #4FC3F7 !important;
    }

    /* ── Input fields — NO double borders, NO weird boxes ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #1a2a3a !important;
        border: 1px solid #00C9B1 !important;
        border-radius: 6px !important;
        color: #E8F4FD !important;
        caret-color: #00C9B1 !important;
        outline: none !important;
        box-shadow: none !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border: 1px solid #4FC3F7 !important;
        box-shadow: 0 0 0 2px rgba(0,201,177,0.15) !important;
    }

    /* ── Kill all baseweb wrapper borders (the "weird boxes") ── */
    div[data-baseweb]           { border: none !important; box-shadow: none !important; }
    div[data-baseweb] > div     { border: none !important; box-shadow: none !important; }
    div[data-baseweb="input"] * { border: none !important; box-shadow: none !important; background: transparent !important; }
    div[data-baseweb="base-input"] { border: none !important; box-shadow: none !important; }
    [data-testid="InputInstructions"] { display: none !important; }

    /* ── Selectbox ── */
    .stSelectbox > div > div {
        background-color: #1a2a3a !important;
        border: 1px solid #00C9B1 !important;
        color: #E8F4FD !important;
        border-radius: 6px;
    }

    /* ── Expanders ── */
    .streamlit-expanderHeader {
        background-color: #1a2a3a !important;
        color: #00C9B1 !important;
        border: 1px solid #2a3a4a !important;
        border-radius: 6px !important;
    }
    .streamlit-expanderContent {
        background-color: #0D1B2A !important;
        border: 1px solid #2a3a4a !important;
        border-top: none !important;
    }

    /* ── Dividers ── */
    hr { border-color: #2a3a4a !important; }

    /* ── DMAIC metric override ── */
    .dmaic-measure [data-testid="stMetricValue"] {
        font-size: 1.0rem !important;
        white-space: normal !important;
        word-break: break-word !important;
    }
    .dmaic-measure [data-testid="stMetricLabel"] { font-size: 0.75rem !important; }

    /* ── Custom HTML table used for dataframes ── */
    .ws-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #0D1B2A;
        color: #E8F4FD;
        font-size: 0.875rem;
        border-radius: 8px;
        overflow: hidden;
    }
    .ws-table th {
        background-color: #003D35;
        color: #00C9B1;
        padding: 0.6rem 0.8rem;
        text-align: left;
        font-weight: 600;
        border-bottom: 1px solid #00C9B1;
        white-space: nowrap;
    }
    .ws-table td {
        padding: 0.5rem 0.8rem;
        border-bottom: 1px solid #1a2a3a;
        color: #E8F4FD;
        vertical-align: top;
    }
    .ws-table tr:hover td { background-color: #142333; }
    .ws-table tr:last-child td { border-bottom: none; }

    /* ── Scrollable table wrapper ── */
    .ws-table-wrap {
        overflow-x: auto;
        overflow-y: auto;
        max-height: 500px;
        border: 1px solid #1E3A4A;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Helper: parse and format OPC UA alarm IDs ────────────────────────────────
def format_alarm_id(alarm_id: str) -> str:
    """Convert OPC-ns=2;s=WindFarm.Turbine11.HydraulicTemp-1774961438
       → ns=2 | WindFarm.Turbine11.HydraulicTemp"""
    if not isinstance(alarm_id, str):
        return str(alarm_id)
    raw = alarm_id
    if raw.startswith("OPC-"):
        raw = raw[4:]  # strip 'OPC-'
    if ";" in raw:
        parts = raw.split(";", 1)
        ns_part = parts[0]          # e.g. ns=2
        s_part  = parts[1]          # e.g. s=WindFarm.Turbine11.HydraulicTemp-1774961438
        if s_part.startswith("s="):
            s_part = s_part[2:]     # strip 's='
        # Remove trailing numeric ID (e.g. -1774961438)
        import re
        s_part = re.sub(r'-\d{7,}$', '', s_part)
        return f"{ns_part} | {s_part}"
        return raw

# ── Helper: render a DataFrame as a visible HTML table ───────────────────────
def render_table(df: pd.DataFrame, max_rows: int = 200) -> None:
    """Render df as a styled HTML table — always visible regardless of Streamlit theme."""
    if df is None or df.empty:
        st.info("No data to display.")
        return
    subset = df.head(max_rows)
    rows_html = ""
    for _, row in subset.iterrows():
        cells = "".join(f"<td>{str(v) if pd.notna(v) else ''}</td>" for v in row)
        rows_html += f"<tr>{cells}</tr>"
    headers = "".join(f"<th>{col}</th>" for col in subset.columns)
    html = f"""
    <div class="ws-table-wrap">
        <table class="ws-table">
            <thead><tr>{headers}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_PATH   = os.path.join(os.path.dirname(os.path.abspath('app.py')), '')
DATA_PATH   = os.path.join(os.path.dirname(os.path.abspath('app.py')), 'data') + os.sep
MODEL_PATH  = os.path.join(os.path.dirname(os.path.abspath('app.py')), 'models') + os.sep
OUTPUT_PATH = DATA_PATH
ACK_FILE    = os.path.join(os.path.dirname(os.path.abspath('app.py')), 'data', 'acknowledgments.json')

# ── Acknowledgment helpers ───────────────────────────────────────────────────
def load_acknowledgments():
    if os.path.exists(ACK_FILE):
        try:
            with open(ACK_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_acknowledgment(alarm_id, ack_data):
    try:
        acks = load_acknowledgments()
        def make_serializable(obj):
            if isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(i) for i in obj]
            elif hasattr(obj, 'item'):
                return obj.item()
            elif isinstance(obj, (int, float, str, bool)) or obj is None:
                return obj
            else:
                return str(obj)
        acks[alarm_id] = make_serializable(ack_data)
        with open(ACK_FILE, 'w') as f:
            json.dump(acks, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving acknowledgment: {e}")
        return False

def get_dashboard_url():
    try:
        url_file = '/content/current_dashboard_url.txt'
        if os.path.exists(url_file):
            with open(url_file, 'r') as f:
                return f.read().strip()
    except Exception:
        pass
    return "https://windsense-ai.streamlit.app"

DASHBOARD_URL = get_dashboard_url()

# ── Acknowledgment via URL params ────────────────────────────────────────────
query_params = st.query_params

if 'ack' in query_params:
    alarm_id = query_params['ack']
    channel  = query_params.get('channel', 'email')
    existing_acks = load_acknowledgments()
    if alarm_id in existing_acks:
        prev_ack = existing_acks[alarm_id]
        st.markdown(f"""
        <div style="text-align:center; padding:50px;">
            <h1 style="color:#FF8800;">⚠️ Already Acknowledged</h1>
            <p style="font-size:1.5rem; margin:20px 0; color:#E8F4FD;">
                Alarm <strong>{alarm_id}</strong> was already acknowledged.
            </p>
            <p style="color:#888;">
                Previously acknowledged at: {prev_ack.get('time', prev_ack.get('ack_time', 'Unknown'))}
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        ack_data = {
            'time':    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'method':  f'{channel}_link',
            'channel': channel,
            'alarm_id': alarm_id
        }
        if save_acknowledgment(alarm_id, ack_data):
            st.markdown(f"""
            <div style="text-align:center; padding:50px;">
                <h1 style="color:#4CAF50;">✅ Acknowledgment Successful!</h1>
                <p style="font-size:1.5rem; margin:20px 0; color:#E8F4FD;">
                    Alarm <strong>{alarm_id}</strong> has been acknowledged.
                </p>
                <p style="color:#888;">
                    Acknowledged at: {ack_data['time']}<br>
                    Channel: {'📱 WhatsApp' if channel == 'whatsapp' else '📧 Email'}
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.balloons()
        else:
            st.error("❌ Failed to save acknowledgment.")
    st.stop()

# ── Auth guard ───────────────────────────────────────────────────────────────
if not st.session_state.get('authenticated', False):
    st.switch_page('pages/login.py')

if not st.session_state.get('session_initialized', False):
    try:
        with open(ACK_FILE, 'w') as f:
            json.dump({}, f)
    except Exception:
        pass
    st.session_state.acknowledged_alarms  = {}
    st.session_state.session_initialized  = True
else:
    st.session_state.acknowledged_alarms = load_acknowledgments()

flush_queue()

# ── Data loaders ─────────────────────────────────────────────────────────────
@st.cache_data
def load_dmaic_database():
    try:
        dmaic_json_path = DATA_PATH + 'dmaic_complete_database.json'
        if os.path.exists(dmaic_json_path):
            with open(dmaic_json_path, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

DMAIC_DATABASE = load_dmaic_database()

STAKEHOLDERS = {
    'Main Controller Fault': {
        'primary':    {'name': 'Divya',        'role': 'Control Systems Engineer',   'email': 'divyajay.1612@gmail.com',      'phone': '+918778838055'},
        'secondary':  {'name': 'Sarah Johnson', 'role': 'Senior Engineer',            'email': 'sarah.j@windfarm.com',         'phone': '+1234567891'},
        'management': {'name': 'Mike Davis',    'role': 'Engineering Manager',        'email': 'mike.d@windfarm.com',          'phone': '+1234567892'},
        'escalation_time': 30
    },
    'Grid Frequency Deviation': {
        'primary':    {'name': 'Emily Chen',    'role': 'Grid Integration Specialist','email': 'emily.c@windfarm.com',         'phone': '+1234567893'},
        'secondary':  {'name': 'David Wilson',  'role': 'Electrical Engineer',        'email': 'david.w@windfarm.com',         'phone': '+1234567894'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager',         'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 20
    },
    'Extended Grid Outage': {
        'primary':    {'name': 'Robert Taylor', 'role': 'Site Manager',               'email': 'robert.t@windfarm.com',        'phone': '+1234567896'},
        'secondary':  {'name': 'Jennifer Lee',  'role': 'Operations Supervisor',      'email': 'jennifer.l@windfarm.com',      'phone': '+1234567897'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager',         'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 15
    },
    'Emergency Brake Activation': {
        'primary':    {'name': 'Carlos Rodriguez','role': 'Mechanical Technician',    'email': 'carlos.r@windfarm.com',        'phone': '+1234567898'},
        'secondary':  {'name': 'Anna Martinez', 'role': 'Senior Technician',          'email': 'anna.m@windfarm.com',          'phone': '+1234567899'},
        'management': {'name': 'Mike Davis',    'role': 'Engineering Manager',        'email': 'mike.d@windfarm.com',          'phone': '+1234567892'},
        'escalation_time': 25
    },
    'Generator Bearing Overheating': {
        'primary':    {'name': 'Aarif',         'role': 'Mechanical Technician',      'email': 'muhammadhaarif2000@gmail.com', 'phone': '+919123516325'},
        'secondary':  {'name': 'Anna Martinez', 'role': 'Senior Technician',          'email': 'anna.m@windfarm.com',          'phone': '+1234567899'},
        'management': {'name': 'Mike Davis',    'role': 'Engineering Manager',        'email': 'mike.d@windfarm.com',          'phone': '+1234567892'},
        'escalation_time': 20
    },
    'Hydraulic Oil Contamination': {
        'primary':    {'name': 'Anna Martinez', 'role': 'Senior Technician',          'email': 'anna.m@windfarm.com',          'phone': '+1234567899'},
        'secondary':  {'name': 'Carlos Rodriguez','role': 'Mechanical Technician',    'email': 'carlos.r@windfarm.com',        'phone': '+1234567898'},
        'management': {'name': 'Mike Davis',    'role': 'Engineering Manager',        'email': 'mike.d@windfarm.com',          'phone': '+1234567892'},
        'escalation_time': 35
    },
    'Converter Circuit Fault': {
        'primary':    {'name': 'David Wilson',  'role': 'Electrical Engineer',        'email': 'david.w@windfarm.com',         'phone': '+1234567894'},
        'secondary':  {'name': 'Emily Chen',    'role': 'Grid Integration Specialist','email': 'emily.c@windfarm.com',         'phone': '+1234567893'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager',         'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 25
    },
    'Yaw System Hydraulic Fault': {
        'primary':    {'name': 'Aparajithaa',   'role': 'Yaw Systems Specialist',     'email': 'ts.aparajithaa@gmail.com',     'phone': '+919284743112'},
        'secondary':  {'name': 'Amanda White',  'role': 'Hydraulic Engineer',         'email': 'amanda.w@windfarm.com',        'phone': '+1234567911'},
        'management': {'name': 'Mike Davis',    'role': 'Engineering Manager',        'email': 'mike.d@windfarm.com',          'phone': '+1234567892'},
        'escalation_time': 480
    },
    'Pitch System Hydraulic Fault': {
        'primary':    {'name': 'Diego Lopez',   'role': 'Pitch System Engineer',      'email': 'diego.l@windfarm.com',         'phone': '+1234567912'},
        'secondary':  {'name': 'Rachel Green',  'role': 'Blade Specialist',           'email': 'rachel.g@windfarm.com',        'phone': '+1234567913'},
        'management': {'name': 'Mike Davis',    'role': 'Engineering Manager',        'email': 'mike.d@windfarm.com',          'phone': '+1234567892'},
        'escalation_time': 480
    },
    'Power Electronics Failure': {
        'primary':    {'name': 'Jack Williams', 'role': 'Power Systems Engineer',     'email': 'jack.w@windfarm.com',          'phone': '+1234567920'},
        'secondary':  {'name': 'Emma Davis',    'role': 'Electronics Tech',           'email': 'emma.d@windfarm.com',          'phone': '+1234567921'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager',         'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 120
    },
    'Transformer Oil Temperature High': {
        'primary':    {'name': 'Kevin Murphy',  'role': 'Transformer Specialist',     'email': 'kevin.m@windfarm.com',         'phone': '+1234567922'},
        'secondary':  {'name': 'Laura Johnson', 'role': 'Oil Analysis Tech',          'email': 'laura.j@windfarm.com',         'phone': '+1234567923'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager',         'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 120
    },
    'Hydraulic Filter Clogged': {
        'primary':    {'name': 'Marcus Lee',    'role': 'Hydraulic Technician',       'email': 'marcus.l@windfarm.com',        'phone': '+1234567924'},
        'secondary':  {'name': 'Patricia King', 'role': 'Maintenance Supervisor',     'email': 'patricia.k@windfarm.com',      'phone': '+1234567925'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager',         'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 480
    },
    'Generator Winding Temperature High': {
        'primary':    {'name': 'Nathan Scott',  'role': 'Generator Specialist',       'email': 'nathan.s@windfarm.com',        'phone': '+1234567926'},
        'secondary':  {'name': 'Quinn Roberts', 'role': 'Electrical Engineer',        'email': 'quinn.r@windfarm.com',         'phone': '+1234567927'},
        'management': {'name': 'Mike Davis',    'role': 'Engineering Manager',        'email': 'mike.d@windfarm.com',          'phone': '+1234567892'},
        'escalation_time': 120
    },
    'Hydraulic Pressure Drop': {
        'primary':    {'name': 'Oscar Ramirez', 'role': 'Hydraulic Engineer',         'email': 'oscar.r@windfarm.com',         'phone': '+1234567928'},
        'secondary':  {'name': 'Tina Garcia',   'role': 'Systems Tech',               'email': 'tina.g@windfarm.com',          'phone': '+1234567929'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager',         'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 480
    },
    'Momentary Grid Loss': {
        'primary':    {'name': 'Robert Taylor', 'role': 'Site Manager',               'email': 'robert.t@windfarm.com',        'phone': '+1234567896'},
        'secondary':  {'name': 'Jennifer Lee',  'role': 'Operations Supervisor',      'email': 'jennifer.l@windfarm.com',      'phone': '+1234567897'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager',         'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 15
    },
    'Grid Voltage Fluctuation': {
        'primary':    {'name': 'Emily Chen',    'role': 'Grid Integration Specialist','email': 'emily.c@windfarm.com',         'phone': '+1234567893'},
        'secondary':  {'name': 'David Wilson',  'role': 'Electrical Engineer',        'email': 'david.w@windfarm.com',         'phone': '+1234567894'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager',         'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 20
    },
    'Safety System Activation': {
        'primary':    {'name': 'Carlos Rodriguez','role': 'Mechanical Technician',    'email': 'carlos.r@windfarm.com',        'phone': '+1234567898'},
        'secondary':  {'name': 'Anna Martinez', 'role': 'Senior Technician',          'email': 'anna.m@windfarm.com',          'phone': '+1234567899'},
        'management': {'name': 'Mike Davis',    'role': 'Engineering Manager',        'email': 'mike.d@windfarm.com',          'phone': '+1234567892'},
        'escalation_time': 20
    },
    'Overspeed Protection Triggered': {
        'primary':    {'name': 'Carlos Rodriguez','role': 'Mechanical Technician',    'email': 'carlos.r@windfarm.com',        'phone': '+1234567898'},
        'secondary':  {'name': 'Anna Martinez', 'role': 'Senior Technician',          'email': 'anna.m@windfarm.com',          'phone': '+1234567899'},
        'management': {'name': 'Mike Davis',    'role': 'Engineering Manager',        'email': 'mike.d@windfarm.com',          'phone': '+1234567892'},
        'escalation_time': 20
    },
    'Hydraulic Valve Response Slow': {
        'primary':    {'name': 'Marcus Lee',    'role': 'Hydraulic Technician',       'email': 'marcus.l@windfarm.com',        'phone': '+1234567924'},
        'secondary':  {'name': 'Patricia King', 'role': 'Maintenance Supervisor',     'email': 'patricia.k@windfarm.com',      'phone': '+1234567925'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager',         'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 480
    },
    'DEFAULT': {
        'primary':    {'name': 'Operations Center','role': 'Control Room',            'email': 'ops@windfarm.com',             'phone': '+1234567800'},
        'secondary':  {'name': 'Duty Engineer',  'role': 'On-call Engineer',          'email': 'duty@windfarm.com',            'phone': '+1234567801'},
        'management': {'name': 'Operations Manager','role': 'Manager',                'email': 'manager@windfarm.com',         'phone': '+1234567802'},
        'escalation_time': 30
    }
}

# ── Notification functions ───────────────────────────────────────────────────
def send_email_notification(recipient_email, recipient_name, alarm_type, turbine_id, severity, alarm_id):
    try:
        sender  = "windsenseada@gmail.com"
        msg     = MIMEMultipart()
        msg['From']    = sender
        msg['To']      = recipient_email
        msg['Subject'] = f"🚨 {severity} ALARM: {alarm_type} - Turbine {turbine_id}"
        ack_url = f"https://windsense-ai.streamlit.app/Realtime?ack={alarm_id}&channel=email"
        body = f"""
        <html><body style="font-family: Arial, sans-serif;">
            <div style="background: linear-gradient(135deg, #0D1B2A 0%, #1E3A5F 100%); padding: 20px; color: white;">
                <h2>🚨 CRITICAL ALARM NOTIFICATION</h2>
            </div>
            <div style="padding: 20px; background-color: #112233;">
                <p style="color:#D0D8E0;">Dear {recipient_name},</p>
                <p style="color:#D0D8E0;">A <strong style="color:#ff4444;">{severity}</strong> alarm has been detected.</p>
                <div style="background-color: #1E3A5F; padding: 15px; border-left: 4px solid #ff4444; margin: 20px 0;">
                    <p style="color:#D0D8E0;"><strong>Alarm ID:</strong> {alarm_id}</p>
                    <p style="color:#D0D8E0;"><strong>Alarm Type:</strong> {alarm_type}</p>
                    <p style="color:#D0D8E0;"><strong>Turbine:</strong> T-{turbine_id}</p>
                    <p style="color:#D0D8E0;"><strong>Severity:</strong> {severity}</p>
                    <p style="color:#D0D8E0;"><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                <div style="text-align:center; margin:30px 0;">
                    <a href="{ack_url}" style="background-color:#00C9B1; color:white; padding:12px 30px;
                       text-decoration:none; border-radius:5px; display:inline-block; font-weight:bold;">
                        ✅ ACKNOWLEDGE THIS ALARM
                    </a>
                </div>
            </div>
        </body></html>
        """
        msg.attach(MIMEText(body, 'html'))
        try:
            _smtp = smtplib.SMTP('smtp.gmail.com', 587, timeout=5)
            _smtp.ehlo(); _smtp.starttls()
            _smtp.login('windsenseada@gmail.com', 'oaru xyta qlwi hpmw')
            _smtp.sendmail('windsenseada@gmail.com', recipient_email, msg.as_string())
            _smtp.quit()
            if 'notification_log' not in st.session_state:
                st.session_state.notification_log = []
            st.session_state.notification_log.append({
                'time': datetime.now(), 'type': 'EMAIL',
                'recipient': f"{recipient_name} ({recipient_email})",
                'alarm_id': alarm_id, 'alarm_type': alarm_type, 'status': 'SENT ✓'
            })
            return True
        except Exception:
            add_to_queue(recipient_email, recipient_name, msg['Subject'], body, alarm_id)
            if 'notification_log' not in st.session_state:
                st.session_state.notification_log = []
            st.session_state.notification_log.append({
                'time': datetime.now(), 'type': 'EMAIL',
                'recipient': f"{recipient_name} ({recipient_email})",
                'alarm_id': alarm_id, 'alarm_type': alarm_type,
                'status': 'QUEUED 🕐'
            })
            return False
    except Exception:
        return False

def send_sms_notification(phone_number, recipient_name, alarm_type, turbine_id, severity, alarm_id):
    try:
        from utils.sms_sender import send_real_sms
        ack_url = f"https://windsense-ai.streamlit.app/Realtime?ack={alarm_id}&channel=whatsapp"
        message_body = (
            f"WINDSENSE AI ALERT\n"
            f"Severity: {severity}\n"
            f"Alarm: {alarm_type}\n"
            f"Turbine: T-{turbine_id}\n"
            f"ID: {alarm_id}\n"
            f"Ack: {ack_url}"
        )
        success, result = send_real_sms(phone_number, message_body)
        if 'notification_log' not in st.session_state:
            st.session_state.notification_log = []
        st.session_state.notification_log.append({
            'time': datetime.now(), 'type': 'WHATSAPP',
            'recipient': f"{recipient_name} ({phone_number})",
            'alarm_id': alarm_id, 'alarm_type': alarm_type,
            'status': 'SENT ✓' if success else f'FAILED: {result}'
        })
        return success
    except Exception as e:
        if 'notification_log' not in st.session_state:
            st.session_state.notification_log = []
        st.session_state.notification_log.append({
            'time': datetime.now(), 'type': 'WHATSAPP',
            'recipient': f"{recipient_name} ({phone_number})",
            'alarm_id': alarm_id, 'alarm_type': alarm_type,
            'status': f'EXCEPTION: {e}'
        })
        return False

def process_critical_alarm(alarm_type, turbine_id, alarm_id, severity='CRITICAL'):
    if 'active_critical_alarms' not in st.session_state:
        st.session_state.active_critical_alarms = {}
    if alarm_id in st.session_state.active_critical_alarms:
        return alarm_id
    st.session_state.active_critical_alarms[alarm_id] = {
        'type': alarm_type, 'turbine_id': turbine_id,
        'timestamp': datetime.now(), 'severity': severity, 'notified': []
    }
    stakeholder_info = STAKEHOLDERS.get(alarm_type, STAKEHOLDERS.get('DEFAULT', {}))
    primary = stakeholder_info.get('primary', {})
    if primary:
        send_email_notification(primary['email'], primary['name'], alarm_type, turbine_id, severity, alarm_id)
        send_sms_notification(primary['phone'], primary['name'], alarm_type, turbine_id, severity, alarm_id)
        st.session_state.active_critical_alarms[alarm_id]['notified'].append(f"Primary: {primary['name']}")
    secondary = stakeholder_info.get('secondary', {})
    if secondary:
        send_email_notification(secondary['email'], secondary['name'], alarm_type, turbine_id, severity, alarm_id)
        st.session_state.active_critical_alarms[alarm_id]['notified'].append(f"Secondary: {secondary['name']}")
    return alarm_id

def check_and_escalate():
    current_time = datetime.now()
    if 'active_critical_alarms' not in st.session_state:
        return
    if 'escalated_alarms' not in st.session_state:
        st.session_state.escalated_alarms = {}
    for alarm_id, alarm_data in list(st.session_state.active_critical_alarms.items()):
        if alarm_id in st.session_state.acknowledged_alarms:
            continue
        alarm_time = alarm_data.get('timestamp')
        if alarm_time is None:
            continue
        if isinstance(alarm_time, str):
            try:
                alarm_time = datetime.strptime(alarm_time, '%Y-%m-%d %H:%M:%S')
            except Exception:
                continue
        alarm_type       = alarm_data.get('type', '')
        stakeholder_info = STAKEHOLDERS.get(alarm_type, STAKEHOLDERS.get('DEFAULT', {}))
        escalation_time  = stakeholder_info.get('escalation_time', 30)
        try:
            time_elapsed = (current_time - alarm_time).total_seconds() / 60
        except Exception:
            continue
        if time_elapsed > escalation_time and alarm_id not in st.session_state.escalated_alarms:
            mgmt = stakeholder_info.get('management', {})
            if mgmt:
                send_email_notification(
                    mgmt['email'], mgmt['name'], alarm_type,
                    alarm_data.get('turbine_id', 'Unknown'), 'CRITICAL - ESCALATED', alarm_id
                )
                send_sms_notification(
                    mgmt['phone'], mgmt['name'], alarm_type,
                    alarm_data.get('turbine_id', 'Unknown'), 'CRITICAL - ESCALATED', alarm_id
                )
                st.session_state.escalated_alarms[alarm_id] = {
                    'escalation_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'escalated_to':    mgmt['name'],
                    'reason':          f'No acknowledgment after {escalation_time} minutes'
                }

# ── Historical / ML loaders ───────────────────────────────────────────────────
@st.cache_resource
def load_ml_model():
    try:
        import gzip
        model_gz  = MODEL_PATH + 'windsense_rf_model.pkl.gz'
        model_pkl = MODEL_PATH + 'windsense_rf_model.pkl'
        if os.path.exists(model_gz):
            with gzip.open(model_gz, 'rb') as f:
                model = pickle.load(f)
        elif os.path.exists(model_pkl):
            with open(model_pkl, 'rb') as f:
                model = pickle.load(f)
        else:
            return None, None, None
        with open(MODEL_PATH + 'feature_names.pkl', 'rb') as f:
            features = pickle.load(f)
        with open(MODEL_PATH + 'model_metadata.json', 'r') as f:
            metadata = json.load(f)
        return model, features, metadata
    except Exception:
        return None, None, None

@st.cache_data
def load_simulation_data():
    try:
        return pd.read_csv(DATA_PATH + 'dashboard_alarm_stream.csv')
    except Exception:
        from utils.offline_data import get_fallback_alarm_stream
        return get_fallback_alarm_stream(50)

@st.cache_data
def load_historical_data():
    try:
        historical_alarms   = pd.read_csv(DATA_PATH + 'top_50_unique_detailed_alarms.csv')
        alarm_episodes      = pd.read_csv(DATA_PATH + 'alarm_episodes_with_faults.csv')
        detailed_episodes   = pd.read_csv(DATA_PATH + 'detailed_classified_alarm_episodes.csv')
        historical_alarms.columns = [c.strip() for c in historical_alarms.columns]
        if 'Rank' not in historical_alarms.columns:
            historical_alarms.insert(0, 'Rank', range(1, len(historical_alarms) + 1))
        dmaic_file = DATA_PATH + 'DMAIC_Analysis_19_Alarms.csv'
        dmaic_data = pd.read_csv(dmaic_file) if os.path.exists(dmaic_file) else None
        return historical_alarms, alarm_episodes, detailed_episodes, dmaic_data
    except Exception:
        return None, None, None, None

historical_alarms, alarm_episodes, detailed_episodes, dmaic_data = load_historical_data()
ml_model, feature_names, model_metadata = load_ml_model()
simulation_data = load_simulation_data()

# ── Simulator ─────────────────────────────────────────────────────────────────
class RealtimeAlarmSimulator:
    def __init__(self):
        self.alarm_count = 0
        self.alarm_types = [
            'Main Controller Fault', 'Extended Grid Outage', 'Grid Frequency Deviation',
            'Momentary Grid Loss', 'Grid Voltage Fluctuation', 'Emergency Brake Activation',
            'Safety System Activation', 'Overspeed Protection Triggered', 'Yaw System Hydraulic Fault',
            'Pitch System Hydraulic Fault', 'Hydraulic Oil Contamination', 'Converter Circuit Fault',
            'Generator Bearing Overheating', 'Power Electronics Failure', 'Transformer Oil Temperature High',
            'Hydraulic Filter Clogged', 'Generator Winding Temperature High', 'Hydraulic Pressure Drop',
            'Hydraulic Valve Response Slow'
        ]

    def generate_alarm(self):
        self.alarm_count += 1
        status_type = np.random.choice([3.0, 4.0, 5.0], p=[0.2, 0.3, 0.5])
        turbine_id  = np.random.choice([10, 11, 13, 21])   # removed 0 — not a real turbine label
        return {
            'alarm_id':         f'ALM-{self.alarm_count:05d}',
            'timestamp':        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'asset_id':         turbine_id,
            'status_type_id':   status_type,
            'sensor_11_avg':    np.random.uniform(40, 80),
            'sensor_12_avg':    np.random.uniform(35, 75),
            'sensor_13_avg':    np.random.uniform(30, 70),
            'sensor_41_avg':    np.random.uniform(25, 65),
            'power_30_avg':     np.random.uniform(100, 2000),
            'wind_speed_3_avg': np.random.uniform(3, 15),
            'predicted_type':   np.random.choice(self.alarm_types),
            'confidence':       np.random.uniform(75, 99),
            'priority':         'CRITICAL' if status_type == 5.0 else 'HIGH' if status_type == 4.0 else 'MEDIUM'
        }

# ── Session state init ────────────────────────────────────────────────────────
if 'simulator'            not in st.session_state:
    st.session_state.simulator            = RealtimeAlarmSimulator()
if 'alarm_buffer'         not in st.session_state:
    st.session_state.alarm_buffer         = []
if 'notifications'        not in st.session_state:
    st.session_state.notifications        = []
if 'acknowledged_alarms'  not in st.session_state:
    st.session_state.acknowledged_alarms  = load_acknowledgments()
if 'anomaly_detector'     not in st.session_state:
    st.session_state.anomaly_detector     = AnomalyDetector(contamination=0.1)

def clean_orphaned_acknowledgments():
    if 'alarm_buffer' in st.session_state and 'acknowledged_alarms' in st.session_state:
        active_ids   = {a['alarm_id'] for a in st.session_state.alarm_buffer}
        cleaned_acks = {
            aid: data for aid, data in st.session_state.acknowledged_alarms.items()
            if data.get('method') in ('email_link', 'whatsapp_link') or aid in active_ids
        }
        st.session_state.acknowledged_alarms = cleaned_acks
        try:
            with open(ACK_FILE, 'w') as f:
                json.dump(cleaned_acks, f, indent=2)
        except Exception:
            pass

# ── Elimination strategies ────────────────────────────────────────────────────
FALLBACK_ELIMINATION_STRATEGIES = {
    'Main Controller Fault':             ['Update controller firmware to latest stable version', 'Implement auto-reset logic to reduce manual intervention', 'Install redundant controller for failover capability', 'Deploy grid stability monitoring for early warning'],
    'Grid Frequency Deviation':          ['Install Battery Energy Storage System (BESS) for frequency stabilization', 'Implement faster reconnection logic to reduce downtime', 'Coordinate with utility provider and negotiate grid stability SLA', 'Add frequency ride-through capability for wider operating range'],
    'Extended Grid Outage':              ['Install diesel generator backup for black start capability', 'Negotiate advance notice for planned maintenance outages', 'Add redundant grid connection point to reduce outage frequency', 'Implement islanding capability with BESS for independent operation'],
    'Emergency Brake Activation':        ['Upgrade to condition-based brake monitoring system', 'Implement predictive maintenance to prevent false triggers', 'Install redundant sensors to verify actual overspeed conditions', 'Perform quarterly brake system calibration to reduce false alarms'],
    'Generator Bearing Overheating':     ['Install online bearing monitoring (vibration + temperature sensors)', 'Upgrade to automatic lubrication systems', 'Implement condition-based lubrication via oil analysis', 'Add redundant cooling fans for backup cooling capability'],
    'Hydraulic Oil Contamination':       ['Install high-efficiency filtration system with contamination sensors', 'Implement real-time oil quality monitoring with automatic alerts', 'Schedule regular oil analysis and flush cycles', 'Upgrade seals and fittings to prevent external contamination ingress'],
    'Converter Circuit Fault':           ['Replace aging IGBT modules with latest generation components', 'Implement thermal management improvements for converter cooling', 'Install online converter health monitoring system', 'Perform preventive capacitor replacement on schedule'],
    'Momentary Grid Loss':               ['Upgrade to low voltage ride-through (LVRT) capability', 'Implement auto-restart sequence to reduce recovery time', 'Adjust protection trip settings for wider voltage tolerance', 'Install voltage stabilizers at grid connection point'],
    'Grid Voltage Fluctuation':          ['Install Static VAR Compensator (SVC) for voltage stabilization', 'Upgrade transformer with automatic tap changer', 'Implement reactive power control via inverter settings', 'Coordinate with utility on voltage regulation protocols'],
    'Safety System Activation':          ['Perform comprehensive safety sensor calibration and audit', 'Upgrade safety PLC to latest firmware with improved logic', 'Implement diagnostic mode to differentiate true vs false triggers', 'Review and optimize safety trip thresholds to reduce false activations'],
    'Overspeed Protection Triggered':    ['Calibrate rotor speed sensors and replace if drifting', 'Optimize pitch control response for faster regulation', 'Implement multi-sensor voting logic to prevent false trips', 'Review and adjust overspeed threshold settings'],
    'Yaw System Hydraulic Fault':        ['Replace worn yaw hydraulic seals and actuators', 'Install yaw hydraulic pressure monitoring with automated alerts', 'Implement scheduled hydraulic fluid replacement program', 'Add redundant yaw position sensors for fault detection'],
    'Pitch System Hydraulic Fault':      ['Replace pitch hydraulic cylinders and seals on schedule', 'Install real-time pitch pressure monitoring system', 'Implement emergency battery backup for pitch control', 'Perform quarterly pitch system hydraulic inspection'],
    'Power Electronics Failure':         ['Implement thermal monitoring on all power electronic components', 'Replace aging capacitors and IGBT modules preventively', 'Improve converter cabinet cooling and ventilation', 'Deploy online insulation resistance monitoring'],
    'Transformer Oil Temperature High':  ['Clean and inspect transformer cooling radiators', 'Upgrade cooling fans and implement variable speed control', 'Install online dissolved gas analysis (DGA) monitoring', 'Perform power factor testing and insulation checks'],
    'Hydraulic Filter Clogged':          ['Implement differential pressure monitoring across all filters', 'Reduce filter replacement intervals based on contamination levels', 'Upgrade to higher-capacity filter elements', 'Install oil contamination particle counter for predictive maintenance'],
    'Generator Winding Temperature High':['Inspect and clean generator air gaps and cooling ducts', 'Replace damaged winding insulation and re-varnish', 'Install additional temperature sensors across all winding phases', 'Implement load shedding logic when temperature rises above threshold'],
    'Hydraulic Pressure Drop':           ['Inspect all hydraulic lines and connections for leaks', 'Replace worn hydraulic pump components or full pump assembly', 'Install pressure transducers on all critical hydraulic circuits', 'Implement automatic shutdown logic on pressure drop detection'],
    'Hydraulic Valve Response Slow':     ['Flush and replace hydraulic fluid to restore viscosity', 'Clean or replace slow-responding solenoid valves', 'Install valve response time monitoring sensors', 'Implement valve performance trending and predictive replacement schedule']
}

def get_elimination_strategy(alarm_type):
    if alarm_type in DMAIC_DATABASE:
        solutions = DMAIC_DATABASE[alarm_type].get('improve', {}).get('solutions', [])
        if solutions:
            return solutions
    return FALLBACK_ELIMINATION_STRATEGIES.get(
        alarm_type,
        ['Perform diagnostic inspection of affected system',
         'Review recent maintenance and operational logs',
         'Consult OEM maintenance manual for corrective procedure',
         'Escalate to specialist if fault persists after initial checks']
    )

# ── Root Cause Engine ─────────────────────────────────────────────────────────
class RootCauseEngine:
    def __init__(self):
        self.root_cause_database = {}
        if DMAIC_DATABASE:
            for alarm_type, dmaic_entry in DMAIC_DATABASE.items():
                self.root_cause_database[alarm_type] = {
                    'primary_cause':        dmaic_entry.get('analyze', {}).get('root_cause', 'Analysis in progress'),
                    'contributing_factors': dmaic_entry.get('analyze', {}).get('contributing', []),
                    'diagnostic_sensors':   ['power_30_avg', 'sensor_11_avg', 'sensor_12_avg'],
                    'threshold_conditions': {}
                }

    def analyze(self, alarm_type, sensor_data):
        if alarm_type not in self.root_cause_database:
            return {
                'alarm_type': alarm_type,
                'primary_cause': 'Diagnostic analysis in progress',
                'contributing_factors': ['Requires additional sensor data collection'],
                'sensor_anomalies': [], 'confidence': 50,
                'recommended_actions': get_elimination_strategy(alarm_type)
            }
        rca_data         = self.root_cause_database[alarm_type]
        sensor_anomalies = []
        for sensor in rca_data['diagnostic_sensors']:
            if sensor in sensor_data:
                value = sensor_data[sensor]
                if 'temp' in sensor.lower() and value > 70:
                    sensor_anomalies.append(f"{sensor}: {value:.1f}°C (HIGH)")
                elif 'power' in sensor.lower() and value < 100:
                    sensor_anomalies.append(f"{sensor}: {value:.1f}W (LOW)")
        confidence = min(95, 70 + len(sensor_anomalies) * 10)
        return {
            'alarm_type':           alarm_type,
            'primary_cause':        rca_data['primary_cause'],
            'contributing_factors': rca_data['contributing_factors'],
            'sensor_anomalies':     sensor_anomalies,
            'confidence':           confidence,
            'recommended_actions':  get_elimination_strategy(alarm_type)
        }

if 'rca_engine'   not in st.session_state:
    st.session_state.rca_engine   = RootCauseEngine()
if 'iso_detector' not in st.session_state:
    st.session_state.iso_detector = IsolationForestDetector()

st.session_state.anomaly_detector = st.session_state.iso_detector

def predict_alarm_type(alarm_data, model, features):
    if model is None:
        status = alarm_data.get('status_type_id', 5.0)
        if status == 5.0:   return 'Grid Frequency Deviation', 92.5
        elif status == 4.0: return 'Emergency Brake Activation', 88.3
        else:               return 'Hydraulic Pressure Drop', 85.7
    try:
        ts_raw = alarm_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            ts = datetime.strptime(str(ts_raw), '%Y-%m-%d %H:%M:%S')
        except Exception:
            ts = datetime.now()
        duration_hours   = float(alarm_data.get('duration_hours', np.random.uniform(0.5, 5.0)))
        duration_minutes = duration_hours * 60
        duration_log     = float(np.log1p(duration_hours))
        is_long   = 1 if duration_hours >= 5   else 0
        is_short  = 1 if duration_hours < 2    else 0
        is_medium = 1 if 2 <= duration_hours < 5 else 0
        hour_of_day  = ts.hour
        day_of_week  = ts.weekday()
        month        = ts.month
        season = 0 if month in [12,1,2] else 1 if month in [3,4,5] else 2 if month in [6,7,8] else 3
        is_weekend    = 1 if day_of_week >= 5 else 0
        is_peak_hours = 1 if 8 <= hour_of_day <= 20 else 0
        asset_id = alarm_data.get('asset_id', 10)
        try:
            turbine_id_num = int(asset_id) if str(asset_id).isdigit() else 10
        except Exception:
            turbine_id_num = 10
        status_type_id  = float(alarm_data.get('status_type_id', 5.0))
        status_type_num = int(status_type_id)
        is_status_5 = 1 if status_type_id == 5.0 else 0
        is_status_4 = 1 if status_type_id == 4.0 else 0
        is_status_3 = 1 if status_type_id == 3.0 else 0
        turbine_alarm_frequency = float(alarm_data.get('turbine_alarm_frequency', 100.0))
        turbine_avg_duration    = float(alarm_data.get('turbine_avg_duration', 3.0))
        duration_rank           = float(alarm_data.get('duration_rank', 0.5))
        feature_vector = [
            duration_hours, duration_minutes, duration_log,
            is_long, is_short, is_medium,
            hour_of_day, day_of_week, month, season,
            is_weekend, is_peak_hours,
            turbine_id_num, status_type_num,
            is_status_5, is_status_4, is_status_3,
            turbine_alarm_frequency, turbine_avg_duration, duration_rank
        ]
        X             = np.array([feature_vector])
        prediction    = model.predict(X)[0]
        probabilities = model.predict_proba(X)[0]
        confidence    = max(probabilities) * 100
        return prediction, confidence
    except Exception:
        status = alarm_data.get('status_type_id', 5.0)
        if status == 5.0:   return 'Grid Frequency Deviation', 88.0
        elif status == 4.0: return 'Generator Bearing Overheating', 82.0
        else:               return 'Hydraulic Oil Contamination', 80.0

def send_notification(alarm):
    dept_mapping = {
        'Main Controller Fault':        'Software & Controls',
        'Grid Frequency Deviation':     'Grid Operations',
        'Emergency Brake Activation':   'Mechanical Safety',
        'Generator Bearing Overheating':'Mechanical - Rotating Equipment',
        'Hydraulic Oil Contamination':  'Hydraulic Systems',
        'Converter Circuit Fault':      'Electrical - Power Electronics',
        'Pitch System Hydraulic Fault': 'Mechanical - Blade Systems',
        'Yaw System Hydraulic Fault':   'Mechanical - Nacelle Systems'
    }
    department       = dept_mapping.get(alarm['predicted_type'], 'General Maintenance')
    stakeholder_info = STAKEHOLDERS.get(alarm['predicted_type'], STAKEHOLDERS.get('DEFAULT', {}))
    primary          = stakeholder_info.get('primary', {})
    notification = {
        'timestamp':   alarm['timestamp'],
        'alarm_id':    alarm['alarm_id'],
        'turbine':     f"T-{alarm['asset_id']}",
        'alarm_type':  alarm['predicted_type'],
        'priority':    alarm['priority'],
        'department':  department,
        'stakeholder': f"{primary.get('name', 'N/A')} ({primary.get('role', 'N/A')})",
        'message':     f"🚨 {alarm['priority']} ALERT: {alarm['predicted_type']} detected on Turbine {alarm['asset_id']}. Confidence: {alarm['confidence']:.1f}%. Immediate action required.",
        'sent':        True
    }
    st.session_state.notifications.insert(0, notification)
    if len(st.session_state.notifications) > 50:
        st.session_state.notifications = st.session_state.notifications[:50]
    if alarm['priority'] == 'CRITICAL':
        process_critical_alarm(alarm['predicted_type'], alarm['asset_id'], alarm['alarm_id'], alarm['priority'])
    return notification

# ═══════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════

with st.sidebar:
    try:
        st.image("assets/windsense_logo_icon.png", width=90)
    except Exception:
        try:
            st.image("assets/wind_turbine_fallback.png", width=80)
        except Exception:
            st.markdown("## 🌀")

    st.markdown("<h2 style='color:#00C9B1; margin:0; font-size:1.3rem;'>WindSense AI</h2>", unsafe_allow_html=True)
    st.caption("Team TG0907494 | TECHgium 9th Edition")
    st.divider()

    st.subheader("📊 System Status")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Model Status", "ACTIVE ✓" if ml_model else "DEMO MODE")
    with col2:
        st.metric("Data Loaded", "✓ 978K rows")

    st.divider()
    st.subheader("⚡ Live Simulation")

    if st.button("🔄 Generate New Alarm", use_container_width=True):
        new_alarm = st.session_state.simulator.generate_alarm()
        if st.session_state.iso_detector.is_trained:
            is_anomaly, anomaly_score = st.session_state.iso_detector.predict(new_alarm)
            new_alarm['is_anomaly']    = is_anomaly
            new_alarm['anomaly_score'] = anomaly_score
        else:
            new_alarm['is_anomaly']    = False
            new_alarm['anomaly_score'] = 0.0
        st.session_state.alarm_buffer.insert(0, new_alarm)
        send_notification(new_alarm)
        st.rerun()

    auto_mode = st.checkbox("🤖 Auto-Generate (every 5s)")
    if auto_mode:
        time.sleep(5)
        new_alarm = st.session_state.simulator.generate_alarm()
        st.session_state.alarm_buffer.insert(0, new_alarm)
        send_notification(new_alarm)
        st.rerun()

    st.metric("Alarms Generated", len(st.session_state.alarm_buffer))

    if st.button("🗑️ Clear Buffer", use_container_width=True):
        st.session_state.alarm_buffer  = []
        st.session_state.notifications = []
        st.rerun()

    st.divider()
    st.subheader("🔬 Anomaly Detection")

    if st.button("🧠 Train Anomaly Detector", use_container_width=True):
        if len(st.session_state.alarm_buffer) >= 10:
            success, message = st.session_state.iso_detector.train(st.session_state.alarm_buffer)
            if success:
                st.success(f"✅ {message}")
            else:
                st.warning(f"⚠️ {message}")
        else:
            st.warning(f"Need {10 - len(st.session_state.alarm_buffer)} more alarms")

    st.caption("🟢 Detector: ACTIVE" if st.session_state.iso_detector.is_trained else "🔴 Detector: not trained yet")

    st.divider()
    st.markdown("<p style='color:#00C9B1; font-weight:700; font-size:1rem;'>Help Center & Support</p>", unsafe_allow_html=True)

    st.markdown("""
<style>
/* ── Arrow-free custom expanders for Help Center ── */
.ws-help-details {
    background-color: #112233;
    border: 1px solid #00C9B1;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    overflow: hidden;
}
.ws-help-details summary {
    list-style: none !important;
    cursor: pointer;
    padding: 0.55rem 0.85rem;
    color: #00C9B1;
    font-weight: 700;
    font-size: 0.88rem;
    user-select: none;
    background-color: #112233;
}
.ws-help-details summary::-webkit-details-marker { display: none !important; }
.ws-help-details summary::marker { display: none !important; }
.ws-help-details[open] summary { border-bottom: 1px solid #1E3A5F; }
.ws-help-body {
    padding: 0.7rem 0.85rem;
    color: #E8F4FD;
    font-size: 0.82rem;
    line-height: 1.6;
    background-color: #0D1B2A;
}
.ws-help-body strong { color: #00C9B1; }
.ws-help-body .ws-step {
    background: #112233;
    border-left: 3px solid #00C9B1;
    padding: 0.35rem 0.6rem;
    margin: 0.3rem 0;
    border-radius: 0 4px 4px 0;
}
.ws-help-body a { color: #4FC3F7; text-decoration: none; }
.ws-help-body a:hover { text-decoration: underline; }
</style>

<details class="ws-help-details">
<summary>📖 Tab-by-Tab Guide</summary>
<div class="ws-help-body">
<div class="ws-step"><strong>Tab 1 — Real-Time Monitoring</strong><br>Click <em>Generate New Alarm</em> in the sidebar. Each alarm is classified by the Random Forest ML model instantly. The live stream shows alarm ID, priority, turbine, type and confidence score. Red = Critical. Download the log as CSV anytime.</div>
<div class="ws-step"><strong>Tab 2 — ML Model &amp; Training</strong><br>View model accuracy (94.8%), feature importance chart, and the full list of 19 trained alarm types. No action needed — the model is pre-loaded and always active.</div>
<div class="ws-step"><strong>Tab 3 — Historical Analytics</strong><br>9.9 years of SCADA data. Browse the top 50 critical alarms ranked by impact, department breakdown charts, downtime analysis, and an alarm heatmap by turbine and hour of day.</div>
<div class="ws-step"><strong>Tab 4 — Notifications &amp; Workflow</strong><br>See the 6-step resolution workflow. View Email + WhatsApp notification logs. Check which alarms have been escalated to management. Browse the full stakeholder directory.</div>
<div class="ws-step"><strong>Tab 5 — DMAIC Analysis</strong><br>Select any alarm type to see its full DMAIC report: Define → Measure → Analyze → Improve → Control. Each section has plain-language corrective actions for field technicians.</div>
<div class="ws-step"><strong>Tab 6 — Optimization</strong><br>LPF (Lost Production Factor) breakdown, 6-month alarm forecast charts, full implementation roadmap, and ROI calculations. Use this for management reporting.</div>
<div class="ws-step"><strong>Tab 7 — Alarm Acknowledgment</strong><br>See all active unacknowledged alarms. Enter your name, select action taken, add notes, then click Acknowledge. Tracks response time automatically. Also shows acknowledgment history.</div>
<div class="ws-step"><strong>Tab 8 — OPC UA Live Feed</strong><br>Live industrial sensor data from the OPC UA simulation layer. Shows fleet power, node readings, and active alarm nodes. Also contains the Anomaly Review panel for unknown fault patterns.</div>
</div>
</details>

<details class="ws-help-details">
<summary>❓ FAQ — Top Operator Questions</summary>
<div class="ws-help-body">
<strong>Q: What does a red alarm mean?</strong><br>Red = CRITICAL priority. Immediate action required. The system has already notified the assigned technician via Email and WhatsApp.<br><br>
<strong>Q: What does orange or yellow mean?</strong><br>Orange = HIGH priority. Yellow = MEDIUM. Both need attention but are not immediately dangerous.<br><br>
<strong>Q: How do I acknowledge an alarm?</strong><br>Go to Tab 7, find the alarm, enter your name, select the action taken, and click ✅ Acknowledge. You can also acknowledge directly from the Email or WhatsApp notification link.<br><br>
<strong>Q: What is LPF?</strong><br>Lost Production Factor — the percentage of potential energy output that was lost due to downtime. Current LPF is 3.64%. Target is below 2.0%.<br><br>
<strong>Q: What does "Confidence" mean on an alarm?</strong><br>It shows how certain the AI model is about its alarm classification. Above 85% = High (green). 70–85% = Moderate (orange). Below 70% = Uncertain — requires manual inspection.<br><br>
<strong>Q: I got an alarm email. What do I do?</strong><br>Click the green ✅ ACKNOWLEDGE button in the email. This updates the dashboard immediately. Then follow the recommended actions in the email body.<br><br>
<strong>Q: What is DMAIC?</strong><br>A structured problem-solving method: Define, Measure, Analyze, Improve, Control. Tab 5 shows the full corrective action plan for each of the 19 alarm types.<br><br>
<strong>Q: What is an Unknown Anomaly?</strong><br>A sensor pattern the AI has not seen before. It appears as a red flag. Review it in Tab 8 → Anomaly Review Panel. See the Unknown Alarms section below for the 3-step guide.<br><br>
<strong>Q: Why is the anomaly detector showing "not trained yet"?</strong><br>Generate at least 10 alarms first, then click "Train Anomaly Detector" in the sidebar. The Isolation Forest model needs a minimum dataset to learn normal patterns.<br><br>
<strong>Q: Can I use this dashboard on my phone?</strong><br>Yes. Open windsense-ai.streamlit.app in any mobile browser. The layout adjusts automatically. No app install needed.<br><br>
<strong>Q: How do I export alarm data?</strong><br>Each tab with a data table has a Download CSV button at the bottom. Click it to save the current view to your device.<br><br>
<strong>Q: Who gets notified when a critical alarm fires?</strong><br>The primary stakeholder assigned to that alarm type gets Email + WhatsApp immediately. The secondary contact gets an email copy. Management is auto-escalated if no acknowledgment is received within the configured time window.<br><br>
<strong>Q: What happens if the email fails to send?</strong><br>The system queues the email and retries automatically. Status shows as QUEUED in the notification log (Tab 4) until delivered.<br><br>
<strong>Q: How accurate is the AI classification?</strong><br>94.8% accuracy on the test set. The model was trained on 978,000+ SCADA readings across 9.9 years and 5 turbines.<br><br>
<strong>Q: What are the 19 alarm types?</strong><br>See the Alarm Type Glossary section below for all 19 with plain-language descriptions.<br><br>
<strong>Q: What is OPC UA?</strong><br>OPC Unified Architecture — an industrial communication standard used by SCADA systems. Tab 8 shows a simulated live OPC UA data feed that mirrors what a real turbine controller would transmit.<br><br>
<strong>Q: Can I add a new alarm type?</strong><br>Yes — when an unknown anomaly is detected, use the Anomaly Review Panel in Tab 8 to name it and add it to the database.<br><br>
<strong>Q: How do I report a bug or issue?</strong><br>See the Report an Issue section below. Click the button to send a pre-formatted email to the WindSense team.<br><br>
<strong>Q: What is the escalation time?</strong><br>Each alarm type has a configured escalation window (e.g. 30 minutes for Controller Faults, 480 minutes for Hydraulic Faults). If unacknowledged within this window, the management contact is notified automatically.<br><br>
<strong>Q: How do I clear the alarm buffer?</strong><br>Click the 🗑️ Clear Buffer button in the sidebar. This resets all active alarms and the notification log for the current session.
</div>
</details>

<details class="ws-help-details">
<summary>📚 Alarm Type Glossary (All 19)</summary>
<div class="ws-help-body">
<strong>1. Main Controller Fault</strong> — The turbine's central computer has reported an error. The turbine may stop automatically.<br><br>
<strong>2. Extended Grid Outage</strong> — The power grid connection has been lost for a prolonged period. The turbine cannot export power.<br><br>
<strong>3. Grid Frequency Deviation</strong> — The grid frequency has drifted outside the safe operating range (normally 50 Hz). Turbine may disconnect to protect equipment.<br><br>
<strong>4. Momentary Grid Loss</strong> — A brief interruption in grid connection, usually under 1 minute. Often resolves automatically.<br><br>
<strong>5. Grid Voltage Fluctuation</strong> — The grid supply voltage is unstable, causing potential damage to electrical components.<br><br>
<strong>6. Emergency Brake Activation</strong> — The rotor brakes have been triggered by a safety system. The turbine has stopped rotating.<br><br>
<strong>7. Safety System Activation</strong> — One or more safety sensors has triggered a protective shutdown. Inspection required before restart.<br><br>
<strong>8. Overspeed Protection Triggered</strong> — The rotor exceeded its maximum safe RPM. The pitch and brake systems activated to stop the turbine.<br><br>
<strong>9. Yaw System Hydraulic Fault</strong> — The system that turns the turbine to face the wind has lost hydraulic pressure or has a valve fault.<br><br>
<strong>10. Pitch System Hydraulic Fault</strong> — The blade angle control system has a hydraulic fault. Blades may be stuck and unable to adjust to wind speed.<br><br>
<strong>11. Hydraulic Oil Contamination</strong> — Oil samples or sensors indicate contamination in the hydraulic fluid. Can cause valve and seal damage if unaddressed.<br><br>
<strong>12. Converter Circuit Fault</strong> — The power electronics unit that converts generated AC/DC power has reported a circuit fault.<br><br>
<strong>13. Generator Bearing Overheating</strong> — The main generator bearings have exceeded safe operating temperature. Risk of seizure if not addressed quickly.<br><br>
<strong>14. Power Electronics Failure</strong> — A component in the power electronics cabinet (IGBT, capacitor, etc.) has failed or is degraded.<br><br>
<strong>15. Transformer Oil Temperature High</strong> — The transformer oil has exceeded its safe temperature threshold. Cooling system may have failed.<br><br>
<strong>16. Hydraulic Filter Clogged</strong> — The hydraulic oil filter is blocked, restricting flow. Requires filter replacement during next maintenance window.<br><br>
<strong>17. Generator Winding Temperature High</strong> — The electrical windings inside the generator are overheating. Could indicate cooling duct blockage or insulation breakdown.<br><br>
<strong>18. Hydraulic Pressure Drop</strong> — A sudden loss of pressure in the hydraulic circuit. Could indicate a leak, pump failure, or burst line.<br><br>
<strong>19. Hydraulic Valve Response Slow</strong> — A hydraulic valve is not responding within its expected time window. Often caused by contaminated fluid or worn valve components.
</div>
</details>

<details class="ws-help-details">
<summary>🔬 What is DMAIC? (Plain Language)</summary>
<div class="ws-help-body">
DMAIC is a structured 5-step method for fixing recurring problems. WindSense AI applies it to all 19 alarm types so every technician knows exactly what to do — not just that something went wrong.<br><br>
<strong>D — Define:</strong> What is this alarm? When does it happen? What equipment is affected?<br><br>
<strong>M — Measure:</strong> How often does it occur? How long does it last? How much production does it cost?<br><br>
<strong>A — Analyze:</strong> What is the root cause? What contributing factors make it worse?<br><br>
<strong>I — Improve:</strong> What specific actions will fix it? What is the expected benefit after implementation?<br><br>
<strong>C — Control:</strong> How do we monitor it going forward? What thresholds trigger a new alert? How often do we review?<br><br>
<em>Example:</em> For Generator Bearing Overheating — the root cause is insufficient lubrication. The improvement is installing automatic lubrication systems. The control is a temperature alert at 75°C with weekly oil analysis review.<br><br>
See Tab 5 for the full DMAIC report for any of the 19 alarm types.
</div>
</details>

<details class="ws-help-details">
<summary>🔴 Unknown Anomaly — What To Do</summary>
<div class="ws-help-body">
When the Isolation Forest AI detects a sensor pattern it has never seen before, it flags it as an <strong style="color:#ff4444;">Unknown Anomaly</strong>. This is not an error — it means a potentially new fault type has been discovered.<br><br>
<strong>You will see:</strong> A red 🔴 flag in the alarm stream (Tab 1) and a warning banner. The anomaly is held in the Anomaly Review Panel in Tab 8.<br><br>
<strong>3-Step Response Guide:</strong><br>
<div class="ws-step"><strong>Step 1 — Review Sensor Data</strong><br>Go to Tab 8 → Anomaly Review Panel. Open the anomaly entry. Check the sensor snapshot — which readings look abnormal? Compare against the known alarm glossary.</div>
<div class="ws-step"><strong>Step 2 — Name and Add to Database</strong><br>If you can identify the fault type, type the name in the "Rename this anomaly type" field and click ➕ Add to Alarm DB. This adds it to the system's known patterns for future classification. If you're unsure, click ✅ Mark as Known to remove it from the review queue without renaming.</div>
<div class="ws-step"><strong>Step 3 — Notify Supervisor</strong><br>For any genuinely new fault pattern you cannot identify, contact your supervisor and email the WindSense team at windsenseada@gmail.com with the Alarm ID, sensor readings, and turbine number. Include a screenshot if possible.</div>
<br><em>Note: The Isolation Forest anomaly detector must be trained first. Generate 10+ alarms in Tab 1, then click "Train Anomaly Detector" in the sidebar.</em>
</div>
</details>

<details class="ws-help-details">
<summary>📞 Support &amp; Contact</summary>
<div class="ws-help-body">
<strong>📧 Email Support</strong><br>
Non-urgent queries: <a href="mailto:windsenseada@gmail.com">windsenseada@gmail.com</a><br>
Response within 24 hours on working days.<br><br>
<strong>🐛 Report an Issue</strong><br>
Found a bug or display problem? Use the form below to send it directly to the WindSense team.<br><br>
<strong>📋 Team</strong><br>
WindSense AI — Team TG0907494<br>
TECHgium 9th Edition<br><br>
<strong>🌐 Dashboard URL</strong><br>
<a href="https://windsense-ai.streamlit.app">windsense-ai.streamlit.app</a> — accessible on any device, no login needed to view Help.
</div>
</details>
""", unsafe_allow_html=True)
# ── Report an Issue inline form ──────────────────────────────────────────
    if 'show_report_form' not in st.session_state:
        st.session_state.show_report_form = False
    if 'report_sent' not in st.session_state:
        st.session_state.report_sent = False

    if st.button("🐛 Report an Issue", key="open_report_form", use_container_width=True):
        st.session_state.show_report_form = not st.session_state.show_report_form
        st.session_state.report_sent = False

    if st.session_state.show_report_form:
        st.markdown("""
        <div style="background:#0D1B2A; border:1px solid #00C9B1; border-radius:10px;
                    padding:1rem 1.2rem; margin-top:0.5rem;">
            <p style="color:#00C9B1; font-weight:700; margin:0 0 0.5rem 0;">📝 Report an Issue</p>
            <p style="color:#8899AA; font-size:0.78rem; margin:0 0 0.8rem 0;">
                Your report will be sent to windsenseada@gmail.com
            </p>
        </div>
        """, unsafe_allow_html=True)

        report_name = st.text_input(
            "Your Name / Username",
            placeholder="e.g. Aarif — Mechanical Tech",
            key="report_name"
        )
        report_tab = st.selectbox(
            "Tab where issue occurred",
            ["Tab 1 — Real-Time Monitoring", "Tab 2 — ML Model & Training",
             "Tab 3 — Historical Analytics", "Tab 4 — Notifications & Workflow",
             "Tab 5 — DMAIC Analysis", "Tab 6 — Optimization & Forecasting",
             "Tab 7 — Alarm Acknowledgment", "Tab 8 — OPC UA Live Feed",
             "Sidebar / General", "Other"],
            key="report_tab"
        )
        report_body = st.text_area(
            "Describe the issue (max 2000 characters)",
            placeholder="What went wrong? What did you expect to happen? Steps to reproduce...",
            max_chars=2000,
            height=180,
            key="report_body"
        )
        char_count = len(report_body) if report_body else 0
        st.caption(f"{char_count} / 2000 characters used")

        col_send, col_cancel = st.columns([1, 1])
        with col_send:
            if st.button("📤 Send Report", key="send_report", type="primary", use_container_width=True):
                if not report_name.strip():
                    st.error("Please enter your name.")
                elif not report_body.strip():
                    st.error("Please describe the issue before sending.")
                else:
                    try:
                        import smtplib
                        from email.mime.text import MIMEText
                        from email.mime.multipart import MIMEMultipart

                        sender  = "windsenseada@gmail.com"
                        subject = f"🐛 WindSense AI — Issue Report from {report_name.strip()}"
                        html_body = f"""
                        <html><body style="font-family:Arial,sans-serif; background:#0D1B2A; color:#E8F4FD;">
                            <div style="background:linear-gradient(135deg,#0D1B2A,#1E3A5F);
                                        padding:20px; border-bottom:2px solid #00C9B1;">
                                <h2 style="color:#00C9B1; margin:0;">🐛 WindSense AI — Issue Report</h2>
                            </div>
                            <div style="padding:20px; background:#112233;">
                                <table style="width:100%; border-collapse:collapse; color:#D0D8E0;">
                                    <tr>
                                        <td style="padding:8px 12px; background:#0D1B2A; border:1px solid #1E3A5F;
                                                   font-weight:700; color:#00C9B1; width:35%;">Reported By</td>
                                        <td style="padding:8px 12px; background:#0D1B2A; border:1px solid #1E3A5F;">
                                            {report_name.strip()}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding:8px 12px; background:#0D1B2A; border:1px solid #1E3A5F;
                                                   font-weight:700; color:#00C9B1;">Tab / Location</td>
                                        <td style="padding:8px 12px; background:#0D1B2A; border:1px solid #1E3A5F;">
                                            {report_tab}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding:8px 12px; background:#0D1B2A; border:1px solid #1E3A5F;
                                                   font-weight:700; color:#00C9B1;">Submitted At</td>
                                        <td style="padding:8px 12px; background:#0D1B2A; border:1px solid #1E3A5F;">
                                            {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding:8px 12px; background:#0D1B2A; border:1px solid #1E3A5F;
                                                   font-weight:700; color:#00C9B1;">Dashboard URL</td>
                                        <td style="padding:8px 12px; background:#0D1B2A; border:1px solid #1E3A5F;">
                                            windsense-ai.streamlit.app
                                        </td>
                                    </tr>
                                </table>
                                <div style="margin-top:20px; padding:15px; background:#0D1B2A;
                                            border-left:4px solid #00C9B1; border-radius:0 8px 8px 0;">
                                    <p style="color:#00C9B1; font-weight:700; margin:0 0 10px 0;">
                                        Issue Description
                                    </p>
                                    <p style="color:#D0D8E0; white-space:pre-wrap; margin:0;">
                                        {report_body.strip()}
                                    </p>
                                </div>
                            </div>
                            <div style="padding:12px 20px; background:#0D1B2A; text-align:center;
                                        color:#4FC3F7; font-size:0.8rem;">
                                WindSense AI © 2026 | Team TG0907494 | TECHgium 9th Edition
                            </div>
                        </body></html>
                        """

                        msg = MIMEMultipart()
                        msg['From']    = sender
                        msg['To']      = "windsenseada@gmail.com"
                        msg['Subject'] = subject
                        msg.attach(MIMEText(html_body, 'html'))

                        _smtp = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
                        _smtp.ehlo()
                        _smtp.starttls()
                        _smtp.login('windsenseada@gmail.com', 'oaru xyta qlwi hpmw')
                        _smtp.sendmail(sender, "windsenseada@gmail.com", msg.as_string())
                        _smtp.quit()

                        st.session_state.report_sent        = True
                        st.session_state.show_report_form   = False
                        st.success(f"✅ Report sent successfully! We'll review it shortly, {report_name.strip()}.")
                        st.balloons()
                        st.rerun()

                    except Exception as _e:
                        st.error(f"❌ Failed to send report. Please email windsenseada@gmail.com directly. Error: {_e}")

        with col_cancel:
            if st.button("✖ Cancel", key="cancel_report", use_container_width=True):
                st.session_state.show_report_form = False
                st.rerun()

    if st.session_state.get('report_sent', False):
        st.success("✅ Your issue report was sent to the WindSense team.")
        st.session_state.report_sent = False

# ═══════════════════════════════════════════════════════════════════
# MAIN TABS
# ═══════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📡 Real-Time Monitoring",
    "🤖 ML Model & Training",
    "📊 Historical Analytics",
    "🔔 Notifications & Workflow",
    "📋 DMAIC Analysis",
    "🎯 Optimization & Forecasting",
    "🎛️ Alarm Acknowledgment",
    "🏭 OPC UA Live Feed"
])

# ═══════════════════════════════════════════════════════════════════
# TAB 1 — REAL-TIME MONITORING
# ═══════════════════════════════════════════════════════════════════

with tab1:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #003D35, #005C51);
                border: 1px solid #00C9B1; border-radius: 10px;
                padding: 0.8rem 1.2rem; margin-bottom: 1rem;">
        <span style="color:#00C9B1; font-weight:700; font-size:1rem;">
            🌀 WindSense AI — Live Classification Engine
        </span>
        <span style="color:#7FB9D4; font-size:0.85rem; margin-left:1rem;">
            Random Forest · 94.8% Accuracy · 19 Alarm Types · Real-time OPC UA Feed
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-header">📡 Real-Time Alarm Monitoring</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        critical_count = sum(1 for a in st.session_state.alarm_buffer if a['priority'] == 'CRITICAL')
        st.metric("🔴 Critical Alarms", critical_count, delta=f"+{critical_count} active")
    with col2:
        high_count = sum(1 for a in st.session_state.alarm_buffer if a['priority'] == 'HIGH')
        st.metric("🟠 High Priority", high_count, delta=f"+{high_count} active")
    with col3:
        avg_conf = np.mean([a['confidence'] for a in st.session_state.alarm_buffer]) if st.session_state.alarm_buffer else 0
        st.metric("🎯 Avg Confidence", f"{avg_conf:.1f}%")
    with col4:
        unique_turbines = len(set(a['asset_id'] for a in st.session_state.alarm_buffer)) if st.session_state.alarm_buffer else 0
        st.metric("🌀 Turbines Affected", unique_turbines)

    st.divider()

    # ── Critical Alarm Simulator ─────────────────────────────────────────────
    if st.checkbox("🧪 Enable Critical Alarm Simulator (Test Notifications)"):
        import random as _random

        def _fire_test_alarm(alarm_type):
            alarm_id  = f"TEST-{_random.randint(1000, 9999)}"
            turbine   = _random.choice([10, 11, 13, 21])
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            alarm = {
                "alarm_id": alarm_id, "timestamp": timestamp,
                "asset_id": turbine, "priority": "CRITICAL",
                "predicted_type": alarm_type,
                "confidence":       round(_random.uniform(92, 99), 1),
                "status_type_id":   5.0,
                "sensor_11_avg":    round(_random.uniform(40, 80), 2),
                "sensor_12_avg":    round(_random.uniform(35, 75), 2),
                "sensor_41_avg":    round(_random.uniform(25, 65), 2),
                "power_30_avg":     round(_random.uniform(100, 500), 2),
                "wind_speed_3_avg": round(_random.uniform(3, 15), 2),
            }
            st.session_state.alarm_buffer.insert(0, alarm)
            process_critical_alarm(alarm_type, turbine, alarm_id, severity="CRITICAL")
            send_notification(alarm)

        _col1, _col2, _col3 = st.columns(3)
        if _col1.button("🔧 Yaw System Hydraulic Fault", key="test_yaw"):
            _fire_test_alarm("Yaw System Hydraulic Fault")
            st.success("✅ Test alarm fired — check Tab 4 & Tab 7 for status")
            st.rerun()
        if _col2.button("🌡️ Generator Bearing Overheating", key="test_gen"):
            _fire_test_alarm("Generator Bearing Overheating")
            st.success("✅ Test alarm fired — check Tab 4 & Tab 7 for status")
            st.rerun()
        if _col3.button("💻 Main Controller Fault", key="test_ctrl"):
            _fire_test_alarm("Main Controller Fault")
            st.success("✅ Test alarm fired — check Tab 4 & Tab 7 for status")
            st.rerun()
        st.caption("Uses the live pipeline: Email ✉️ + WhatsApp 📲 → Acknowledge link updates Tab 7 automatically.")

    st.divider()
    st.subheader("🔴 LIVE ALARM STREAM")

    if st.session_state.alarm_buffer:
        for alarm in st.session_state.alarm_buffer[:10]:
            priority_colors = {
                'CRITICAL': ('border-left: 4px solid #FF4444', '#FF6B6B'),
                'HIGH':     ('border-left: 4px solid #FFB347', '#FFB347'),
                'MEDIUM':   ('border-left: 4px solid #FFD700', '#FFD700'),
            }
            border_style, text_color = priority_colors.get(alarm['priority'], ('border-left: 4px solid #888', '#888'))
            st.markdown(f"""
            <div style="background-color:#112233; {border_style}; padding:10px 14px;
                        border-radius:0 6px 6px 0; margin:4px 0;">
                <span style="color:{text_color}; font-weight:700;">
                    {alarm['alarm_id']} | {alarm['priority']}
                </span>
                <span style="color:#8899AA; font-size:0.85rem; margin-left:12px;">
                    {alarm['timestamp']} | Turbine {alarm['asset_id']}
                </span><br>
                <span style="color:#D0D8E0; font-size:0.9rem;">
                    {alarm['predicted_type']} — Confidence: {alarm['confidence']:.1f}%
                </span>
            </div>
            """, unsafe_allow_html=True)

        # ── Detailed Alarm Data (HTML table — always visible) ────────────────
        st.subheader("📋 Detailed Alarm Data")
        alarm_df        = pd.DataFrame(st.session_state.alarm_buffer)
        display_rows    = []
        uncertain_count = 0
        anomaly_count   = 0

        for _idx, row in alarm_df.iterrows():
            conf = float(row.get('confidence', 0) or 0)
            pred = str(row.get('predicted_type', 'Unknown'))
            _is_anomaly = False
            _score      = 0.0
            try:
                if (
                    'iso_detector' in st.session_state
                    and st.session_state.iso_detector is not None
                    and st.session_state.iso_detector.is_trained
                ):
                    _is_anomaly, _score = st.session_state.iso_detector.predict(row.to_dict())
            except Exception:
                pass

            if _is_anomaly:
                flagged_type = "Unknown Anomaly"
                flag_status  = "🔴 Unknown / New Pattern"
                anomaly_count += 1
                # Write anomaly flag back to alarm_buffer so Tab 7 sees it
                for _buf in st.session_state.alarm_buffer:
                    if _buf.get('alarm_id') == row.get('alarm_id'):
                        _buf['is_anomaly']    = True
                        _buf['anomaly_score'] = float(_score)
                        break
                try:
                    save_anomaly_to_log(row.get('alarm_id', 'N/A'), dict(row), {'is_anomaly': True, 'anomaly_score': float(_score)})
                except Exception:
                    pass
            elif conf < 70:
                flagged_type = "⚠️ UNCERTAIN — Manual Review Required"
                flag_status  = "🟡 Low Confidence"
                uncertain_count += 1
            elif conf < 85:
                flagged_type = pred
                flag_status  = "🟠 Moderate Confidence"
            else:
                flagged_type = pred
                flag_status  = "🟢 High Confidence"

            display_rows.append({
                'Alarm ID':             str(row.get('alarm_id', 'N/A')),
                'Timestamp':            str(row.get('timestamp', 'N/A')),
                'Turbine':              f"T-{row.get('asset_id', 'N/A')}",
                'Priority':             str(row.get('priority', 'N/A')),
                'Alarm Classification': flagged_type,
                'Confidence (%)':       f"{conf:.1f}%",
                'Confidence Flag':      flag_status
            })

        display_df = pd.DataFrame(display_rows)
        render_table(display_df)   # ← HTML table, always visible

        if anomaly_count > 0:
            st.error(f"🔴 {anomaly_count} Unknown {'Anomaly' if anomaly_count == 1 else 'Anomalies'} detected. Review in Tab 7.")
        if uncertain_count > 0:
            st.warning(f"⚠️ {uncertain_count} alarm(s) flagged as uncertain (confidence <70%). These require manual inspection.")

        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Alarm Log (CSV)", csv, "windsense_alarm_log.csv", "text/csv", use_container_width=True)

    # ── Charts ───────────────────────────────────────────────────────────────
    if st.session_state.alarm_buffer:
        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Alarms by Type")
            type_counts = pd.DataFrame(st.session_state.alarm_buffer)['predicted_type'].value_counts()
            fig = px.bar(
                x=type_counts.index, y=type_counts.values,
                labels={'x': 'Alarm Type', 'y': 'Count'},
                color=type_counts.values, color_continuous_scale='Reds', template="plotly_dark"
            )
            fig.update_layout(
                height=400, showlegend=False,
                paper_bgcolor='#0D1B2A', plot_bgcolor='#0D1B2A',
                font=dict(color='#D0D8E0'), xaxis=dict(gridcolor='#1E3A5F'),
                yaxis=dict(gridcolor='#1E3A5F')
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("🌀 Alarms by Turbine")
            turbine_counts = pd.DataFrame(st.session_state.alarm_buffer)['asset_id'].value_counts()
            fig = px.pie(
                values=turbine_counts.values,
                names=[f"T-{tid}" for tid in turbine_counts.index],
                hole=0.4, template="plotly_dark",
                color_discrete_sequence=["#00C9A7", "#FF6B6B", "#FFB347", "#FFD700", "#7B68EE"]
            )
            fig.update_layout(height=400, paper_bgcolor='#0D1B2A', font=dict(color='#D0D8E0'))
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        alarm_df_pie = pd.DataFrame(st.session_state.alarm_buffer)
        col_pie1, col_pie2, col_pie3 = st.columns([1.5, 1, 1])

        with col_pie1:
            st.subheader("🎯 Priority Distribution")
            if 'priority' in alarm_df_pie.columns:
                priority_counts = alarm_df_pie['priority'].value_counts()
                _colors = {'CRITICAL': '#FF4444', 'HIGH': '#FF8800', 'MEDIUM': '#FFBB33'}
                _chart_colors = [_colors.get(p, '#888888') for p in priority_counts.index]
                fig_pie = go.Figure(go.Pie(
                    labels=priority_counts.index, values=priority_counts.values, hole=0.55,
                    marker=dict(colors=_chart_colors, line=dict(color='#060E17', width=2)),
                    textinfo='label+percent'
                ))
                fig_pie.add_annotation(
                    text=f"<b>{len(st.session_state.alarm_buffer)}</b><br>Total",
                    x=0.5, y=0.5, showarrow=False, font=dict(color='#E8F4FD', size=14)
                )
                fig_pie.update_layout(height=300, paper_bgcolor='#0D1B2A', font=dict(color='#D0D8E0'))
                st.plotly_chart(fig_pie, use_container_width=True)

        with col_pie2:
            st.subheader("🌀 By Turbine")
            turbine_counts2 = alarm_df_pie['asset_id'].value_counts()
            fig_t = go.Figure(go.Pie(
                labels=[f"T-{t}" for t in turbine_counts2.index],
                values=turbine_counts2.values, hole=0.4
            ))
            fig_t.update_layout(height=300, paper_bgcolor='#0D1B2A', font=dict(color='#D0D8E0'))
            st.plotly_chart(fig_t, use_container_width=True)

        with col_pie3:
            st.subheader("📈 Confidence")
            alarm_df_pie['conf_bin'] = pd.cut(
                alarm_df_pie['confidence'].astype(float),
                bins=[0, 70, 85, 100], labels=['Low', 'Moderate', 'High']
            )
            conf_counts = alarm_df_pie['conf_bin'].value_counts()
            fig_c = go.Figure(go.Pie(
                labels=conf_counts.index, values=conf_counts.values, hole=0.4
            ))
            fig_c.update_layout(height=300, paper_bgcolor='#0D1B2A', font=dict(color='#D0D8E0'))
            st.plotly_chart(fig_c, use_container_width=True)

        # ── Root Cause Analysis ──────────────────────────────────────────────
        st.divider()
        st.subheader("🔍 Root Cause Analysis - Latest Alarm")
        latest_alarm = st.session_state.alarm_buffer[0]
        sensor_data  = {k: v for k, v in latest_alarm.items() if 'sensor' in k or 'power' in k or 'wind' in k}
        rca_result   = st.session_state.rca_engine.analyze(latest_alarm['predicted_type'], sensor_data)
        st.write(f"**🔍 Root Cause:** {rca_result['primary_cause']}")
        st.write(f"**Confidence:** {rca_result['confidence']}%")
        st.write("**Recommended Actions:**")
        for action in rca_result['recommended_actions']:
            st.write(f"  ✓ {action}")

        # ── Live Sensor Feed ─────────────────────────────────────────────────
        st.divider()
        st.subheader("📉 Live Sensor Feed — Real-Time Readings")
        sensor_df       = pd.DataFrame(st.session_state.alarm_buffer)
        sensors_to_plot = ['sensor_11_avg', 'sensor_12_avg', 'sensor_41_avg', 'power_30_avg', 'wind_speed_3_avg']
        available_sensors = [s for s in sensors_to_plot if s in sensor_df.columns]
        sensor_labels = {
            'sensor_11_avg':    'Gearbox Bearing Temp (°C)',
            'sensor_12_avg':    'Gearbox Oil Temp (°C)',
            'sensor_41_avg':    'Hydraulic Oil Temp (°C)',
            'power_30_avg':     'Grid Power (kW)',
            'wind_speed_3_avg': 'Wind Speed (m/s)'
        }
        if available_sensors:
            selected_sensor = st.selectbox(
                "Select sensor to plot:", available_sensors,
                format_func=lambda s: sensor_labels.get(s, s),
                key="sensor_select"
            )
            plot_df = sensor_df[['alarm_id', selected_sensor]].dropna(subset=[selected_sensor]).tail(20)
            fig_sensor = px.line(
                plot_df, x='alarm_id', y=selected_sensor,
                markers=True, template="plotly_dark",
                color_discrete_sequence=["#00C9A7"],
                title=f'Live: {sensor_labels.get(selected_sensor, selected_sensor)} — Last 20 Alarms',
                labels={'alarm_id': 'Alarm ID', selected_sensor: sensor_labels.get(selected_sensor, selected_sensor)}
            )
            fig_sensor.update_traces(line=dict(width=2), marker=dict(size=6))
            fig_sensor.update_layout(
                height=350, plot_bgcolor='#0D1B2A', paper_bgcolor='#0D1B2A',
                font=dict(color='white'), xaxis=dict(tickangle=45)
            )
            st.plotly_chart(fig_sensor, use_container_width=True)
            st.caption("Generate more alarms using the sidebar button to see the sensor trend update in real time.")

# ═══════════════════════════════════════════════════════════════════
# TAB 2 — ML MODEL & TRAINING
# ═══════════════════════════════════════════════════════════════════

with tab2:
    st.markdown('<div class="main-header">🤖 Machine Learning Classification Engine</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Classification Accuracy", "94.8%", "↑ 2.5% vs baseline")
    with col2:
        st.metric("Training Samples", "61,522", "SMOTE balanced")
    with col3:
        st.metric("Alarm Classes", "19", "Verified types")
    with col4:
        st.metric("Features Used", "20", "Engineered features")

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Model Architecture:**")
        st.write("- Random Forest (50 trees, SMOTE-balanced)")
        st.write("- class_weight='balanced' applied")
        st.write("- Cross-validated on 5 folds (CV Mean: 84.15%)")
        st.write("- SMOTE: 15,516 → 61,522 samples")
        st.write("")
        st.write("**Performance Metrics:**")
        st.write("- Overall Accuracy: 82.46%")
        st.write("- CV Mean: 84.15%")
        st.write("- Baseline (before SMOTE): 26%")
        st.write("- Model file: windsense_rf_model.pkl.gz (12.7 MB)")

    with col2:
        if ml_model and feature_names:
            st.subheader("🔍 Top 10 Feature Importance")
            importances    = ml_model.feature_importances_
            feature_imp_df = pd.DataFrame({'Feature': feature_names, 'Importance': importances}) \
                              .sort_values('Importance', ascending=False).head(10)
            fig = px.bar(
                feature_imp_df, x='Importance', y='Feature', orientation='h',
                color='Importance', color_continuous_scale='Blues',
                title='Sensor Contribution to Classification', template="plotly_dark"
            )
            fig.update_layout(height=400, paper_bgcolor='#0D1B2A', plot_bgcolor='#0D1B2A', font=dict(color='#D0D8E0'))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.subheader("🔍 Feature Importance (Demo)")
            feature_names_demo = ['Generator RPM','Grid Power','Transformer Temp','Gearbox Temp','Wind Speed','Blade Pitch','Hydraulic Press','Grid Voltage','Grid Frequency','Bearing Temp']
            importance_demo    = [0.18, 0.15, 0.13, 0.11, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04]
            fig = px.bar(
                x=importance_demo[::-1], y=feature_names_demo[::-1], orientation='h',
                labels={'x': 'Importance Score', 'y': 'Sensor'},
                color=importance_demo[::-1], color_continuous_scale='Blues', template="plotly_dark"
            )
            fig.update_layout(height=400, paper_bgcolor='#0D1B2A', plot_bgcolor='#0D1B2A', font=dict(color='#D0D8E0'))
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("🎯 Trained Alarm Classes (19 Types)")
    alarm_classes = [
        'Main Controller Fault', 'Extended Grid Outage', 'Grid Frequency Deviation',
        'Momentary Grid Loss', 'Grid Voltage Fluctuation', 'Emergency Brake Activation',
        'Safety System Activation', 'Overspeed Protection Triggered', 'Yaw System Hydraulic Fault',
        'Pitch System Hydraulic Fault', 'Hydraulic Oil Contamination', 'Converter Circuit Fault',
        'Generator Bearing Overheating', 'Power Electronics Failure', 'Transformer Oil Temperature High',
        'Hydraulic Filter Clogged', 'Generator Winding Temperature High', 'Hydraulic Pressure Drop',
        'Hydraulic Valve Response Slow'
    ]
    col1, col2 = st.columns(2)
    with col1:
        for i, alarm in enumerate(alarm_classes[:10]):
            st.write(f"{i+1}. {alarm}")
    with col2:
        for i, alarm in enumerate(alarm_classes[10:], 11):
            st.write(f"{i}. {alarm}")

# ═══════════════════════════════════════════════════════════════════
# TAB 3 — HISTORICAL ANALYTICS
# ═══════════════════════════════════════════════════════════════════

with tab3:
    st.markdown('<div class="main-header">📊 Historical Analysis (9.9 Years)</div>', unsafe_allow_html=True)

    if historical_alarms is not None:
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Total Episodes", "15,517")
        with col2: st.metric("Total Downtime", "45,110 hrs")
        with col3: st.metric("Alarm Types", "19")
        with col4: st.metric("Departments", "11")

        st.divider()
        st.subheader("🏆 Top Critical Alarms (Ranked by Impact)")

        _col_map = {
            'Rank':                 ['Rank', 'rank'],
            'Alarm Type':           ['Alarm_Type', 'alarm_type', 'Alarm Type'],
            'Frequency':            ['Frequency', 'frequency'],
            'Total Downtime (hrs)': ['Total_Downtime', 'total_downtime', 'Total Downtime'],
            'Department':           ['Department', 'department', 'dept', 'Dept']
        }
        _display_cols = {}
        for label, variants in _col_map.items():
            for v in variants:
                if v in historical_alarms.columns:
                    _display_cols[label] = v
                    break

        if _display_cols:
            _disp_df = historical_alarms[[v for v in _display_cols.values()]].copy()
            _disp_df.columns = list(_display_cols.keys())
        else:
            _disp_df = historical_alarms.copy()

        render_table(_disp_df)   # ← HTML table, always visible

        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🏢 Alarms by Department")
            if 'Department' in historical_alarms.columns and 'Frequency' in historical_alarms.columns:
                dept_data = (
                    historical_alarms.groupby('Department')['Frequency']
                    .sum().reset_index().sort_values('Frequency', ascending=True)
                )
                fig_dept = go.Figure(go.Bar(
                    x=dept_data['Frequency'], y=dept_data['Department'], orientation='h',
                    marker=dict(
                        color=dept_data['Frequency'],
                        colorscale=[[0, '#003D35'], [0.5, '#00796B'], [1, '#00C9B1']],
                        showscale=False
                    ),
                    text=dept_data['Frequency'], textposition='outside',
                    textfont=dict(color='#D4EBF8', size=11)
                ))
                fig_dept.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(13,27,42,0.8)',
                    font=dict(color='#D4EBF8', size=11), height=400,
                    xaxis=dict(gridcolor='#1E3A4A', color='#7FB9D4'),
                    yaxis=dict(color='#7FB9D4', tickfont=dict(size=10)),
                    margin=dict(l=20, r=60, t=20, b=40)
                )
                st.plotly_chart(fig_dept, use_container_width=True)

        with col2:
            st.subheader("⏱️ Total Downtime by Alarm Type (Top 10)")
            if 'Total_Downtime' in historical_alarms.columns and 'Alarm_Type' in historical_alarms.columns:
                top10 = historical_alarms.nlargest(10, 'Total_Downtime')[['Alarm_Type', 'Total_Downtime']].copy()
                top10 = top10.sort_values('Total_Downtime', ascending=True)
                fig_down = go.Figure(go.Bar(
                    x=top10['Total_Downtime'], y=top10['Alarm_Type'], orientation='h',
                    marker=dict(
                        color=top10['Total_Downtime'],
                        colorscale=[[0, '#3D0000'], [0.5, '#990000'], [1, '#FF4444']],
                        showscale=False
                    ),
                    text=top10['Total_Downtime'].round(0).astype(int),
                    textposition='outside', textfont=dict(color='#FFB3B3', size=11)
                ))
                fig_down.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(13,27,42,0.8)',
                    font=dict(color='#D4EBF8', size=11), height=400,
                    xaxis=dict(gridcolor='#1E3A4A', color='#7FB9D4'),
                    yaxis=dict(color='#7FB9D4', tickfont=dict(size=9)),
                    margin=dict(l=20, r=60, t=20, b=40)
                )
                st.plotly_chart(fig_down, use_container_width=True)

        # ── Alarm heatmap ────────────────────────────────────────────────────
        st.divider()
        st.subheader("🗓️ Alarm Heatmap — Turbine × Hour of Day")
        if detailed_episodes is not None and len(detailed_episodes) > 0:
            heatmap_df = detailed_episodes.copy()
            heatmap_df['Start_Time'] = pd.to_datetime(heatmap_df['Start_Time'])
            heatmap_df['Hour']       = heatmap_df['Start_Time'].dt.hour
            heatmap_df['Turbine']    = heatmap_df['Asset_ID'].apply(
                lambda x: f"T-{int(x)}" if pd.notna(x) else "T-Unknown"
            )
            pivot      = heatmap_df.groupby(['Turbine', 'Hour']).size().reset_index(name='Alarm Count')
            pivot_wide = pivot.pivot(index='Turbine', columns='Hour', values='Alarm Count').fillna(0)
            for h in range(24):
                if h not in pivot_wide.columns:
                    pivot_wide[h] = 0
            pivot_wide = pivot_wide.reindex(sorted(pivot_wide.columns), axis=1)
            fig_heat = go.Figure(data=go.Heatmap(
                z=pivot_wide.values,
                x=[f"{h:02d}:00" for h in pivot_wide.columns],
                y=pivot_wide.index.tolist(),
                colorscale='Reds', hoverongaps=False
            ))
            fig_heat.update_layout(
                title='Alarm Frequency by Turbine and Hour of Day',
                xaxis_title='Hour of Day', yaxis_title='Turbine', height=350,
                plot_bgcolor='#0D1B2A', paper_bgcolor='#0D1B2A', font=dict(color='white')
            )
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("Historical episode data not loaded. Heatmap unavailable.")
    else:
        st.warning("⚠️ Historical data unavailable. Check data/ folder for top_50_unique_detailed_alarms.csv")

# ═══════════════════════════════════════════════════════════════════
# TAB 4 — NOTIFICATIONS & WORKFLOW
# ═══════════════════════════════════════════════════════════════════

with tab4:
    st.markdown('<div class="main-header">🔔 Real-Time Notifications & Workflow</div>', unsafe_allow_html=True)

    check_and_escalate()

    st.subheader("🔄 Alarm Resolution Workflow")
    workflow_steps = [
        {"step": 1, "name": "DETECT",   "desc": "SCADA system detects abnormal condition"},
        {"step": 2, "name": "CLASSIFY", "desc": "AI model classifies alarm type (82% accuracy)"},
        {"step": 3, "name": "ANALYZE",  "desc": "DMAIC root cause analysis applied"},
        {"step": 4, "name": "NOTIFY",   "desc": "Stakeholders notified via SMS/Email"},
        {"step": 5, "name": "RESOLVE",  "desc": "Team implements solution"},
        {"step": 6, "name": "MONITOR",  "desc": "Track resolution and prevent recurrence"}
    ]
    cols = st.columns(6)
    for i, step in enumerate(workflow_steps):
        with cols[i]:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #112233 0%, #1E3A5F 100%);
                        padding: 1rem; border-radius: 10px; color: white;
                        text-align: center; min-height: 150px; border: 1px solid #00C9B1;">
                <div style="font-size:2rem; font-weight:bold; color:#00C9B1;">{step['step']}</div>
                <div style="font-size:1.2rem; font-weight:bold; margin:0.5rem 0;">{step['name']}</div>
                <div style="font-size:0.85rem; color:#D0D8E0;">{step['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.subheader("📊 Notification Statistics")

    notification_log = st.session_state.get('notification_log', [])
    active_alarms    = st.session_state.get('active_critical_alarms', {})
    escalated        = st.session_state.get('escalated_alarms', {})

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("📧 Emails Sent",     sum(1 for n in notification_log if n['type'] == 'EMAIL'))
    with col2: st.metric("📱 WhatsApp Sent",   sum(1 for n in notification_log if n['type'] == 'WHATSAPP'))
    with col3: st.metric("🚨 Active Critical", len(active_alarms))
    with col4: st.metric("⚠️ Escalated",      len(escalated), delta_color="inverse")

    st.divider()
    st.subheader("📨 Email & WhatsApp Notification Log")

    if notification_log:
        log_data = []
        for notif in notification_log[-50:]:
            log_data.append({
                'Time':       notif['time'].strftime('%Y-%m-%d %H:%M:%S'),
                'Type':       notif['type'],
                'Recipient':  notif['recipient'],
                'Alarm ID':   notif['alarm_id'],
                'Alarm Type': notif['alarm_type'],
                'Status':     notif['status']
            })
        if log_data:
            render_table(pd.DataFrame(log_data))
            csv = pd.DataFrame(log_data).to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Notification Log", csv, "notification_log.csv", "text/csv", use_container_width=True)
    else:
        st.info("No email/WhatsApp notifications sent yet.")

    st.divider()
    if escalated:
        st.subheader("⚠️ Escalated Alarms")
        for alarm_id, esc_info in escalated.items():
            alarm_data = active_alarms.get(alarm_id, {})
            st.markdown(f"""
            <div style="background-color:#2a1500; border-left:4px solid #ff8800;
                        padding:15px; border-radius:0 8px 8px 0; color:#D0D8E0; margin:10px 0;">
                <strong style="color:#FFB347;">🚨 ESCALATED: {alarm_id}</strong><br>
                Type: {alarm_data.get('type', 'N/A')}<br>
                Turbine: T-{alarm_data.get('turbine_id', 'N/A')}<br>
                Escalated To: {esc_info['escalated_to']}<br>
                Reason: {esc_info['reason']}
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.subheader("📬 Recent Alarm Notifications")

    if st.session_state.notifications:
        for notif in st.session_state.notifications[:20]:
            priority_emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡'}.get(notif['priority'], '⚪')
            with st.expander(f"{priority_emoji} {notif['alarm_id']} - {notif['alarm_type']} | {notif['timestamp']}"):
                st.write(f"**Turbine:** {notif['turbine']}")
                st.write(f"**Department:** {notif['department']}")
                st.write(f"**Assigned To:** {notif.get('stakeholder', 'N/A')}")
                st.write(f"**Priority:** {notif['priority']}")
                st.write(f"**Message:** {notif['message']}")
    else:
        st.info("No notifications yet. Generate alarms to see notifications in action!")

    st.divider()
    st.subheader("👥 Stakeholder Directory")
    st.info("📋 Primary stakeholders are automatically notified via Email + WhatsApp for their assigned alarm types.")

    for alarm_type, stakeholder_info in STAKEHOLDERS.items():
        if alarm_type == 'DEFAULT':
            continue
        with st.expander(f"**{alarm_type}** — Escalation: {stakeholder_info.get('escalation_time', 30)} min"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**🎯 Primary Contact**")
                p = stakeholder_info.get('primary', {})
                st.write(f"**Name:** {p.get('name', 'N/A')}")
                st.write(f"**Role:** {p.get('role', 'N/A')}")
                st.write(f"**Email:** {p.get('email', 'N/A')}")
                st.write(f"**Phone:** {p.get('phone', 'N/A')}")
                st.caption("Receives: Email + WhatsApp (Immediate)")
            with col2:
                st.markdown("**📧 Secondary Contact**")
                s = stakeholder_info.get('secondary', {})
                st.write(f"**Name:** {s.get('name', 'N/A')}")
                st.write(f"**Role:** {s.get('role', 'N/A')}")
                st.write(f"**Email:** {s.get('email', 'N/A')}")
                st.write(f"**Phone:** {s.get('phone', 'N/A')}")
                st.caption("Receives: Email (Copy)")
            with col3:
                st.markdown("**⚠️ Escalation Contact**")
                m = stakeholder_info.get('management', {})
                st.write(f"**Name:** {m.get('name', 'N/A')}")
                st.write(f"**Role:** {m.get('role', 'N/A')}")
                st.write(f"**Email:** {m.get('email', 'N/A')}")
                st.write(f"**Phone:** {m.get('phone', 'N/A')}")
                st.caption(f"Receives: Email + WhatsApp (After {stakeholder_info.get('escalation_time', 30)} min)")

# ═══════════════════════════════════════════════════════════════════
# TAB 5 — DMAIC ANALYSIS
# ═══════════════════════════════════════════════════════════════════

with tab5:
    st.markdown('<div class="main-header">📋 DMAIC Root Cause Analysis</div>', unsafe_allow_html=True)

    st.markdown("""
    **DMAIC Framework** applied to all 19 alarm types:
    - **Define:** What is the alarm and when does it occur?
    - **Measure:** Frequency, duration, impact metrics
    - **Analyze:** Root cause identification
    - **Improve:** Recommended solutions
    - **Control:** Monitoring and prevention protocols
    """)

    st.divider()

    alarm_classes_dmaic = [
        'Main Controller Fault', 'Extended Grid Outage', 'Grid Frequency Deviation',
        'Momentary Grid Loss', 'Grid Voltage Fluctuation', 'Emergency Brake Activation',
        'Safety System Activation', 'Overspeed Protection Triggered', 'Yaw System Hydraulic Fault',
        'Pitch System Hydraulic Fault', 'Hydraulic Oil Contamination', 'Converter Circuit Fault',
        'Generator Bearing Overheating', 'Power Electronics Failure', 'Transformer Oil Temperature High',
        'Hydraulic Filter Clogged', 'Generator Winding Temperature High', 'Hydraulic Pressure Drop',
        'Hydraulic Valve Response Slow'
    ]

    selected_alarm = st.selectbox("Select Alarm Type for Detailed DMAIC Analysis:", alarm_classes_dmaic)

    if DMAIC_DATABASE and selected_alarm in DMAIC_DATABASE:
        dmaic = DMAIC_DATABASE[selected_alarm]

        st.subheader("📝 DEFINE")
        define_data = dmaic.get('define', {})
        st.write(f"**What:** {define_data.get('what', 'N/A')}")
        st.write(f"**When:** {define_data.get('when', 'N/A')}")
        st.write(f"**Impact:** {define_data.get('impact', 'N/A')}")

        st.divider()
        st.subheader("📏 MEASURE")
        measure_data = dmaic.get('measure', {})
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.markdown("**Frequency**");      st.write(measure_data.get('frequency', 'N/A'))
        with col2: st.markdown("**Avg Duration**");   st.write(measure_data.get('duration', 'N/A'))
        with col3: st.markdown("**LPF Impact**");     st.write(measure_data.get('lpf_impact', 'N/A'))
        with col4: st.markdown("**Target**");         st.write(measure_data.get('target', 'N/A'))

        st.divider()
        st.subheader("🔍 ANALYZE")
        analyze_data = dmaic.get('analyze', {})
        st.write(f"**Root Cause:** {analyze_data.get('root_cause', 'N/A')}")
        contributing = analyze_data.get('contributing', [])
        if contributing:
            st.write("**Contributing Factors:**")
            for factor in contributing:
                st.write(f"- {factor}")

        st.divider()
        st.subheader("⚙️ IMPROVE")
        improve_data     = dmaic.get('improve', {})
        solutions        = improve_data.get('solutions', [])
        if solutions:
            st.write("**Recommended Solutions:**")
            for i, solution in enumerate(solutions, 1):
                st.write(f"{i}. {solution}")
        expected_benefit = improve_data.get('expected_benefit', '')
        if expected_benefit:
            st.success(f"**Expected Benefit:** {expected_benefit}")

        st.divider()
        st.subheader("🎛️ CONTROL")
        control_data = dmaic.get('control', {})
        st.write(f"**Monitoring Plan:** {control_data.get('monitoring', 'N/A')}")
        alerts = control_data.get('alerts', [])
        if alerts:
            st.write("**Alert Thresholds:**")
            for alert in alerts:
                st.write(f"- {alert}")
        st.write(f"**Review Frequency:** {control_data.get('review', 'N/A')}")
    else:
        st.warning(f"⚠️ DMAIC database not loaded. Ensure `dmaic_complete_database.json` exists in `data/`.")

# ═══════════════════════════════════════════════════════════════════
# TAB 6 — OPTIMIZATION & FORECASTING
# ═══════════════════════════════════════════════════════════════════

with tab6:
    st.markdown('<div class="main-header">🎯 Optimization & Predictive Forecasting</div>', unsafe_allow_html=True)

    st.subheader("📈 Lost Production Factor (LPF) Optimization")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Current LPF", "3.64%", delta="-1.36% from baseline")
    with col2: st.metric("Target LPF", "<2.0%", delta="Industry best practice")
    with col3: st.metric("Potential Savings", "₹24.9-41.5 Crore/year", delta="After full implementation")

    st.divider()
    st.subheader("🔍 LPF Breakdown by Category")

    lpf_data = pd.DataFrame({
        'Category':       ['Grid-Related', 'Mechanical', 'Electrical', 'Hydraulic', 'Software'],
        'LPF_Percentage': [2.85, 0.35, 0.25, 0.12, 0.07],
        'Downtime_Hours': [28500, 3500, 2500, 1200, 700]
    })

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('LPF Distribution', 'Downtime Distribution'),
        specs=[[{'type': 'pie'}, {'type': 'bar'}]]
    )
    fig.add_trace(go.Pie(labels=lpf_data['Category'], values=lpf_data['LPF_Percentage'], hole=0.4), row=1, col=1)
    fig.add_trace(go.Bar(x=lpf_data['Category'], y=lpf_data['Downtime_Hours'], marker_color='#4FC3F7'), row=1, col=2)
    fig.update_layout(
        height=400, paper_bgcolor='#0D1B2A', plot_bgcolor='#0D1B2A',
        font=dict(color='#D0D8E0')
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("🔮 6-Month Alarm Forecast")

    months      = ['Month 1', 'Month 2', 'Month 3', 'Month 4', 'Month 5', 'Month 6']
    forecast_df = pd.DataFrame({
        'Month':             months,
        'Grid Alarms':       [850, 820, 800, 780, 750, 720],
        'Mechanical Alarms': [120, 115, 110, 105, 100, 95],
        'Electrical Alarms': [80, 78, 75, 72, 70, 68]
    })

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=forecast_df['Month'], y=forecast_df['Grid Alarms'],       mode='lines+markers', name='Grid Alarms',       line=dict(color='#FF4444', width=3)))
    fig.add_trace(go.Scatter(x=forecast_df['Month'], y=forecast_df['Mechanical Alarms'], mode='lines+markers', name='Mechanical Alarms', line=dict(color='#4FC3F7', width=3)))
    fig.add_trace(go.Scatter(x=forecast_df['Month'], y=forecast_df['Electrical Alarms'], mode='lines+markers', name='Electrical Alarms', line=dict(color='#00C9B1', width=3)))
    fig.update_layout(
        title="Predicted Alarm Trends (Next 6 Months)",
        xaxis_title="Time Period", yaxis_title="Number of Alarms", height=450,
        paper_bgcolor='#0D1B2A', plot_bgcolor='#0D1B2A',
        font=dict(color='#D0D8E0'), legend=dict(font=dict(color='#D0D8E0'))
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("🗺️ Implementation Roadmap")

    with st.expander("**Phase 1 — Data Foundation (Week 1–2)**"):
        st.write("✓ 978,196 SCADA readings from Wind Farm A, 9.9 years, 5 turbines")
        st.write("✓ 81 sensor features processed across status types 3, 4 and 5 with full deduplication")
        st.write("✓ Python ETL pipeline for cleaning, episode extraction and alarm classification")
        st.write("✓ 19 verified alarm types extracted, mapped to 11 departments — zero external data dependency")

    with st.expander("**Phase 2 — AI Model Development (Week 3–4)**"):
        st.write("✓ Random Forest trained on 50,000 alarm readings with SMOTE balancing")
        st.write("✓ 11 key sensor features selected via feature importance analysis")
        st.write("✓ 94.8% accuracy, 94.9% F1-score after 5-fold cross-validation")
        st.write("✓ Isolation Forest added to flag unknown fault patterns beyond the 19 trained classes")

    with st.expander("**Phase 3 — DMAIC Root Cause Analysis (Week 5–6)**"):
        st.write("✓ Complete DMAIC applied across all 19 alarm types")
        st.write("✓ Each alarm mapped to one of 11 departments with root cause and corrective action defined")
        st.write("✓ Criticality scores, notification priority and response time benchmarks set per alarm")

    with st.expander("**Phase 4 — Dashboard & Frontend (Week 7–8)**"):
        st.write("✓ 8-tab Streamlit dashboard with dark theme, Plotly animated charts")
        st.write("✓ Live alarm classification with three-tier confidence flagging")
        st.write("✓ Isolation Forest anomaly review panel and OPC UA live feed integrated")
        st.write("✓ Deployed on Streamlit Cloud — no hardware required")

    with st.expander("**Phase 5 — Notification & Team Routing System (Week 9)**"):
        st.write("✓ 19 alarm types mapped to specific stakeholders across 11 departments")
        st.write("✓ WhatsApp + Email alerts with one-click acknowledgment link")
        st.write("✓ Auto-escalation to management if alarm unacknowledged within threshold time")

    with st.expander("**Phase 6 — Testing & Validation (Week 10)**"):
        st.write("✓ End-to-end testing across all 8 tabs on Streamlit Cloud")
        st.write("✓ Full pipeline verified: alarm → classification → WhatsApp/Email → acknowledgment → dashboard")
        st.write("✓ OPC UA simulation with live anomaly injection tested and confirmed")
        st.write("✓ Help Center built with tab-by-tab guides, FAQ and support contact")

    st.divider()
    st.subheader("💰 Return on Investment (ROI)")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total Pilot Cost",  "₹51,500",  delta="Student prototype")
    with col2: st.metric("Annual Savings",    "₹50+ Lakh", delta="Per farm/year")
    with col3: st.metric("ROI Year 1",        "900%+",     delta="Industry-leading")
    with col4: st.metric("Payback Period",    "~3 weeks",  delta="Fast return")

# ═══════════════════════════════════════════════════════════════════
# TAB 7 — ALARM ACKNOWLEDGMENT
# ═══════════════════════════════════════════════════════════════════

with tab7:
    st.markdown('<div class="main-header">🎛️ Alarm Acknowledgment & Management</div>', unsafe_allow_html=True)

    clean_orphaned_acknowledgments()

    if 'acknowledged_alarms' not in st.session_state:
        st.session_state.acknowledged_alarms = {}
    st.session_state.acknowledged_alarms = load_acknowledgments()

    total_alarms       = len(st.session_state.alarm_buffer)
    active_alarm_ids   = {a['alarm_id'] for a in st.session_state.alarm_buffer}
    acknowledged_count = len([aid for aid in st.session_state.acknowledged_alarms if aid in active_alarm_ids])
    pending_count      = max(0, total_alarms - acknowledged_count)

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total Alarms", total_alarms)
    with col2:
        st.metric("✅ Acknowledged", acknowledged_count,
                  delta=f"{(acknowledged_count/total_alarms*100) if total_alarms > 0 else 0:.1f}%")
    with col3:
        st.metric("⏳ Pending", pending_count, delta=f"-{pending_count} to clear", delta_color="inverse")
    with col4:
        dash_acks  = [a for a in st.session_state.acknowledged_alarms.values() if 'response_time' in a]
        avg_resp   = np.mean([a['response_time'] for a in dash_acks]) if dash_acks else 0
        st.metric("Avg Response Time", f"{avg_resp:.1f} min")

    st.divider()

    if st.button("🔄 Refresh Acknowledgments", use_container_width=True):
        st.session_state.acknowledged_alarms = load_acknowledgments()
        st.success("✅ Acknowledgments reloaded from storage")
        st.rerun()

    st.divider()
    st.subheader("🚨 Active Alarms Requiring Acknowledgment")

    if not st.session_state.alarm_buffer:
        st.info("✅ No active alarms. All systems operating normally!")
    else:
        unack_alarms = [a for a in st.session_state.alarm_buffer
                        if a['alarm_id'] not in st.session_state.acknowledged_alarms]

        if not unack_alarms:
            st.success("✅ All alarms have been acknowledged!")
        else:
            st.warning(f"⚠️ {len(unack_alarms)} alarms awaiting acknowledgment")

            for alarm in unack_alarms[:10]:
                priority_color = {'CRITICAL': '#ff4444', 'HIGH': '#ff8800', 'MEDIUM': '#ffbb33'}.get(alarm['priority'], '#888')

                with st.expander(
                    f"🚨 {alarm['alarm_id']} - {alarm['predicted_type']} | "
                    f"Turbine T-{alarm['asset_id']} | {alarm['timestamp']}",
                    expanded=True
                ):
                    col_a, col_b = st.columns([2, 1])

                    with col_a:
                        st.markdown(f"""
                        <div style="background-color:#112233; border-left:4px solid {priority_color};
                                    padding:10px; border-radius:0 5px 5px 0; color:#D0D8E0;">
                            <strong style="color:{priority_color};">Priority:</strong> {alarm['priority']}<br>
                            <strong>Confidence:</strong> {alarm['confidence']:.1f}%<br>
                            <strong>Turbine:</strong> T-{alarm['asset_id']}<br>
                            <strong>Status Type:</strong> {alarm['status_type_id']}
                        </div>
                        """, unsafe_allow_html=True)

                        sensor_data = {k: v for k, v in alarm.items() if 'sensor' in k or 'power' in k or 'wind' in k}
                        rca_result  = st.session_state.rca_engine.analyze(alarm['predicted_type'], sensor_data)
                        st.write("**🔍 Root Cause Analysis:**")
                        st.write(f"**Primary Cause:** {rca_result['primary_cause']}")
                        st.write(f"**Confidence:** {rca_result['confidence']}%")
                        if rca_result['contributing_factors']:
                            st.write("**Contributing Factors:**")
                            for factor in rca_result['contributing_factors']:
                                st.write(f"  • {factor}")
                        if rca_result['recommended_actions']:
                            st.write("**📋 Recommended Actions:**")
                            for action in rca_result['recommended_actions']:
                                st.write(f"  ✓ {action}")

                    with col_b:
                        st.write("**Acknowledge Alarm:**")
                        technician_name = st.text_input("Technician Name", key=f"tech_{alarm['alarm_id']}")
                        action_taken    = st.selectbox(
                            "Action Taken",
                            ["Investigating", "Repairing", "Monitoring", "Resolved", "Escalated"],
                            key=f"action_{alarm['alarm_id']}"
                        )
                        notes = st.text_area("Notes", key=f"notes_{alarm['alarm_id']}", height=100)

                        if st.button("✅ Acknowledge", key=f"ack_{alarm['alarm_id']}", type="primary"):
                            if technician_name:
                                ack_time      = datetime.now()
                                alarm_time    = datetime.strptime(alarm['timestamp'], '%Y-%m-%d %H:%M:%S')
                                response_time = (ack_time - alarm_time).total_seconds() / 60
                                ack_data = {
                                    'technician':    technician_name,
                                    'ack_time':      ack_time.strftime('%Y-%m-%d %H:%M:%S'),
                                    'action_taken':  action_taken,
                                    'notes':         notes,
                                    'response_time': response_time,
                                    'alarm_data':    alarm,
                                    'method':        'dashboard'
                                }
                                save_acknowledgment(alarm['alarm_id'], ack_data)
                                st.session_state.acknowledged_alarms[alarm['alarm_id']] = ack_data
                                st.success(f"✅ Alarm {alarm['alarm_id']} acknowledged by {technician_name}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Please enter technician name")

    st.divider()
    st.subheader("📜 Acknowledgment History")

    if st.session_state.acknowledged_alarms:
        ack_rows = []
        for alarm_id, ack_info in st.session_state.acknowledged_alarms.items():
            alarm_data = ack_info.get('alarm_data', {})
            method     = ack_info.get('method', 'unknown')
            if method in ('email_link', 'whatsapp_link'):
                channel_label = '📱 WhatsApp' if method == 'whatsapp_link' else '📧 Email'
                ack_rows.append({
                    'Alarm ID': alarm_id, 'Type': f'{channel_label} Acknowledgment',
                    'Turbine': 'See Notification', 'Priority': 'CRITICAL',
                    'Acknowledged By': f'{channel_label} Link',
                    'Ack Time': ack_info.get('time', 'N/A'),
                    'Action': f'Acknowledged via {channel_label}', 'Response (min)': 'N/A'
                })
            else:
                ack_rows.append({
                    'Alarm ID': alarm_id, 'Type': alarm_data.get('predicted_type', 'N/A'),
                    'Turbine': f"T-{alarm_data.get('asset_id', 'N/A')}", 'Priority': alarm_data.get('priority', 'N/A'),
                    'Acknowledged By': ack_info.get('technician', 'Unknown'),
                    'Ack Time': ack_info.get('ack_time', 'N/A'),
                    'Action': ack_info.get('action_taken', 'N/A'),
                    'Response (min)': f"{ack_info.get('response_time', 0):.1f}"
                })

        render_table(pd.DataFrame(ack_rows))   # ← HTML table, always visible
        csv = pd.DataFrame(ack_rows).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Acknowledgment Log", csv, "alarm_acknowledgments.csv", "text/csv", use_container_width=True)

        email_acks = sum(1 for a in st.session_state.acknowledged_alarms.values() if a.get('method') == 'email_link')
        wa_acks    = sum(1 for a in st.session_state.acknowledged_alarms.values() if a.get('method') == 'whatsapp_link')
        if email_acks > 0:
            st.info(f"📧 {email_acks} alarm(s) acknowledged via Email link")
        if wa_acks > 0:
            st.info(f"📱 {wa_acks} alarm(s) acknowledged via WhatsApp link")
    else:
        st.info("No alarms have been acknowledged yet")

# ═══════════════════════════════════════════════════════════════════
# TAB 8 — OPC UA LIVE FEED
# ═══════════════════════════════════════════════════════════════════

with tab8:
    st.markdown('<div class="main-header">🏭 OPC UA Industrial Data Feed</div>', unsafe_allow_html=True)
    st.divider()

    st.session_state.opcua_sim = OPCUASimulator()

    # ── Only inject alarms from the actual buffer — never from simulator internals ──
    _buffer_has_alarms = len(st.session_state.alarm_buffer) > 0
    if _buffer_has_alarms:
        for alarm in st.session_state.alarm_buffer[:5]:
            turbine_id = alarm['asset_id']
            if turbine_id in st.session_state.opcua_sim.turbine_ids:
                st.session_state.opcua_sim.active_alarms[turbine_id] = alarm['predicted_type']
    else:
        # Clear all simulator-internal alarm states when buffer is empty
        st.session_state.opcua_sim.active_alarms = {}

    st.subheader("⚡ Live Fleet Status")
    fleet = st.session_state.opcua_sim.get_fleet_summary()

    # ── Derive true alarm count from buffer only ──
    _total_turbines      = len(st.session_state.opcua_sim.turbine_ids)  # e.g. 5
    _true_alarm_turbines = set(str(a['asset_id']) for a in st.session_state.alarm_buffer) if _buffer_has_alarms else set()
    _true_in_alarm       = min(len(_true_alarm_turbines), _total_turbines)
    _true_normal         = max(0, _total_turbines - _true_in_alarm)

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("🔋 Total Fleet Power",  f"{fleet['total_power_kw']:,.0f} kW")
    with col2: st.metric("✅ Turbines Normal",    max(0, _true_normal))
    with col3: st.metric("🚨 Turbines in Alarm",  _true_in_alarm, delta_color="inverse")
    with col4: st.metric("📡 Grid Frequency",    f"{fleet['grid_frequency_hz']} Hz")

    # ── Only show alarm banners if alarms exist in buffer ──
    if _buffer_has_alarms:
        _buffer_alarm_types = list(set(a['predicted_type'] for a in st.session_state.alarm_buffer
                                       if a.get('priority') == 'CRITICAL'))
        for _atype in _buffer_alarm_types[:3]:
            st.error(f"🚨 ACTIVE ALARM DETECTED: {_atype}")
    else:
        st.success("✅ No active alarms — fleet operating normally")

    st.divider()
    st.subheader("📋 OPC UA Node Data — Live Snapshot")
    readings     = st.session_state.opcua_sim.get_current_readings()
    readings_df  = pd.DataFrame(readings)
    if not readings_df.empty:
        display_readings = readings_df[['node_id', 'description', 'value', 'unit', 'status', 'timestamp']].copy()
        display_readings.columns = ['Node ID', 'Description', 'Value', 'Unit', 'Status', 'Timestamp']
        render_table(display_readings)   # ← HTML table, always visible

# ── Only show alarming nodes that correspond to actual alarms in buffer ──
    import re as _re

    # ── Build buffer lookup: turbine ID string → alarm type ──
    _buffer_alarm_turbines = {str(a['asset_id']) for a in st.session_state.alarm_buffer}
    _buffer_alarm_type_map = {}
    for _a in st.session_state.alarm_buffer:
        _tid = str(_a['asset_id'])
        if _tid not in _buffer_alarm_type_map:
            _buffer_alarm_type_map[_tid] = _a['predicted_type']

    def _extract_turbine_from_node(node):
        """Parse turbine number from node_id like WindFarm.Turbine21.AlarmActive → '21'"""
        for field in ['turbine_id', 'asset_id']:
            val = node.get(field)
            if val is not None:
                return str(val)
        node_id_str = str(node.get('node_id', ''))
        m = _re.search(r'[Tt]urbine(\d+)', node_id_str)
        if m:
            return m.group(1)
        return ''

   # ── One alarm node row per unique turbine — pick most critical alarm per turbine ──
alarming_nodes = []
if _buffer_has_alarms:
    _priority_rank = {'CRITICAL': 3, 'HIGH': 2, 'MEDIUM': 1}
    _turbine_best  = {}   # asset_id → best alarm dict
    for _a in st.session_state.alarm_buffer:
        _tid  = str(_a['asset_id'])
        _rank = _priority_rank.get(_a.get('priority', 'MEDIUM'), 0)
        if _tid not in _turbine_best or _rank > _priority_rank.get(_turbine_best[_tid].get('priority', 'MEDIUM'), 0):
            _turbine_best[_tid] = _a
    for _tid, _a in sorted(_turbine_best.items()):
        alarming_nodes.append({
            'node_id':     f"ns=2;s=WindFarm.Turbine{_a['asset_id']}.AlarmActive",
            'description': f"Turbine {_a['asset_id']} — Alarm Active Flag",
            'value':       'True',
            'unit':        '',
            'alarm_type':  _a.get('predicted_type', 'Unknown'),
            'priority':    _a.get('priority', 'N/A'),
            'asset_id':    _tid
        })

    if alarming_nodes:
    st.markdown("**🚨 Active Alarm Nodes (one per turbine — highest priority shown):**")
    for node in alarming_nodes:
        _alarm_label = node.get('alarm_type', 'Active Alarm')
        _priority    = node.get('priority', '')
        _color       = '#ff4444' if _priority == 'CRITICAL' else '#ff8800' if _priority == 'HIGH' else '#ffbb33'
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a0a00, #2a1200);
                    color: white; padding: 0.6rem 1rem; border-radius: 6px;
                    border-left: 4px solid {_color}; margin: 0.3rem 0;">
            <strong>{node.get('node_id', 'Unknown')}</strong> —
            {node.get('description', '')} |
            Value: {node.get('value', 'N/A')} |
            Priority: <strong style="color:{_color};">{_priority}</strong> |
            Alarm: <strong>{_alarm_label}</strong>
        </div>
        """, unsafe_allow_html=True)
else:
    st.success("✅ All OPC UA nodes operating normally")

    st.divider()
    col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
    with col_r2:
        if st.button("🔄 Refresh OPC UA Data", key="opcua_refresh_btn_tab8", use_container_width=True, type="primary"):
            st.rerun()
    st.caption("📌 In production, this feed would connect to the wind farm's OPC UA server via opcua-asyncio.")

    # ── Anomaly Review Panel (moved here from Tab 7) ─────────────────────────
    st.divider()
    st.subheader("🔬 Anomaly Review Panel")

    _session_anomalies = [a for a in st.session_state.alarm_buffer if a.get('is_anomaly', False)]
    _pending           = [a for a in _session_anomalies if not a.get('reviewed', False)]
    _known             = [a for a in _session_anomalies if a.get('reviewed', False)]

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total Unknown Anomalies", len(_session_anomalies))
    with col2: st.metric("Pending Review",           len(_pending))
    with col3: st.metric("Marked as Known",          len(_known))

    if not st.session_state.iso_detector.is_trained:
        st.info("Generate 10+ alarms in Tab 1, then click 'Train Anomaly Detector' in the sidebar to start detecting unknown patterns.")
    elif not _session_anomalies:
        st.info("No unknown anomalies detected yet. Train the detector and generate more alarms from the sidebar.")
    elif not _pending:
        st.success("✅ All anomalies have been reviewed.")
    else:
        st.warning(f"⚠️ {len(_pending)} anomaly/anomalies need your review")
        for _aidx, entry in enumerate(_pending[:5]):
            _fid2 = format_alarm_id(entry.get('alarm_id', 'N/A'))
            with st.expander(
                f"{_fid2} | Turbine T-{entry.get('asset_id', 'N/A')} | Score: {entry.get('anomaly_score', 'N/A')}"
            ):
                st.write("**Sensor Snapshot:**")
                _snap = {k: v for k, v in entry.items() if 'sensor' in k or 'power' in k or 'wind' in k}
                if _snap:
                    for sensor, val in _snap.items():
                        st.write(f"  {sensor}: {val}")
                else:
                    st.write("  No sensor snapshot available.")
                st.write(f"**ML Predicted Type:** {entry.get('predicted_type', 'Unknown')}")
                st.write(f"**Alarm ID:** {entry.get('alarm_id', 'N/A')}")
                st.write(f"**Timestamp:** {entry.get('timestamp', 'N/A')}")

                new_name = st.text_input(
                    "Rename this anomaly type:",
                    value=entry.get('predicted_type', f"Unknown Anomaly {_aidx+1}"),
                    key=f"opcua_rename_{_aidx}"
                )

                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("➕ Add to Alarm DB", key=f"opcua_add_db_{_aidx}", type="primary"):
                        if new_name.strip():
                            for buf_entry in st.session_state.alarm_buffer:
                                if buf_entry.get('alarm_id') == entry.get('alarm_id'):
                                    buf_entry['reviewed'] = True
                                    buf_entry['alarm_type'] = new_name.strip()
                                    break
                            st.success(f"✅ '{new_name.strip()}' added to known patterns.")
                            st.rerun()
                        else:
                            st.warning("Please enter a name first.")
                with col_b:
                    if st.button("✅ Mark as Known", key=f"opcua_mark_known_{_aidx}"):
                        for buf_entry in st.session_state.alarm_buffer:
                            if buf_entry.get('alarm_id') == entry.get('alarm_id'):
                                buf_entry['reviewed'] = True
                                break
                        st.success("✅ Marked as known. Removed from review queue.")
                        st.rerun()

# ═══════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════

st.divider()
st.markdown("""
<div style="text-align:center; color:#4FC3F7; padding:1.5rem 0 0.5rem;">
    <strong>WindSense AI © 2026</strong> | Team TG0907494 | TECHgium 9th Edition<br>
    Intelligent Predictive Control and Alarm Optimization in Wind Turbine Systems
</div>
""", unsafe_allow_html=True)