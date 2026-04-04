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

# ── Single unified CSS block ─────────────────────────────────────────────────
st.markdown("""
<style>
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        outline: none !important;
        box-shadow: none !important;
        -webkit-box-shadow: none !important;
        border: 1px solid #1E3A4A !important;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus {
        outline: none !important;
        box-shadow: 0 0 0 2px rgba(0, 201, 177, 0.25) !important;
        border: 1px solid #00C9B1 !important;
    }

    [data-testid="stWidgetLabel"] { border: none !important; box-shadow: none !important; }
    div[data-baseweb="input"] { border: none !important; box-shadow: none !important; }
    div[data-baseweb="input"] > div { border: none !important; box-shadow: none !important; }
    div[data-baseweb="textarea"] { border: none !important; box-shadow: none !important; }
    div[data-baseweb="textarea"] > div { border: none !important; box-shadow: none !important; }
    div[data-baseweb="select"] { border: none !important; box-shadow: none !important; }
    div[data-baseweb="select"] > div { border: none !important; }

    [data-testid="stSidebarNav"] {display: none !important;}
    .stApp { background-color: #0D1B2A; color: #E8F4FD; }
    .main .block-container { background-color: #0D1B2A; padding-top: 1rem; }
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
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D1B2A 0%, #1a2a3a 100%);
        border-right: 1px solid #00C9B1;
    }
    [data-testid="stSidebar"] * { color: #E8F4FD !important; }
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
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; color: #00C9B1 !important; }
    [data-testid="stMetricLabel"] { font-size: 0.85rem !important; color: #4FC3F7 !important; }
    [data-testid="stMetricDelta"] { font-size: 0.75rem !important; }
    .stButton > button {
        background: linear-gradient(135deg, #004D40, #00796B);
        color: white !important;
        border: 1px solid #00C9B1;
        border-radius: 6px;
        font-weight: 600;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #00796B, #00C9B1);
        border: 1px solid #4FC3F7;
    }
    .stTextInput input, .stSelectbox div, .stTextArea textarea {
        background-color: #1a2a3a !important;
        border: 1px solid #00C9B1 !important;
        color: #E8F4FD !important;
        border-radius: 6px;
    }
    .streamlit-expanderHeader {
        background-color: #1a2a3a !important;
        color: #00C9B1 !important;
        border: 1px solid #2a3a4a;
        border-radius: 6px;
    }
    hr { border-color: #2a3a4a !important; }
    .dmaic-measure [data-testid="stMetricValue"] {
        font-size: 1.0rem !important;
        white-space: normal !important;
        word-break: break-word !important;
    }
    .dmaic-measure [data-testid="stMetricLabel"] { font-size: 0.75rem !important; }

    /* ── Dataframe visibility fix ── */
    [role="gridcell"] {
        color: #E8F4FD !important;
        background-color: #112233 !important;
    }
    [role="columnheader"] {
        color: #00C9B1 !important;
        background-color: #0D1B2A !important;
    }
    [data-testid="stDataFrame"] div[class*="dvn-scroller"] {
        background-color: #112233 !important;
    }

    /* ── Sidebar collapse button fix ── */
    [data-testid="collapsedControl"] {
        color: #00C9B1 !important;
    }
    button[kind="header"] svg {
        fill: #00C9B1 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_PATH  = os.path.join(os.path.dirname(os.path.abspath('app.py')), '')
DATA_PATH  = os.path.join(os.path.dirname(os.path.abspath('app.py')), 'data') + os.sep
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath('app.py')), 'models') + os.sep
OUTPUT_PATH = DATA_PATH
ACK_FILE   = os.path.join(os.path.dirname(os.path.abspath('app.py')), 'data', 'acknowledgments.json')

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
    return "http://localhost:8501"

DASHBOARD_URL = get_dashboard_url()

# ── Auth guard ───────────────────────────────────────────────────────────────
# ACK links must be checked BEFORE the auth guard so unauthenticated
# users clicking email/WhatsApp links are not bounced to login.
query_params = st.query_params

if 'ack' in query_params:
    alarm_id = query_params['ack']
    channel  = query_params.get('channel', 'email')
    existing_acks = load_acknowledgments()
    if alarm_id in existing_acks:
        prev_ack = existing_acks[alarm_id]
        st.markdown(f"""
        <div style="text-align: center; padding: 50px;">
            <h1 style="color: #FF8800;">⚠️ Already Acknowledged</h1>
            <p style="font-size: 1.5rem; margin: 20px 0;">
                Alarm <strong>{alarm_id}</strong> was already acknowledged.
            </p>
            <p style="color: #666;">
                Previously acknowledged at: {prev_ack.get('time', prev_ack.get('ack_time', 'Unknown'))}
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        ack_data = {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'method': f'{channel}_link',
            'channel': channel,
            'alarm_id': alarm_id
        }
        if save_acknowledgment(alarm_id, ack_data):
            st.markdown(f"""
            <div style="text-align: center; padding: 50px;">
                <h1 style="color: #4CAF50;">✅ Acknowledgment Successful!</h1>
                <p style="font-size: 1.5rem; margin: 20px 0;">
                    Alarm <strong>{alarm_id}</strong> has been acknowledged.
                </p>
                <p style="color: #666;">
                    Acknowledged at: {ack_data['time']}<br>
                    This alarm has been logged in the system.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.balloons()
        else:
            st.error("❌ Failed to save acknowledgment.")
    st.stop()

if not st.session_state.get('authenticated', False) and 'ack' not in st.query_params:
    st.switch_page('pages/login.py')

if not st.session_state.get('session_initialized', False):
    try:
        with open(ACK_FILE, 'w') as f:
            json.dump({}, f)
    except Exception:
        pass
    st.session_state.acknowledged_alarms = {}
    st.session_state.session_initialized = True
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
        'primary':    {'name': 'Divya',        'role': 'Control Systems Engineer',  'email': 'divyajay.1612@gmail.com',      'phone': '+918778838055'},
        'secondary':  {'name': 'Sarah Johnson', 'role': 'Senior Engineer',           'email': 'sarah.j@windfarm.com',         'phone': '+1234567891'},
        'management': {'name': 'Mike Davis',    'role': 'Engineering Manager',       'email': 'mike.d@windfarm.com',          'phone': '+1234567892'},
        'escalation_time': 30
    },
    'Grid Frequency Deviation': {
        'primary':    {'name': 'Emily Chen',    'role': 'Grid Integration Specialist','email': 'emily.c@windfarm.com',         'phone': '+1234567893'},
        'secondary':  {'name': 'David Wilson',  'role': 'Electrical Engineer',        'email': 'david.w@windfarm.com',         'phone': '+1234567894'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager',         'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 20
    },
    'Extended Grid Outage': {
        'primary':    {'name': 'Robert Taylor',  'role': 'Site Manager',             'email': 'robert.t@windfarm.com',        'phone': '+1234567896'},
        'secondary':  {'name': 'Jennifer Lee',   'role': 'Operations Supervisor',    'email': 'jennifer.l@windfarm.com',      'phone': '+1234567897'},
        'management': {'name': 'Lisa Anderson',  'role': 'Operations Manager',       'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 15
    },
    'Emergency Brake Activation': {
        'primary':    {'name': 'Carlos Rodriguez','role': 'Mechanical Technician',   'email': 'carlos.r@windfarm.com',        'phone': '+1234567898'},
        'secondary':  {'name': 'Anna Martinez',  'role': 'Senior Technician',        'email': 'anna.m@windfarm.com',          'phone': '+1234567899'},
        'management': {'name': 'Mike Davis',     'role': 'Engineering Manager',      'email': 'mike.d@windfarm.com',          'phone': '+1234567892'},
        'escalation_time': 25
    },
    'Generator Bearing Overheating': {
        'primary':    {'name': 'Aarif',          'role': 'Mechanical Technician',    'email': 'muhammadhaarif2000@gmail.com', 'phone': '+919123516325'},
        'secondary':  {'name': 'Anna Martinez',  'role': 'Senior Technician',        'email': 'anna.m@windfarm.com',          'phone': '+1234567899'},
        'management': {'name': 'Mike Davis',     'role': 'Engineering Manager',      'email': 'mike.d@windfarm.com',          'phone': '+1234567892'},
        'escalation_time': 20
    },
    'Hydraulic Oil Contamination': {
        'primary':    {'name': 'Anna Martinez',  'role': 'Senior Technician',        'email': 'anna.m@windfarm.com',          'phone': '+1234567899'},
        'secondary':  {'name': 'Carlos Rodriguez','role': 'Mechanical Technician',   'email': 'carlos.r@windfarm.com',        'phone': '+1234567898'},
        'management': {'name': 'Mike Davis',     'role': 'Engineering Manager',      'email': 'mike.d@windfarm.com',          'phone': '+1234567892'},
        'escalation_time': 35
    },
    'Converter Circuit Fault': {
        'primary':    {'name': 'David Wilson',   'role': 'Electrical Engineer',      'email': 'david.w@windfarm.com',         'phone': '+1234567894'},
        'secondary':  {'name': 'Emily Chen',     'role': 'Grid Integration Specialist','email': 'emily.c@windfarm.com',       'phone': '+1234567893'},
        'management': {'name': 'Lisa Anderson',  'role': 'Operations Manager',       'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 25
    },
    'Yaw System Hydraulic Fault': {
        'primary':    {'name': 'Aparajithaa',    'role': 'Yaw Systems Specialist',   'email': 'ts.aparajithaa@gmail.com',     'phone': '+919284743112'},
        'secondary':  {'name': 'Amanda White',   'role': 'Hydraulic Engineer',       'email': 'amanda.w@windfarm.com',        'phone': '+1234567911'},
        'management': {'name': 'Mike Davis',     'role': 'Engineering Manager',      'email': 'mike.d@windfarm.com',          'phone': '+1234567892'},
        'escalation_time': 480
    },
    'Pitch System Hydraulic Fault': {
        'primary':    {'name': 'Diego Lopez',    'role': 'Pitch System Engineer',    'email': 'diego.l@windfarm.com',         'phone': '+1234567912'},
        'secondary':  {'name': 'Rachel Green',   'role': 'Blade Specialist',         'email': 'rachel.g@windfarm.com',        'phone': '+1234567913'},
        'management': {'name': 'Mike Davis',     'role': 'Engineering Manager',      'email': 'mike.d@windfarm.com',          'phone': '+1234567892'},
        'escalation_time': 480
    },
    'Power Electronics Failure': {
        'primary':    {'name': 'Jack Williams',  'role': 'Power Systems Engineer',   'email': 'jack.w@windfarm.com',          'phone': '+1234567920'},
        'secondary':  {'name': 'Emma Davis',     'role': 'Electronics Tech',         'email': 'emma.d@windfarm.com',          'phone': '+1234567921'},
        'management': {'name': 'Lisa Anderson',  'role': 'Operations Manager',       'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 120
    },
    'Transformer Oil Temperature High': {
        'primary':    {'name': 'Kevin Murphy',   'role': 'Transformer Specialist',   'email': 'kevin.m@windfarm.com',         'phone': '+1234567922'},
        'secondary':  {'name': 'Laura Johnson',  'role': 'Oil Analysis Tech',        'email': 'laura.j@windfarm.com',         'phone': '+1234567923'},
        'management': {'name': 'Lisa Anderson',  'role': 'Operations Manager',       'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 120
    },
    'Hydraulic Filter Clogged': {
        'primary':    {'name': 'Marcus Lee',     'role': 'Hydraulic Technician',     'email': 'marcus.l@windfarm.com',        'phone': '+1234567924'},
        'secondary':  {'name': 'Patricia King',  'role': 'Maintenance Supervisor',   'email': 'patricia.k@windfarm.com',      'phone': '+1234567925'},
        'management': {'name': 'Lisa Anderson',  'role': 'Operations Manager',       'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 480
    },
    'Generator Winding Temperature High': {
        'primary':    {'name': 'Nathan Scott',   'role': 'Generator Specialist',     'email': 'nathan.s@windfarm.com',        'phone': '+1234567926'},
        'secondary':  {'name': 'Quinn Roberts',  'role': 'Electrical Engineer',      'email': 'quinn.r@windfarm.com',         'phone': '+1234567927'},
        'management': {'name': 'Mike Davis',     'role': 'Engineering Manager',      'email': 'mike.d@windfarm.com',          'phone': '+1234567892'},
        'escalation_time': 120
    },
    'Hydraulic Pressure Drop': {
        'primary':    {'name': 'Oscar Ramirez',  'role': 'Hydraulic Engineer',       'email': 'oscar.r@windfarm.com',         'phone': '+1234567928'},
        'secondary':  {'name': 'Tina Garcia',    'role': 'Systems Tech',             'email': 'tina.g@windfarm.com',          'phone': '+1234567929'},
        'management': {'name': 'Lisa Anderson',  'role': 'Operations Manager',       'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 480
    },
    'Momentary Grid Loss': {
        'primary':    {'name': 'Robert Taylor',  'role': 'Site Manager',             'email': 'robert.t@windfarm.com',        'phone': '+1234567896'},
        'secondary':  {'name': 'Jennifer Lee',   'role': 'Operations Supervisor',    'email': 'jennifer.l@windfarm.com',      'phone': '+1234567897'},
        'management': {'name': 'Lisa Anderson',  'role': 'Operations Manager',       'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 15
    },
    'Grid Voltage Fluctuation': {
        'primary':    {'name': 'Emily Chen',     'role': 'Grid Integration Specialist','email': 'emily.c@windfarm.com',       'phone': '+1234567893'},
        'secondary':  {'name': 'David Wilson',   'role': 'Electrical Engineer',      'email': 'david.w@windfarm.com',         'phone': '+1234567894'},
        'management': {'name': 'Lisa Anderson',  'role': 'Operations Manager',       'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 20
    },
    'Safety System Activation': {
        'primary':    {'name': 'Carlos Rodriguez','role': 'Mechanical Technician',   'email': 'carlos.r@windfarm.com',        'phone': '+1234567898'},
        'secondary':  {'name': 'Anna Martinez',  'role': 'Senior Technician',        'email': 'anna.m@windfarm.com',          'phone': '+1234567899'},
        'management': {'name': 'Mike Davis',     'role': 'Engineering Manager',      'email': 'mike.d@windfarm.com',          'phone': '+1234567892'},
        'escalation_time': 20
    },
    'Overspeed Protection Triggered': {
        'primary':    {'name': 'Carlos Rodriguez','role': 'Mechanical Technician',   'email': 'carlos.r@windfarm.com',        'phone': '+1234567898'},
        'secondary':  {'name': 'Anna Martinez',  'role': 'Senior Technician',        'email': 'anna.m@windfarm.com',          'phone': '+1234567899'},
        'management': {'name': 'Mike Davis',     'role': 'Engineering Manager',      'email': 'mike.d@windfarm.com',          'phone': '+1234567892'},
        'escalation_time': 20
    },
    'Hydraulic Valve Response Slow': {
        'primary':    {'name': 'Marcus Lee',     'role': 'Hydraulic Technician',     'email': 'marcus.l@windfarm.com',        'phone': '+1234567924'},
        'secondary':  {'name': 'Patricia King',  'role': 'Maintenance Supervisor',   'email': 'patricia.k@windfarm.com',      'phone': '+1234567925'},
        'management': {'name': 'Lisa Anderson',  'role': 'Operations Manager',       'email': 'lisa.a@windfarm.com',          'phone': '+1234567895'},
        'escalation_time': 480
    },
    'DEFAULT': {
        'primary':    {'name': 'Operations Center','role': 'Control Room',           'email': 'ops@windfarm.com',             'phone': '+1234567800'},
        'secondary':  {'name': 'Duty Engineer',  'role': 'On-call Engineer',         'email': 'duty@windfarm.com',            'phone': '+1234567801'},
        'management': {'name': 'Operations Manager','role': 'Manager',               'email': 'manager@windfarm.com',         'phone': '+1234567802'},
        'escalation_time': 30
    }
}

# ── Notification functions ───────────────────────────────────────────────────
def send_email_notification(recipient_email, recipient_name, alarm_type, turbine_id, severity, alarm_id):
    try:
        sender_email = "windsenseada@gmail.com"
        msg = MIMEMultipart()
        msg['From']    = sender_email
        msg['To']      = recipient_email
        msg['Subject'] = f"🚨 {severity} ALARM: {alarm_type} - Turbine {turbine_id}"
        aack_url = f"https://windsense-ai.streamlit.app/?ack={alarm_id}&channel=email"
        body = f"""
        <html><body style="font-family: Arial, sans-serif;">
            <div style="background: linear-gradient(135deg, #0D1B2A 0%, #1E3A5F 100%); padding: 20px; color: white;">
                <h2>🚨 CRITICAL ALARM NOTIFICATION</h2>
            </div>
            <div style="padding: 20px; background-color: #112233;">
                <p style="color:#D0D8E0;">Dear {recipient_name},</p>
                <p style="color:#D0D8E0;">A <strong style="color: #ff4444;">{severity}</strong> alarm has been detected.</p>
                <div style="background-color: #1E3A5F; padding: 15px; border-left: 4px solid #ff4444; margin: 20px 0;">
                    <p style="color:#D0D8E0;"><strong>Alarm ID:</strong> {alarm_id}</p>
                    <p style="color:#D0D8E0;"><strong>Alarm Type:</strong> {alarm_type}</p>
                    <p style="color:#D0D8E0;"><strong>Turbine:</strong> T-{turbine_id}</p>
                    <p style="color:#D0D8E0;"><strong>Severity:</strong> {severity}</p>
                    <p style="color:#D0D8E0;"><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{ack_url}" style="background-color: #00C9B1; color: white; padding: 12px 30px;
                       text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                        ✅ ACKNOWLEDGE THIS ALARM
                    </a>
                </div>
            </div>
        </body></html>
        """
        msg.attach(MIMEText(body, 'html'))
        try:
            _smtp = smtplib.SMTP('smtp.gmail.com', 587, timeout=5)
            _smtp.ehlo()
            _smtp.starttls()
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
                'status': 'QUEUED 🕐 (will send when online)'
            })
            return False
    except Exception:
        return False

def send_sms_notification(phone_number, recipient_name, alarm_type, turbine_id, severity, alarm_id):
    try:
        from utils.sms_sender import send_real_sms

        ack_url = f"https://windsense-ai.streamlit.app/?ack={alarm_id}&channel=whatsapp"
        message_body = (
            f"WINDSENSE AI ALERT\n"
            f"Severity: {severity}\n"
            f"Alarm: {alarm_type}\n"
            f"Turbine: T-{turbine_id}\n"
            f"ID: {alarm_id}\n"
            f"Ack: {ack_url}"
        )
        success, result = send_real_sms(phone_number, message_body)
        if "notification_log" not in st.session_state:
            st.session_state.notification_log = []
        st.session_state.notification_log.append({
            "time": datetime.now(), "type": "WHATSAPP",
            "recipient": f"{recipient_name} ({phone_number})",
            "alarm_id": alarm_id, "alarm_type": alarm_type,
            "status": "SENT ✓" if success else f"FAILED: {result}",
        })
        return success
    except Exception as e:
        if "notification_log" not in st.session_state:
            st.session_state.notification_log = []
        st.session_state.notification_log.append({
            "time": datetime.now(), "type": "WHATSAPP",
            "recipient": f"{recipient_name} ({phone_number})",
            "alarm_id": alarm_id, "alarm_type": alarm_type,
            "status": f"EXCEPTION: {e}",
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
        alarm_type = alarm_data.get('type', '')
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
                    'escalated_to': mgmt['name'],
                    'reason': f'No acknowledgment after {escalation_time} minutes'
                }

# ── Historical / ML data loaders ─────────────────────────────────────────────
@st.cache_resource
def load_ml_model():
    try:
        import gzip
        model_gz = MODEL_PATH + 'windsense_rf_model.pkl.gz'
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
    except Exception as e:
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
        historical_alarms = pd.read_csv(DATA_PATH + 'top_50_unique_detailed_alarms.csv')
        alarm_episodes = pd.read_csv(DATA_PATH + 'alarm_episodes_with_faults.csv')
        detailed_episodes = pd.read_csv(DATA_PATH + 'detailed_classified_alarm_episodes.csv')
        historical_alarms.columns = [c.strip() for c in historical_alarms.columns]
        if 'Rank' not in historical_alarms.columns:
            historical_alarms.insert(0, 'Rank', range(1, len(historical_alarms) + 1))
        dmaic_file = DATA_PATH + 'DMAIC_Analysis_19_Alarms.csv'
        if os.path.exists(dmaic_file):
            dmaic_data = pd.read_csv(dmaic_file)
        else:
            dmaic_data = None
        return historical_alarms, alarm_episodes, detailed_episodes, dmaic_data
    except Exception as e:
        return None, None, None, None

historical_alarms, alarm_episodes, detailed_episodes, dmaic_data = load_historical_data()
ml_model, feature_names, model_metadata = load_ml_model()
simulation_data = load_simulation_data()

# ── Simulator class ───────────────────────────────────────────────────────────
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
        turbine_id  = np.random.choice([10, 11, 13, 21])
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
if 'simulator'         not in st.session_state:
    st.session_state.simulator         = RealtimeAlarmSimulator()
if 'alarm_buffer'      not in st.session_state:
    st.session_state.alarm_buffer      = []
if 'notifications'     not in st.session_state:
    st.session_state.notifications     = []
if 'acknowledged_alarms' not in st.session_state:
    st.session_state.acknowledged_alarms = load_acknowledgments()
if 'anomaly_detector'  not in st.session_state:
    st.session_state.anomaly_detector  = AnomalyDetector(contamination=0.1)

def clean_orphaned_acknowledgments():
    if 'alarm_buffer' in st.session_state and 'acknowledged_alarms' in st.session_state:
        active_alarm_ids = {a['alarm_id'] for a in st.session_state.alarm_buffer}
        cleaned_acks = {}
        for aid, ack_data in st.session_state.acknowledged_alarms.items():
            if ack_data.get('method') == 'email_link' or aid in active_alarm_ids:
                cleaned_acks[aid] = ack_data
        st.session_state.acknowledged_alarms = cleaned_acks
        try:
            with open(ACK_FILE, 'w') as f:
                json.dump(cleaned_acks, f, indent=2)
        except Exception:
            pass

# ── Elimination strategies ────────────────────────────────────────────────────
FALLBACK_ELIMINATION_STRATEGIES = {
    'Main Controller Fault':            ['Update controller firmware to latest stable version', 'Implement auto-reset logic to reduce manual intervention', 'Install redundant controller for failover capability', 'Deploy grid stability monitoring for early warning'],
    'Grid Frequency Deviation':         ['Install Battery Energy Storage System (BESS) for frequency stabilization', 'Implement faster reconnection logic to reduce downtime', 'Coordinate with utility provider and negotiate grid stability SLA', 'Add frequency ride-through capability for wider operating range'],
    'Extended Grid Outage':             ['Install diesel generator backup for black start capability', 'Negotiate advance notice for planned maintenance outages', 'Add redundant grid connection point to reduce outage frequency', 'Implement islanding capability with BESS for independent operation'],
    'Emergency Brake Activation':       ['Upgrade to condition-based brake monitoring system', 'Implement predictive maintenance to prevent false triggers', 'Install redundant sensors to verify actual overspeed conditions', 'Perform quarterly brake system calibration to reduce false alarms'],
    'Generator Bearing Overheating':    ['Install online bearing monitoring (vibration + temperature sensors)', 'Upgrade to automatic lubrication systems', 'Implement condition-based lubrication via oil analysis', 'Add redundant cooling fans for backup cooling capability'],
    'Hydraulic Oil Contamination':      ['Install high-efficiency filtration system with contamination sensors', 'Implement real-time oil quality monitoring with automatic alerts', 'Schedule regular oil analysis and flush cycles', 'Upgrade seals and fittings to prevent external contamination ingress'],
    'Converter Circuit Fault':          ['Replace aging IGBT modules with latest generation components', 'Implement thermal management improvements for converter cooling', 'Install online converter health monitoring system', 'Perform preventive capacitor replacement on schedule'],
    'Momentary Grid Loss':              ['Upgrade to low voltage ride-through (LVRT) capability', 'Implement auto-restart sequence to reduce recovery time to 15 minutes', 'Adjust protection trip settings for wider voltage tolerance', 'Install voltage stabilizers at grid connection point'],
    'Grid Voltage Fluctuation':         ['Install Static VAR Compensator (SVC) for voltage stabilization', 'Upgrade transformer with automatic tap changer', 'Implement reactive power control via inverter settings', 'Coordinate with utility on voltage regulation protocols'],
    'Safety System Activation':         ['Perform comprehensive safety sensor calibration and audit', 'Upgrade safety PLC to latest firmware with improved logic', 'Implement diagnostic mode to differentiate true vs false triggers', 'Review and optimize safety trip thresholds to reduce false activations'],
    'Overspeed Protection Triggered':   ['Calibrate rotor speed sensors and replace if drifting', 'Optimize pitch control response for faster regulation', 'Implement multi-sensor voting logic to prevent false trips', 'Review and adjust overspeed threshold settings'],
    'Yaw System Hydraulic Fault':       ['Replace worn yaw hydraulic seals and actuators', 'Install yaw hydraulic pressure monitoring with automated alerts', 'Implement scheduled hydraulic fluid replacement program', 'Add redundant yaw position sensors for fault detection'],
    'Pitch System Hydraulic Fault':     ['Replace pitch hydraulic cylinders and seals on schedule', 'Install real-time pitch pressure monitoring system', 'Implement emergency battery backup for pitch control', 'Perform quarterly pitch system hydraulic inspection'],
    'Power Electronics Failure':        ['Implement thermal monitoring on all power electronic components', 'Replace aging capacitors and IGBT modules preventively', 'Improve converter cabinet cooling and ventilation', 'Deploy online insulation resistance monitoring'],
    'Transformer Oil Temperature High': ['Clean and inspect transformer cooling radiators', 'Upgrade cooling fans and implement variable speed control', 'Install online dissolved gas analysis (DGA) monitoring', 'Perform power factor testing and insulation checks'],
    'Hydraulic Filter Clogged':         ['Implement differential pressure monitoring across all filters', 'Reduce filter replacement intervals based on contamination levels', 'Upgrade to higher-capacity filter elements', 'Install oil contamination particle counter for predictive maintenance'],
    'Generator Winding Temperature High':['Inspect and clean generator air gaps and cooling ducts', 'Replace damaged winding insulation and re-varnish', 'Install additional temperature sensors across all winding phases', 'Implement load shedding logic when temperature rises above threshold'],
    'Hydraulic Pressure Drop':          ['Inspect all hydraulic lines and connections for leaks', 'Replace worn hydraulic pump components or full pump assembly', 'Install pressure transducers on all critical hydraulic circuits', 'Implement automatic shutdown logic on pressure drop detection'],
    'Hydraulic Valve Response Slow':    ['Flush and replace hydraulic fluid to restore viscosity', 'Clean or replace slow-responding solenoid valves', 'Install valve response time monitoring sensors', 'Implement valve performance trending and predictive replacement schedule']
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
                    'primary_cause':      dmaic_entry.get('analyze', {}).get('root_cause', 'Analysis in progress'),
                    'contributing_factors': dmaic_entry.get('analyze', {}).get('contributing', []),
                    'diagnostic_sensors': ['power_30_avg', 'sensor_11_avg', 'sensor_12_avg'],
                    'threshold_conditions': {}
                }
        else:
            self.root_cause_database = {
                'Main Controller Fault': {
                    'primary_cause': 'Software instability during grid fluctuations',
                    'contributing_factors': ['Grid frequency deviation triggers protection mode', 'Requires manual intervention and reset', 'Affects all turbines equally'],
                    'diagnostic_sensors': ['power_30_avg', 'sensor_18_avg'],
                    'threshold_conditions': {'power_30_avg': '<100', 'grid_frequency': '±0.5 Hz'}
                },
                'Grid Frequency Deviation': {
                    'primary_cause': 'External grid instability from utility provider',
                    'contributing_factors': ['Poor grid infrastructure in region', 'Delayed reconnection protocols', 'No local frequency stabilization'],
                    'diagnostic_sensors': ['power_30_avg', 'wind_speed_3_avg'],
                    'threshold_conditions': {'grid_frequency': '<49.5 or >50.5 Hz'}
                },
            }

    def analyze(self, alarm_type, sensor_data):
        if alarm_type not in self.root_cause_database:
            return {
                'alarm_type': alarm_type,
                'primary_cause': 'Diagnostic analysis in progress - sensor patterns being evaluated',
                'contributing_factors': ['Requires additional sensor data collection'],
                'sensor_anomalies': [],
                'confidence': 50,
                'recommended_actions': get_elimination_strategy(alarm_type)
            }
        rca_data = self.root_cause_database[alarm_type]
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
            'alarm_type': alarm_type,
            'primary_cause': rca_data['primary_cause'],
            'contributing_factors': rca_data['contributing_factors'],
            'sensor_anomalies': sensor_anomalies,
            'confidence': confidence,
            'recommended_actions': get_elimination_strategy(alarm_type)
        }

if 'rca_engine'    not in st.session_state:
    st.session_state.rca_engine    = RootCauseEngine()
if 'iso_detector'  not in st.session_state:
    st.session_state.iso_detector  = IsolationForestDetector()

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
        asset_id = alarm_data.get('asset_id', 0)
        try:
            turbine_id_num = int(asset_id) if str(asset_id).isdigit() else 0
        except Exception:
            turbine_id_num = 0
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
        X = np.array([feature_vector])
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
        'Pitch System Fault':           'Mechanical - Blade Systems',
        'Yaw System Fault':             'Mechanical - Nacelle Systems'
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

def train_isolation_forest():
    if len(st.session_state.alarm_buffer) < 10:
        return False
    sensors   = ['sensor_11_avg', 'sensor_12_avg', 'sensor_41_avg', 'power_30_avg', 'wind_speed_3_avg']
    df        = pd.DataFrame(st.session_state.alarm_buffer)
    available = [s for s in sensors if s in df.columns]
    if not available:
        return False
    X   = df[available].fillna(0).values
    iso = IsolationForest(contamination=0.1, random_state=42)
    iso.fit(X)
    st.session_state.isolation_forest_model    = iso
    st.session_state.isolation_forest_trained  = True
    st.session_state.isolation_forest_features = available
    return True

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

            st.markdown("<span style='font-size:1.5rem; color:#00C9B1;'>≪ 🌀</span>", unsafe_allow_html=True)

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

    if st.session_state.iso_detector.is_trained:
        st.caption("🟢 Anomaly detector: ACTIVE")
    else:
        st.caption("🔴 Anomaly detector: not trained yet")

    st.divider()
    if st.button("🔁 Reconnect & Refresh", use_container_width=True):
        flush_queue()
        st.rerun()

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
        <span style="color: #00C9B1; font-weight: 700; font-size: 1rem;">
            🌀 WindSense AI — Live Classification Engine
        </span>
        <span style="color: #7FB9D4; font-size: 0.85rem; margin-left: 1rem;">
            Random Forest · 94.8% Accuracy · 19 Alarm Types · Real-time OPC UA Feed
        </span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("ℹ️ About this tab", expanded=False):
        st.markdown("**Real-Time Alarm Monitoring** classifies incoming alarms using the WindSense RF model. Generate alarms via the sidebar, view confidence tiers (🟢 High / 🟠 Moderate / 🟡 Low / 🔴 Anomaly), download the alarm log, and use the Critical Alarm Simulator to test live Email + WhatsApp notifications.")

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

        # ── Detailed Alarm Data ──────────────────────────────────────────────
        st.subheader("📋 Detailed Alarm Data")
        alarm_df       = pd.DataFrame(st.session_state.alarm_buffer)
        display_rows   = []
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
                flagged_type = "🔴 UNKNOWN ANOMALY — Isolation Forest Alert"
                flag_status  = "🔴 Unknown / New Pattern"
                anomaly_count += 1
                try:
                    save_anomaly_to_log(
                        row.get('alarm_id', 'N/A'), dict(row),
                        {'is_anomaly': True, 'anomaly_score': float(_score)}
                    )
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
        st.dataframe(display_df, use_container_width=True, height=400, hide_index=True)

        if anomaly_count > 0:
            st.error(f"🔴 {anomaly_count} UNKNOWN ANOMALY alarm(s) detected by Isolation Forest. Review in Tab 7.")
        if uncertain_count > 0:
            st.warning(f"⚠️ {uncertain_count} alarm(s) flagged as uncertain (confidence <70%). These require manual inspection.")

        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Alarm Log (CSV)", csv, "windsense_alarm_log.csv", "text/csv", use_container_width=True)

        # ── Anomaly Learning Loop ────────────────────────────────────────────
        anomaly_log = load_anomaly_log()
        unreviewed  = [a for a in anomaly_log if not a.get('reviewed', False)]

        if unreviewed:
            st.divider()
            st.subheader("🔍 Anomaly Review Queue")
            st.info(f"{len(unreviewed)} anomalous alarm(s) detected. Review and decide whether to add to known patterns.")
            for i, anomaly in enumerate(unreviewed[:5]):
                with st.expander(
                    f"🚨 {anomaly['alarm_id']} | "
                    f"Turbine T-{anomaly.get('asset_id', anomaly.get('turbine', 'N/A'))} | "
                    f"Score: {anomaly['anomaly_score']}",
                    expanded=False
                ):
                    st.write(f"**Type detected:** {anomaly.get('alarm_type', anomaly.get('predicted_type', 'N/A'))}")
                    st.write(f"**Time:** {anomaly.get('timestamp', anomaly.get('logged_at', 'N/A'))}")
                    st.write(f"**Reason:** {anomaly.get('reason', 'Flagged by Isolation Forest')}")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("✅ Add to Known", key=f"t1_add_{i}_{anomaly['alarm_id']}"):
                            mark_anomaly_reviewed(anomaly['alarm_id'], add_to_known=True)
                            st.success("Added to known patterns!")
                            st.rerun()
                    with col_no:
                        if st.button("❌ Dismiss", key=f"t1_dismiss_{i}_{anomaly['alarm_id']}"):
                            mark_anomaly_reviewed(anomaly['alarm_id'], add_to_known=False)
                            st.rerun()

    else:
        st.info("👈 Click 'Generate New Alarm' in the sidebar to start real-time monitoring")

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
                font=dict(color='#D0D8E0', size=11),
                xaxis=dict(gridcolor='#1E3A5F', linecolor='#1E3A5F', tickfont=dict(color='#8899AA')),
                yaxis=dict(gridcolor='#1E3A5F', linecolor='#1E3A5F', tickfont=dict(color='#8899AA'))
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
            fig.update_layout(
                height=400, paper_bgcolor='#0D1B2A', plot_bgcolor='#0D1B2A',
                font=dict(color='#D0D8E0', size=11),
                legend=dict(font=dict(color='#D0D8E0'))
            )
            st.plotly_chart(fig, use_container_width=True)

        # ── Priority / Turbine / Confidence Pie Row ──────────────────────────
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
                    labels=priority_counts.index, values=priority_counts.values,
                    hole=0.55,
                    marker=dict(colors=_chart_colors, line=dict(color='#060E17', width=2)),
                    textinfo='label+percent'
                ))
                fig_pie.add_annotation(
                    text=f"<b>{len(st.session_state.alarm_buffer)}</b><br>Total",
                    x=0.5, y=0.5, showarrow=False
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        with col_pie2:
            st.subheader("🌀 By Turbine")
            turbine_counts2 = alarm_df_pie['asset_id'].value_counts()
            fig_t = go.Figure(go.Pie(
                labels=[f"T-{t}" for t in turbine_counts2.index],
                values=turbine_counts2.values, hole=0.4
            ))
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
            st.plotly_chart(fig_c, use_container_width=True)

        # ── Root Cause Analysis ──────────────────────────────────────────────
        st.divider()
        st.subheader("🔍 Root Cause Analysis - Latest Alarm")
        latest_alarm = st.session_state.alarm_buffer[0]
        sensor_data  = {k: v for k, v in latest_alarm.items() if 'sensor' in k or 'power' in k or 'wind' in k}
        rca_result   = st.session_state.rca_engine.analyze(latest_alarm['predicted_type'], sensor_data)
        st.write(f"**🔍 Root Cause:** {rca_result['primary_cause']}")
        st.write(f"**Confidence:** {rca_result['confidence']}%")
        st.write("**Recommended Actions (Elimination Strategy):**")
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
            plot_df = sensor_df[['alarm_id', selected_sensor]].copy()
            plot_df = plot_df.dropna(subset=[selected_sensor]).tail(20)
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
        else:
            st.info("Sensor data not available in current alarm buffer.")

# ═══════════════════════════════════════════════════════════════════
# TAB 2 — ML MODEL & TRAINING
# ═══════════════════════════════════════════════════════════════════

with tab2:

    with st.expander("ℹ️ About this tab", expanded=False):
        st.markdown("**ML Model Info** shows the Random Forest classifier that powers alarm classification. 82% accuracy on 15,517 real alarm episodes across 9.9 years.")

    st.markdown('<div class="main-header">🤖 Machine Learning Classification Engine</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Classification Accuracy", "94.8%", " 2.5% vs baseline")
    with col2:
        st.metric("Training Samples", "61,522", "SMOTE balanced")
    with col3:
        st.metric("Alarm Classes", "19", "Verified types")
    with col4:
        st.metric("Features Used", "11", "Key sensors")

    st.markdown("---")
    st.subheader("📊 Model Performance")

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Model Architecture:**")
        st.write("- Random Forest (50 trees, SMOTE-balanced)")
        st.write("- class_weight='balanced' applied")
        st.write("- Cross-validated on 5 folds")
        st.write("- SMOTE: 15,516 → 61,522 samples")
        st.write("")
        st.write("**Performance Metrics:**")
        st.write("- Overall Accuracy: 82.46%")
        st.write("- CV Mean: 84.15%")
        st.write("- Baseline (before SMOTE): 26%")
        st.write("- Model file: windsense_rf_model.pkl.gz (12.7MB)")

    with col2:
        if ml_model and feature_names:
            st.subheader("🔍 Top 10 Feature Importance")
            importances     = ml_model.feature_importances_
            feature_imp_df  = pd.DataFrame({'Feature': feature_names, 'Importance': importances}) \
                               .sort_values('Importance', ascending=False).head(10)
            fig = px.bar(
                feature_imp_df, x='Importance', y='Feature', orientation='h',
                color='Importance', color_continuous_scale='Blues',
                title='Sensor Contribution to Classification', template="plotly_dark"
            )
            fig.update_layout(
                height=400, paper_bgcolor='#0D1B2A', plot_bgcolor='#0D1B2A',
                font=dict(color='#D0D8E0', size=11), title_font=dict(color='#00C9B1', size=14),
                xaxis=dict(gridcolor='#1E3A5F', linecolor='#1E3A5F', tickfont=dict(color='#8899AA')),
                yaxis=dict(gridcolor='#1E3A5F', linecolor='#1E3A5F', tickfont=dict(color='#8899AA'))
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.subheader("🔍 Feature Importance (Demo)")
            feature_names_demo = ['Generator RPM','Grid Power','Transformer Temp','Gearbox Temp','Wind Speed','Blade Pitch','Hydraulic Press','Grid Voltage','Grid Frequency','Bearing Temp']
            importance_demo    = [0.18, 0.15, 0.13, 0.11, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04]
            fig = px.bar(
                x=importance_demo[::-1], y=feature_names_demo[::-1], orientation='h',
                title='Sensor Contribution to Classification',
                labels={'x': 'Importance Score', 'y': 'Sensor'},
                color=importance_demo[::-1], color_continuous_scale='Blues', template="plotly_dark"
            )
            fig.update_layout(
                height=400, paper_bgcolor='#0D1B2A', plot_bgcolor='#0D1B2A',
                font=dict(color='#D0D8E0', size=11), title_font=dict(color='#00C9B1', size=14),
                xaxis=dict(gridcolor='#1E3A5F', linecolor='#1E3A5F', tickfont=dict(color='#8899AA')),
                yaxis=dict(gridcolor='#1E3A5F', linecolor='#1E3A5F', tickfont=dict(color='#8899AA'))
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
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

    with st.expander("ℹ️ About this tab", expanded=False):
        st.markdown("**Historical Analytics** displays 9.9 years of alarm data from Wind Farm A.")

    st.markdown('<div class="main-header">📊 Historical Analysis (9.9 Years)</div>', unsafe_allow_html=True)

    if historical_alarms is not None:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Episodes", "15,517")
        with col2:
            st.metric("Total Downtime", "45,110 hrs")
        with col3:
            st.metric("Alarm Types", "19")
        with col4:
            st.metric("Departments", "11")

        st.divider()
        st.subheader("🏆 Top Critical Alarms (Ranked by Impact)")

        _col_map = {
            'Rank':                  ['Rank', 'rank'],
            'Alarm Type':            ['Alarm_Type', 'alarm_type', 'Alarm Type'],
            'Frequency':             ['Frequency', 'frequency'],
            'Total Downtime (hrs)':  ['Total_Downtime', 'total_downtime', 'Total Downtime'],
            'Department':            ['Department', 'department', 'dept', 'Dept']
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
            st.dataframe(_disp_df, use_container_width=True, height=500)
        else:
            st.dataframe(historical_alarms, use_container_width=True, height=500)

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
                        showscale=False, line=dict(color='rgba(0,201,177,0.3)', width=1)
                    ),
                    text=dept_data['Frequency'], textposition='outside',
                    textfont=dict(color='#D4EBF8', size=11)
                ))
                fig_dept.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(13,27,42,0.8)',
                    font=dict(color='#D4EBF8', size=11), height=400,
                    xaxis=dict(gridcolor='#1E3A4A', title='Number of Alarm Episodes', color='#7FB9D4'),
                    yaxis=dict(color='#7FB9D4', tickfont=dict(size=10)),
                    margin=dict(l=20, r=60, t=20, b=40),
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
                        showscale=False, line=dict(color='rgba(255,68,68,0.3)', width=1)
                    ),
                    text=top10['Total_Downtime'].round(0).astype(int),
                    textposition='outside', textfont=dict(color='#FFB3B3', size=11)
                ))
                fig_down.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(13,27,42,0.8)',
                    font=dict(color='#D4EBF8', size=11), height=400,
                    xaxis=dict(gridcolor='#1E3A4A', title='Total Downtime (hours)', color='#7FB9D4'),
                    yaxis=dict(color='#7FB9D4', tickfont=dict(size=9)),
                    margin=dict(l=20, r=60, t=20, b=40),
                )
                st.plotly_chart(fig_down, use_container_width=True)

        # ── Additional charts ────────────────────────────────────────────────
        st.divider()
        try:
            st.subheader("📊 Alarm Frequency by Type")
            if 'Alarm_Type' in historical_alarms.columns and 'Frequency' in historical_alarms.columns:
                freq_df = historical_alarms[['Alarm_Type', 'Frequency']].dropna().sort_values('Frequency', ascending=False)
            elif 'alarm_type' in historical_alarms.columns:
                freq_col = next((c for c in ['Frequency', 'frequency', 'count'] if c in historical_alarms.columns), None)
                if freq_col:
                    freq_df = historical_alarms[['alarm_type', freq_col]].rename(columns={'alarm_type': 'Alarm_Type', freq_col: 'Frequency'}).dropna()
                else:
                    freq_df = historical_alarms.iloc[:, :2].copy()
                    freq_df.columns = ['Alarm_Type', 'Frequency']
            else:
                freq_df = pd.DataFrame({'Alarm_Type': historical_alarms.iloc[:, 0], 'Frequency': historical_alarms.iloc[:, 1]})

            fig_freq = px.bar(
                freq_df, x='Alarm_Type', y='Frequency',
                color='Frequency', color_continuous_scale='Reds', template="plotly_dark",
                title="Historical Alarm Frequency by Type",
                labels={'Alarm_Type': 'Alarm Type', 'Frequency': 'Number of Episodes'}
            )
            fig_freq.update_layout(
                height=420, paper_bgcolor='#0D1B2A', plot_bgcolor='#0D1B2A',
                font=dict(color='#D0D8E0', size=11), showlegend=False,
                xaxis=dict(tickangle=45, gridcolor='#1E3A5F', tickfont=dict(color='#8899AA')),
                yaxis=dict(gridcolor='#1E3A5F', tickfont=dict(color='#8899AA'))
            )
            st.plotly_chart(fig_freq, use_container_width=True)

            st.subheader("⏱️ Total Downtime by Alarm Type")
            dt_col   = next((c for c in ['Total_Downtime', 'total_downtime', 'Downtime', 'downtime'] if c in historical_alarms.columns), None)
            type_col = next((c for c in ['Alarm_Type', 'alarm_type', 'Alarm Type', 'type'] if c in historical_alarms.columns), None)
            if dt_col and type_col:
                dt_df = historical_alarms[[type_col, dt_col]].dropna().sort_values(dt_col, ascending=False)
                dt_df.columns = ['Alarm_Type', 'Total_Downtime']
                fig_dt = px.bar(
                    dt_df, x='Alarm_Type', y='Total_Downtime',
                    color='Total_Downtime', color_continuous_scale='Blues', template="plotly_dark",
                    title="Total Downtime Hours by Alarm Type",
                    labels={'Alarm_Type': 'Alarm Type', 'Total_Downtime': 'Downtime (hrs)'}
                )
                fig_dt.update_layout(
                    height=420, paper_bgcolor='#0D1B2A', plot_bgcolor='#0D1B2A',
                    font=dict(color='#D0D8E0', size=11), showlegend=False,
                    xaxis=dict(tickangle=45, gridcolor='#1E3A5F', tickfont=dict(color='#8899AA')),
                    yaxis=dict(gridcolor='#1E3A5F', tickfont=dict(color='#8899AA'))
                )
                st.plotly_chart(fig_dt, use_container_width=True)

            st.divider()
            st.subheader("🗓️ Alarm Heatmap — Turbine × Hour of Day")
            if detailed_episodes is not None and len(detailed_episodes) > 0:
                heatmap_df = detailed_episodes.copy()
                heatmap_df['Start_Time'] = pd.to_datetime(heatmap_df['Start_Time'])
                heatmap_df['Hour']       = heatmap_df['Start_Time'].dt.hour
                heatmap_df['Turbine']    = heatmap_df['Asset_ID'].apply(lambda x: f"T-{int(x)}" if pd.notna(x) else "T-Unknown")
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
                    colorscale='Reds', hoverongaps=False,
                    colorbar=dict(title='Alarm Count')
                ))
                fig_heat.update_layout(
                    title='Alarm Frequency by Turbine and Hour of Day (9.9 Years)',
                    xaxis_title='Hour of Day', yaxis_title='Turbine',
                    height=350, plot_bgcolor='#0D1B2A', paper_bgcolor='#0D1B2A',
                    font=dict(color='white')
                )
                st.plotly_chart(fig_heat, use_container_width=True)
                st.caption("Peak hours indicate when grid/weather events are most common.")
            else:
                st.info("Historical episode data not loaded. Heatmap unavailable.")

        except Exception as e:
            st.error(f"Error displaying historical charts: {e}")

    else:
        st.warning("⚠️ Historical data unavailable. Check data/ folder for top_50_unique_detailed_alarms.csv")

# ═══════════════════════════════════════════════════════════════════
# TAB 4 — NOTIFICATIONS & WORKFLOW
# ═══════════════════════════════════════════════════════════════════

with tab4:

    with st.expander("ℹ️ About this tab", expanded=False):
        st.markdown("**Notifications & Workflow** shows the 6-step alarm resolution pipeline.")

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
                <div style="font-size: 2rem; font-weight: bold; color:#00C9B1;">{step['step']}</div>
                <div style="font-size: 1.2rem; font-weight: bold; margin: 0.5rem 0;">{step['name']}</div>
                <div style="font-size: 0.85rem; color:#D0D8E0;">{step['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.subheader("📊 Notification Statistics")

    col1, col2, col3, col4 = st.columns(4)
    notification_log = st.session_state.get('notification_log', [])
    active_alarms    = st.session_state.get('active_critical_alarms', {})
    escalated        = st.session_state.get('escalated_alarms', {})

    with col1:
        st.metric("📧 Emails Sent",    sum(1 for n in notification_log if n['type'] == 'EMAIL'))
    with col2:
        st.metric("📱 WhatsApp Sent",  sum(1 for n in notification_log if n['type'] == 'WHATSAPP'))
    with col3:
        st.metric("🚨 Active Critical", len(active_alarms))
    with col4:
        st.metric("⚠️ Escalated", len(escalated), delta_color="inverse")

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
            log_df = pd.DataFrame(log_data)
            st.table(log_df)
            csv = log_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Notification Log", csv, "notification_log.csv", "text/csv", use_container_width=True)
    else:
        st.info("No email/WhatsApp notifications sent yet.")

    st.divider()
    if escalated:
        st.subheader("⚠️ Escalated Alarms")
        for alarm_id, esc_info in escalated.items():
            alarm_data = active_alarms.get(alarm_id, {})
            st.markdown(f"""
            <div style="background-color: #2a1500; border-left: 4px solid #ff8800;
                        padding: 15px; border-radius: 0 8px 8px 0; color: #D0D8E0; margin: 10px 0;">
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
                st.write(f"**Status:** ✅ Sent to {notif['department']}")
    else:
        st.info("No notifications yet. Generate alarms to see notifications in action!")

    st.divider()
    st.subheader("👥 Stakeholder Directory")
    st.info("📋 Primary stakeholders are automatically notified via Email + WhatsApp for their assigned alarm types.")

    for alarm_type, stakeholder_info in STAKEHOLDERS.items():
        if alarm_type == 'DEFAULT':
            continue
        with st.expander(f"**{alarm_type}** - Escalation Time: {stakeholder_info.get('escalation_time', 30)} min"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**🎯 Primary Contact**")
                primary = stakeholder_info.get('primary', {})
                st.write(f"**Name:** {primary.get('name', 'N/A')}")
                st.write(f"**Role:** {primary.get('role', 'N/A')}")
                st.write(f"**Email:** {primary.get('email', 'N/A')}")
                st.write(f"**Phone:** {primary.get('phone', 'N/A')}")
                st.caption("Receives: Email + WhatsApp (Immediate)")
            with col2:
                st.markdown("**📧 Secondary Contact**")
                secondary = stakeholder_info.get('secondary', {})
                st.write(f"**Name:** {secondary.get('name', 'N/A')}")
                st.write(f"**Role:** {secondary.get('role', 'N/A')}")
                st.write(f"**Email:** {secondary.get('email', 'N/A')}")
                st.write(f"**Phone:** {secondary.get('phone', 'N/A')}")
                st.caption("Receives: Email (Copy)")
            with col3:
                st.markdown("**⚠️ Escalation Contact**")
                management = stakeholder_info.get('management', {})
                st.write(f"**Name:** {management.get('name', 'N/A')}")
                st.write(f"**Role:** {management.get('role', 'N/A')}")
                st.write(f"**Email:** {management.get('email', 'N/A')}")
                st.write(f"**Phone:** {management.get('phone', 'N/A')}")
                st.caption(f"Receives: Email + WhatsApp (After {stakeholder_info.get('escalation_time', 30)} min)")

# ═══════════════════════════════════════════════════════════════════
# TAB 5 — DMAIC ANALYSIS
# ═══════════════════════════════════════════════════════════════════

with tab5:

    with st.expander("ℹ️ About this tab", expanded=False):
        st.markdown("**DMAIC Analysis** provides full Define-Measure-Analyze-Improve-Control documentation for all 19 verified alarm types.")

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

    alarm_classes = [
        'Main Controller Fault', 'Extended Grid Outage', 'Grid Frequency Deviation',
        'Momentary Grid Loss', 'Grid Voltage Fluctuation', 'Emergency Brake Activation',
        'Safety System Activation', 'Overspeed Protection Triggered', 'Yaw System Hydraulic Fault',
        'Pitch System Hydraulic Fault', 'Hydraulic Oil Contamination', 'Converter Circuit Fault',
        'Generator Bearing Overheating', 'Power Electronics Failure', 'Transformer Oil Temperature High',
        'Hydraulic Filter Clogged', 'Generator Winding Temperature High', 'Hydraulic Pressure Drop',
        'Hydraulic Valve Response Slow'
    ]

    selected_alarm = st.selectbox("Select Alarm Type for Detailed DMAIC Analysis:", alarm_classes)

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
        with col1:
            st.markdown("**Frequency**")
            st.write(measure_data.get('frequency', 'N/A'))
        with col2:
            st.markdown("**Avg Duration**")
            st.write(measure_data.get('duration', 'N/A'))
        with col3:
            st.markdown("**LPF Impact**")
            st.write(measure_data.get('lpf_impact', 'N/A'))
        with col4:
            st.markdown("**Target**")
            st.write(measure_data.get('target', 'N/A'))

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
        improve_data = dmaic.get('improve', {})
        solutions    = improve_data.get('solutions', [])
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
        st.warning(
            f"⚠️ DMAIC database not loaded. Please ensure `dmaic_complete_database.json` exists at: "
            f"`{DATA_PATH}dmaic_complete_database.json`"
        )
        st.info("Once the file is available, all 19 alarm types will display full DMAIC analysis automatically.")

# ═══════════════════════════════════════════════════════════════════
# TAB 6 — OPTIMIZATION & FORECASTING
# ═══════════════════════════════════════════════════════════════════

with tab6:

    with st.expander("ℹ️ About this tab", expanded=False):
        st.markdown("**Optimization & Forecasting** shows the LPF reduction roadmap, 5-phase implementation plan, and ROI projections.")

    st.markdown('<div class="main-header">🎯 Optimization & Predictive Forecasting</div>', unsafe_allow_html=True)

    st.subheader("📈 Lost Production Factor (LPF) Optimization")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current LPF", "3.64%", delta="-1.36% from baseline")
    with col2:
        st.metric("Target LPF", "<2.0%", delta="Industry best practice")
    with col3:
        st.metric("Potential Savings", "₹24.9-41.5 Crore/year", delta="After full implementation")

    st.divider()
    st.subheader("🔍 LPF Breakdown by Category")

    lpf_data = pd.DataFrame({
        'Category':        ['Grid-Related', 'Mechanical', 'Electrical', 'Hydraulic', 'Software'],
        'LPF_Percentage':  [2.85, 0.35, 0.25, 0.12, 0.07],
        'Downtime_Hours':  [28500, 3500, 2500, 1200, 700]
    })

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('LPF Distribution', 'Downtime Distribution'),
        specs=[[{'type': 'pie'}, {'type': 'bar'}]]
    )
    fig.add_trace(go.Pie(labels=lpf_data['Category'], values=lpf_data['LPF_Percentage'], hole=0.4), row=1, col=1)
    fig.add_trace(go.Bar(x=lpf_data['Category'], y=lpf_data['Downtime_Hours'], marker_color='#4FC3F7'), row=1, col=2)
    fig.update_layout(
        height=400, showlegend=True,
        paper_bgcolor='#0D1B2A', plot_bgcolor='#0D1B2A',
        font=dict(color='#D0D8E0', size=11),
        xaxis=dict(gridcolor='#1E3A5F', linecolor='#1E3A5F', tickfont=dict(color='#8899AA')),
        yaxis=dict(gridcolor='#1E3A5F', linecolor='#1E3A5F', tickfont=dict(color='#8899AA')),
        xaxis2=dict(gridcolor='#1E3A5F', linecolor='#1E3A5F', tickfont=dict(color='#8899AA')),
        yaxis2=dict(gridcolor='#1E3A5F', linecolor='#1E3A5F', tickfont=dict(color='#8899AA'))
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
        xaxis_title="Time Period", yaxis_title="Number of Alarms", height=500,
        paper_bgcolor='#0D1B2A', plot_bgcolor='#0D1B2A',
        font=dict(color='#D0D8E0', size=11), title_font=dict(color='#00C9B1', size=14),
        xaxis=dict(gridcolor='#1E3A5F', linecolor='#1E3A5F', tickfont=dict(color='#8899AA')),
        yaxis=dict(gridcolor='#1E3A5F', linecolor='#1E3A5F', tickfont=dict(color='#8899AA')),
        legend=dict(font=dict(color='#D0D8E0'))
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("🗺️ 5-Phase Implementation Roadmap")

    phases = [
        {'phase': 'Phase 1: Foundation Setup', 'investment': '₹12,000', 'timeline': '2 weeks',
         'actions': ['Establish data warehouse using PostgreSQL or MongoDB', 'Setup SCADA and CSV database integration', 'Collect and organize historical data (6-12 months)', 'Create data infrastructure for real-time processing', 'Configure cloud storage (Google Cloud - 4 months)'],
         'expected_lpf': 'Baseline established', 'key_milestones': ['Week 1: Data warehouse deployment complete', 'Week 2: Historical data collection and validation done']},
        {'phase': 'Phase 2: AI Model Development & Training', 'investment': '₹15,000', 'timeline': '4 weeks',
         'actions': ['Train Machine Learning Models (Random Forest, SVM, LSTM)', 'Develop AI classifier for alarm categorization', 'Build Root Cause Engine with 85% accuracy', 'Create Predictive Model for 24-72hr forecasting', 'Optimize model parameters using GPU training (Google Colab Pro+)'],
         'expected_lpf': 'Model accuracy: ~88% (F1)', 'key_milestones': ['Week 3: Random Forest classifier trained', 'Week 4: LSTM predictive model developed', 'Week 5: Root Cause Engine integrated', 'Week 6: Model validation and testing complete']},
        {'phase': 'Phase 3: Backend & Frontend Development', 'investment': '₹9,500', 'timeline': '3 weeks',
         'actions': ['API & Dashboard interfacing using Streamlit/Flask', 'Build Real-Time Dashboard with live monitoring', 'Setup REST API Gateway (FastAPI/Django)', 'Implement notification system (SMS/Email alerts via Twilio, Gmail, SendGrid)', 'Create smart team routing and assignment logic'],
         'expected_lpf': 'Dashboard operational', 'key_milestones': ['Week 7: REST API deployment', 'Week 8: Dashboard UI completed', 'Week 9: Notification system tested and live']},
        {'phase': 'Phase 4: Integration & Pilot Deployment', 'investment': '₹10,000', 'timeline': '2 weeks',
         'actions': ['Live turbine pilot integration & test reports', 'SCADA connection via OPC UA client library', 'User acceptance testing (UAT)', 'Configure notifications and escalation workflows', 'Field testing with mechanical, electrical, and software teams'],
         'expected_lpf': 'Initial reduction: 10-15%', 'key_milestones': ['Week 10: SCADA integration successful', 'Week 11: Pilot testing complete with positive results']},
        {'phase': 'Phase 5: Validation & Full-Scale Rollout', 'investment': '₹5,000', 'timeline': '3 weeks',
         'actions': ['Measure Key Performance Indicators (KPI) report', 'Project rollout strategy and scaling plan', 'Operator training and documentation', 'DMAIC loop implementation for continuous improvement', 'Performance validation and optimization'],
         'expected_lpf': 'Target: <2.5% LPF, ~35% reduction', 'key_milestones': ['Week 12: KPI measurement and reporting', 'Week 13: Full team training completed', 'Week 14: System handover and go-live']}
    ]

    for phase in phases:
        with st.expander(f"**{phase['phase']}** - Investment: {phase['investment']} | Timeline: {phase['timeline']}", expanded=True):
            st.write("**Key Deliverables:**")
            for action in phase['actions']:
                st.write(f"✓ {action}")
            st.success(f"**Expected Outcome:** {phase['expected_lpf']}")
            if phase['key_milestones']:
                st.write("**Key Milestones:**")
                for milestone in phase['key_milestones']:
                    st.write(f"  📌 {milestone}")

    st.info("⏱️ **Total Prototype Timeline:** 14 weeks (3.5 months)\n**Note:** This timeline is for student prototype.")

    st.divider()
    st.subheader("💰 Return on Investment (ROI)")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Pilot Cost",  "₹51,500",    delta="Student prototype")
    with col2:
        st.metric("Annual Savings",    "₹50+ Lakh",  delta="Per farm/year")
    with col3:
        st.metric("ROI Year 1",        "900%+",       delta="Industry-leading")
    with col4:
        st.metric("Payback Period",    "~3 weeks",    delta="Fast return")
    st.caption("*Costs shown are for student prototype.")

# ═══════════════════════════════════════════════════════════════════
# TAB 7 — ALARM ACKNOWLEDGMENT
# ═══════════════════════════════════════════════════════════════════

with tab7:

    with st.expander("ℹ️ About this tab", expanded=False):
        st.markdown("**Alarm Acknowledgment** tracks all active alarms and their acknowledgment status.")

    st.markdown('<div class="main-header">🎛️ Alarm Acknowledgment & Management</div>', unsafe_allow_html=True)

    clean_orphaned_acknowledgments()

    if 'acknowledged_alarms' not in st.session_state:
        st.session_state.acknowledged_alarms = {}
    st.session_state.acknowledged_alarms = load_acknowledgments()

    total_alarms     = len(st.session_state.alarm_buffer)
    active_alarm_ids = {a['alarm_id'] for a in st.session_state.alarm_buffer}
    acknowledged_count = len([aid for aid in st.session_state.acknowledged_alarms.keys() if aid in active_alarm_ids])
    pending_count      = max(0, total_alarms - acknowledged_count)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Alarms", total_alarms)
    with col2:
        st.metric("✅ Acknowledged", acknowledged_count,
                  delta=f"{(acknowledged_count/total_alarms*100) if total_alarms > 0 else 0:.1f}%")
    with col3:
        st.metric("⏳ Pending", pending_count, delta=f"-{pending_count} to clear", delta_color="inverse")
    with col4:
        dashboard_acks = [a for a in st.session_state.acknowledged_alarms.values() if 'response_time' in a]
        avg_response   = np.mean([a['response_time'] for a in dashboard_acks]) if dashboard_acks else 0
        st.metric("Avg Response Time", f"{avg_response:.1f} min")

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
                        <div style="background-color: #112233; border-left: 4px solid {priority_color};
                                    padding: 10px; border-radius: 0 5px 5px 0; color: #D0D8E0;">
                            <strong style="color:{priority_color};">Priority:</strong> {alarm['priority']}<br>
                            <strong>Confidence:</strong> {alarm['confidence']:.1f}%<br>
                            <strong>Turbine:</strong> T-{alarm['asset_id']}<br>
                            <strong>Status Type:</strong> {alarm['status_type_id']}
                        </div>
                        """, unsafe_allow_html=True)

                        st.write("**🔍 Root Cause Analysis:**")
                        sensor_data = {k: v for k, v in alarm.items() if 'sensor' in k or 'power' in k or 'wind' in k}
                        rca_result  = st.session_state.rca_engine.analyze(alarm['predicted_type'], sensor_data)
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
                                ack_time    = datetime.now()
                                alarm_time  = datetime.strptime(alarm['timestamp'], '%Y-%m-%d %H:%M:%S')
                                response_time = (ack_time - alarm_time).total_seconds() / 60
                                ack_data = {
                                    'technician':   technician_name,
                                    'ack_time':     ack_time.strftime('%Y-%m-%d %H:%M:%S'),
                                    'action_taken': action_taken,
                                    'notes':        notes,
                                    'response_time': response_time,
                                    'alarm_data':   alarm,
                                    'method':       'dashboard'
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
        ack_data = []
        for alarm_id, ack_info in st.session_state.acknowledged_alarms.items():
            alarm_data = ack_info.get('alarm_data', {})
            method     = ack_info.get('method', 'unknown')
            if method in ('email_link', 'whatsapp_link'):
                channel_label = '📱 WhatsApp' if method == 'whatsapp_link' else '📧 Email'
                ack_data.append({
                    'Alarm ID':             alarm_id,
                    'Type':                 f'{channel_label} Acknowledgment',
                    'Turbine':              'See Notification',
                    'Priority':             'CRITICAL',
                    'Acknowledged By':      f'{channel_label} Link',
                    'Ack Time':             ack_info.get('time', 'N/A'),
                    'Action':               f'Acknowledged via {channel_label}',
                    'Response Time (min)':  'N/A'
                })
            else:
                ack_data.append({
                    'Alarm ID':             alarm_id,
                    'Type':                 alarm_data.get('predicted_type', 'N/A'),
                    'Turbine':              f"T-{alarm_data.get('asset_id', 'N/A')}",
                    'Priority':             alarm_data.get('priority', 'N/A'),
                    'Acknowledged By':      ack_info.get('technician', 'Unknown'),
                    'Ack Time':             ack_info.get('ack_time', 'N/A'),
                    'Action':               ack_info.get('action_taken', 'N/A'),
                    'Response Time (min)':  f"{ack_info.get('response_time', 0):.1f}"
                })

        ack_df = pd.DataFrame(ack_data)
        st.table(ack_df)
        csv = ack_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Acknowledgment Log", csv, "alarm_acknowledgments.csv", "text/csv", use_container_width=True)

        dashboard_acks2 = [a for a in st.session_state.acknowledged_alarms.values()
                           if a.get('method') not in ('email_link', 'whatsapp_link') and 'response_time' in a]
        if dashboard_acks2:
            st.subheader("📊 Acknowledgment Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_response = np.mean([a['response_time'] for a in dashboard_acks2])
                st.metric("Avg Response Time", f"{avg_response:.1f} min")
            with col2:
                actions   = [a.get('action_taken', 'N/A') for a in dashboard_acks2]
                by_action = pd.Series(actions).value_counts()
                st.metric("Most Common Action", by_action.index[0] if len(by_action) > 0 else "N/A")
            with col3:
                techs   = [a.get('technician', 'N/A') for a in dashboard_acks2]
                by_tech = pd.Series(techs).value_counts()
                st.metric("Most Active Technician", by_tech.index[0] if len(by_tech) > 0 else "N/A")

            response_times = [a['response_time'] for a in dashboard_acks2]
            fig = px.histogram(
                x=response_times, nbins=20,
                title='Response Time Distribution',
                labels={'x': 'Response Time (min)', 'y': 'Count'},
                template="plotly_dark", color_discrete_sequence=["#00C9A7"]
            )
            fig.update_layout(
                height=300, paper_bgcolor='#0D1B2A', plot_bgcolor='#0D1B2A',
                font=dict(color='#D0D8E0', size=11), title_font=dict(color='#00C9B1', size=14),
                xaxis=dict(gridcolor='#1E3A5F', linecolor='#1E3A5F', tickfont=dict(color='#8899AA')),
                yaxis=dict(gridcolor='#1E3A5F', linecolor='#1E3A5F', tickfont=dict(color='#8899AA'))
            )
            st.plotly_chart(fig, use_container_width=True)

        email_acks = sum(1 for a in st.session_state.acknowledged_alarms.values() if a.get('method') == 'email_link')
        wa_acks    = sum(1 for a in st.session_state.acknowledged_alarms.values() if a.get('method') == 'whatsapp_link')
        if email_acks > 0:
            st.info(f"📧 {email_acks} alarm(s) acknowledged via Email link")
        if wa_acks > 0:
            st.info(f"📱 {wa_acks} alarm(s) acknowledged via WhatsApp link")
    else:
        st.info("No alarms have been acknowledged yet")

    # ── Anomaly Review Panel ─────────────────────────────────────────────────
    st.divider()
    st.subheader("🔬 Anomaly Review Panel")
    st.caption("Alarms flagged as anomalous by Isolation Forest, awaiting operator review")

    if hasattr(st.session_state, 'iso_detector') and st.session_state.iso_detector.is_trained:
        stats = st.session_state.iso_detector.get_stats()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Anomalies Logged", stats['total_anomalies_logged'])
        with col2:
            st.metric("Pending Review", stats['pending_review'])
        with col3:
            st.metric("Marked as Known", stats['marked_as_known'])

        anomaly_log = st.session_state.iso_detector.load_anomaly_log()
        pending     = [e for e in anomaly_log if e.get('status') == 'pending_review']

        if pending:
            st.warning(f"⚠️ {len(pending)} anomalies need your review")

            for _aidx, entry in enumerate(pending[:5]):
                with st.expander(
                    f"⚠️ {entry['alarm_id']} | Asset: {entry['asset_id']} | "
                    f"Score: {entry['anomaly_score']} | {entry['logged_at']}"
                ):
                    st.write("**Sensor Snapshot:**")
                    for sensor, val in entry.get('sensor_values', {}).items():
                        st.write(f"  {sensor}: {val}")
                    st.write(f"**Predicted Type:** {entry.get('predicted_type', 'N/A')}")

                    new_name = st.text_input(
                        "Rename this anomaly type:",
                        value=f"Unknown Anomaly {entry.get('alarm_id', 'UNK')}",
                        key=f"rename_input_{_aidx}"
                    )

                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("➕ Add to Alarm DB", key=f"add_db_{_aidx}", type="primary"):
                            if new_name.strip():
                                success, msg = st.session_state.iso_detector.add_to_alarm_database(
                                    entry.get('alarm_id', 'UNKNOWN'), new_name.strip()
                                )
                                if success:
                                    st.success(f"✅ {msg}")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error(f"❌ {msg}")
                            else:
                                st.warning("⚠️ Please enter a name before adding.")
                    with col_b:
                        if st.button("✅ Mark as Known (no rename)", key=f"mark_known_{_aidx}"):
                            st.session_state.iso_detector.mark_as_known(entry.get('alarm_id', 'UNKNOWN'))
                            st.success("✅ Marked as known.")
                            st.rerun()
        else:
            st.success("✅ No anomalies pending review")
    else:
        st.info("Train the anomaly detector from the sidebar first (need 10+ alarms generated)")

# ═══════════════════════════════════════════════════════════════════
# TAB 8 — OPC UA LIVE FEED
# ═══════════════════════════════════════════════════════════════════

with tab8:

    with st.expander("ℹ️ About this tab", expanded=False):
        st.markdown("**OPC UA Live Feed** simulates a live IEC 62541 OPC UA data stream from all 5 turbines.")

    st.markdown('<div class="main-header">🏭 OPC UA Industrial Data Feed</div>', unsafe_allow_html=True)
    st.divider()

    st.session_state.opcua_sim = OPCUASimulator()
    for alarm in st.session_state.alarm_buffer[:5]:
        turbine_id = alarm['asset_id']
        if turbine_id in st.session_state.opcua_sim.turbine_ids:
            st.session_state.opcua_sim.active_alarms[turbine_id] = alarm['predicted_type']

    st.subheader("⚡ Live Fleet Status")
    fleet = st.session_state.opcua_sim.get_fleet_summary()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔋 Total Fleet Power",  f"{fleet['total_power_kw']:,.0f} kW")
    with col2:
        st.metric("✅ Turbines Normal",    fleet['turbines_normal'])
    with col3:
        st.metric("🚨 Turbines in Alarm", fleet['turbines_in_alarm'], delta_color="inverse")
    with col4:
        st.metric("📡 Grid Frequency",    f"{fleet['grid_frequency_hz']} Hz")

    if fleet['active_alarm_types']:
        for alarm in fleet['active_alarm_types']:
            st.error(f"🚨 ACTIVE ALARM DETECTED: {alarm}")

    st.divider()
    st.subheader("📋 OPC UA Node Data — Live Snapshot")
    readings     = st.session_state.opcua_sim.get_current_readings()
    readings_df  = pd.DataFrame(readings)
    display_readings = readings_df[['node_id', 'description', 'value', 'unit', 'status', 'timestamp']].copy()
    display_readings.columns = ['Node ID', 'Description', 'Value', 'Unit', 'Status', 'Timestamp']
    st.table(display_readings)

    # Wire OPC UA anomaly readings into iso_detector
    for _reading in readings:
        if _reading.get('is_anomaly', False):
            _synthetic_alarm = {
                'alarm_id':         f"OPC-{str(_reading.get('node_id', 'UNK'))}-{int(time.time())}",
                'asset_id':         str(_reading.get('turbine_id', 'OPC')),
                'predicted_type':   'OPC UA Anomaly',
                'sensor_11_avg':    float(_reading.get('value', 0)) if 'temp'      in str(_reading.get('node_id', '')).lower() else 0.0,
                'sensor_12_avg':    0.0,
                'sensor_41_avg':    float(_reading.get('value', 0)) if 'hydraulic' in str(_reading.get('node_id', '')).lower() else 0.0,
                'power_30_avg':     float(_reading.get('value', 0)) if 'power'     in str(_reading.get('node_id', '')).lower() else 0.0,
                'wind_speed_3_avg': 0.0,
            }
            _anomaly_score = float(_reading.get('anomaly_score', 0.75))
            try:
                if 'iso_detector' in st.session_state and st.session_state.iso_detector is not None:
                    st.session_state.iso_detector.log_anomaly(_synthetic_alarm, _anomaly_score)
            except Exception:
                pass

    alarming_nodes = [r for r in readings if r.get('alarm_active', False) or r.get('is_anomaly', False)]
    if alarming_nodes:
        st.markdown("**🚨 Active Alarm / Anomaly Nodes:**")
        for node in alarming_nodes:
            anomaly_label = " | ⚠️ ANOMALY" if node.get('is_anomaly', False) else ""
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #8B0000, #cc0000);
                        color: white; padding: 0.6rem 1rem; border-radius: 6px;
                        border-left: 4px solid #ff4444; margin: 0.3rem 0;">
                <strong>{node.get('node_id', 'Unknown')}</strong> —
                {node.get('description', '')} |
                Value: {node.get('value', 'N/A')} {node.get('unit', '')} |
                Status: {node.get('status', 'N/A')}{anomaly_label}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ All OPC UA nodes operating normally")

    st.divider()
    col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
    with col_r2:
        if st.button("🔄 Refresh OPC UA Data", use_container_width=True, type="primary"):
            st.rerun()
    st.caption("📌 In production, this feed would connect to the wind farm's OPC UA server via opcua-asyncio.")

# ═══════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════

st.divider()
st.markdown("""
<div style="text-align: center; color: #4FC3F7; padding: 2rem;">
    <strong>WindSense AI © 2026</strong> | Team TG0907494 | TECHgium 9th Edition<br>
    Intelligent Predictive Control and Alarm Optimization in Wind Turbine Systems
</div>
""", unsafe_allow_html=True)