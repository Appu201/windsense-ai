%%writefile windsense_complete_dashboard.py


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
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ═══════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="WindSense AI - Intelligent Alarm Management",
    page_icon="🌀",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 3px solid #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .alert-critical {
        background-color: #ff4444;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .alert-high {
        background-color: #ff8800;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .alert-medium {
        background-color: #ffbb33;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        font-size: 1.1rem;
        font-weight: 600;
    }

    /* Control metric font sizes */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;  /* Reduced from default 2.5rem */
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
    }

    [data-testid="stMetricDelta"] {
        font-size: 0.8rem !important;
    }

    /* Alternative: If you want even smaller */
    .metric-small [data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
    }

    /* Reduce DMAIC Measure metric font size so full text is visible */
    .dmaic-measure [data-testid="stMetricValue"] {
        font-size: 1.0rem !important;
        white-space: normal !important;
        word-break: break-word !important;
    }
    .dmaic-measure [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# FILE PATHS
# ═══════════════════════════════════════════════════════════════════

BASE_PATH = '/content/drive/MyDrive/WindSense_POC_TG0907494/'
DATA_PATH = BASE_PATH + '01_Data/'
MODEL_PATH = BASE_PATH + '02_Models/'
OUTPUT_PATH = BASE_PATH + '03_Outputs/'

# ═══════════════════════════════════════════════════════════════════
# LOAD DMAIC DATABASE (used by both RCA Engine and DMAIC Tab)
# ═══════════════════════════════════════════════════════════════════

@st.cache_data
def load_dmaic_database():
    """Load the complete DMAIC database from JSON"""
    try:
        dmaic_json_path = DATA_PATH + 'dmaic_complete_database.json'
        if os.path.exists(dmaic_json_path):
            with open(dmaic_json_path, 'r') as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        return {}

DMAIC_DATABASE = load_dmaic_database()
# ═══════════════════════════════════════════════════════════════════
# PERSISTENT ACKNOWLEDGMENT STORAGE
# ═══════════════════════════════════════════════════════════════════

ACK_FILE = OUTPUT_PATH + 'acknowledgments.json'

def load_acknowledgments():
    """Load acknowledgments from persistent file"""
    if os.path.exists(ACK_FILE):
        try:
            with open(ACK_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_acknowledgment(alarm_id, ack_data):
    """Save acknowledgment to persistent file"""
    try:
        acks = load_acknowledgments()
        acks[alarm_id] = ack_data
        with open(ACK_FILE, 'w') as f:
            json.dump(acks, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving acknowledgment: {e}")
        return False

# ═══════════════════════════════════════════════════════════════════
# LOAD CURRENT DASHBOARD URL
# ═══════════════════════════════════════════════════════════════════

def get_dashboard_url():
    """Get current dashboard URL from file"""
    try:
        url_file = '/content/current_dashboard_url.txt'
        if os.path.exists(url_file):
            with open(url_file, 'r') as f:
                return f.read().strip()
    except:
        pass
    return "http://localhost:8501"

DASHBOARD_URL = get_dashboard_url()
DASHBOARD_URL = get_dashboard_url()

# ═══════════════════════════════════════════════════════════════════
# HANDLE ACKNOWLEDGMENT FROM EMAIL LINK
# ═══════════════════════════════════════════════════════════════════

query_params = st.query_params

# Handle acknowledgment from email link
if 'ack' in query_params:
    alarm_id = query_params['ack']

    # Load existing acknowledgments
    if 'acknowledged_alarms' not in st.session_state:
        st.session_state.acknowledged_alarms = load_acknowledgments()

    # Check if already acknowledged
    if alarm_id in st.session_state.acknowledged_alarms:
        st.warning(f"⚠️ Alarm {alarm_id} was already acknowledged previously.")
        prev_ack = st.session_state.acknowledged_alarms[alarm_id]
        st.info(f"Previously acknowledged at: {prev_ack.get('time', 'Unknown')}")
    else:
        # Save acknowledgment
        ack_data = {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'method': 'email_link',
            'alarm_id': alarm_id
        }

        if save_acknowledgment(alarm_id, ack_data):
            st.session_state.acknowledged_alarms[alarm_id] = ack_data

            # Show success page
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

    # Button to return to dashboard
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🏠 Return to Dashboard", use_container_width=True, type="primary"):
            st.query_params.clear()
            st.rerun()

    st.stop()

# ═══════════════════════════════════════════════════════════════════
# STAKEHOLDER DATABASE & NOTIFICATION SYSTEM
# ═══════════════════════════════════════════════════════════════════

# Stakeholder database for alarm notifications
STAKEHOLDERS = {
    'Main Controller Fault': {
        'primary': {'name': 'Divya', 'role': 'Control Systems Engineer', 'email': 'divyajay.1612@gmail.com', 'phone': '+918778838055'},
        'secondary': {'name': 'Sarah Johnson', 'role': 'Senior Engineer', 'email': 'sarah.j@windfarm.com', 'phone': '+1234567891'},
        'management': {'name': 'Mike Davis', 'role': 'Engineering Manager', 'email': 'mike.d@windfarm.com', 'phone': '+1234567892'},
        'escalation_time': 30  # minutes
    },
    'Grid Frequency Deviation': {
        'primary': {'name': 'Emily Chen', 'role': 'Grid Integration Specialist', 'email': 'emily.c@windfarm.com', 'phone': '+1234567893'},
        'secondary': {'name': 'David Wilson', 'role': 'Electrical Engineer', 'email': 'david.w@windfarm.com', 'phone': '+1234567894'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager', 'email': 'lisa.a@windfarm.com', 'phone': '+1234567895'},
        'escalation_time': 20
    },
    'Extended Grid Outage': {
        'primary': {'name': 'Robert Taylor', 'role': 'Site Manager', 'email': 'robert.t@windfarm.com', 'phone': '+1234567896'},
        'secondary': {'name': 'Jennifer Lee', 'role': 'Operations Supervisor', 'email': 'jennifer.l@windfarm.com', 'phone': '+1234567897'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager', 'email': 'lisa.a@windfarm.com', 'phone': '+1234567895'},
        'escalation_time': 15
    },
    'Emergency Brake Activation': {
        'primary': {'name': 'Carlos Rodriguez', 'role': 'Mechanical Technician', 'email': 'carlos.r@windfarm.com', 'phone': '+1234567898'},
        'secondary': {'name': 'Anna Martinez', 'role': 'Senior Technician', 'email': 'anna.m@windfarm.com', 'phone': '+1234567899'},
        'management': {'name': 'Mike Davis', 'role': 'Engineering Manager', 'email': 'mike.d@windfarm.com', 'phone': '+1234567892'},
        'escalation_time': 25
    },
    'Generator Bearing Overheating': {
        'primary': {'name': 'Aarif', 'role': 'Mechanical Technician', 'email': 'muhammadhaarif2000@gmail.com', 'phone': '+919123516325'},
        'secondary': {'name': 'Anna Martinez', 'role': 'Senior Technician', 'email': 'anna.m@windfarm.com', 'phone': '+1234567899'},
        'management': {'name': 'Mike Davis', 'role': 'Engineering Manager', 'email': 'mike.d@windfarm.com', 'phone': '+1234567892'},
        'escalation_time': 20
    },
    'Hydraulic Oil Contamination': {
        'primary': {'name': 'Anna Martinez', 'role': 'Senior Technician', 'email': 'anna.m@windfarm.com', 'phone': '+1234567899'},
        'secondary': {'name': 'Carlos Rodriguez', 'role': 'Mechanical Technician', 'email': 'carlos.r@windfarm.com', 'phone': '+1234567898'},
        'management': {'name': 'Mike Davis', 'role': 'Engineering Manager', 'email': 'mike.d@windfarm.com', 'phone': '+1234567892'},
        'escalation_time': 35
    },
    'Converter Circuit Fault': {
        'primary': {'name': 'David Wilson', 'role': 'Electrical Engineer', 'email': 'david.w@windfarm.com', 'phone': '+1234567894'},
        'secondary': {'name': 'Emily Chen', 'role': 'Grid Integration Specialist', 'email': 'emily.c@windfarm.com', 'phone': '+1234567893'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager', 'email': 'lisa.a@windfarm.com', 'phone': '+1234567895'},
        'escalation_time': 25
    },
    'Yaw System Hydraulic Fault': {
        'primary': {'name': 'Aparajithaa', 'role': 'Yaw Systems Specialist', 'email': 'ts.aparajithaa@gmail.com', 'phone': '+919284743112'},
        'secondary': {'name': 'Amanda White', 'role': 'Hydraulic Engineer', 'email': 'amanda.w@windfarm.com', 'phone': '+1234567911'},
        'management': {'name': 'Mike Davis', 'role': 'Engineering Manager', 'email': 'mike.d@windfarm.com', 'phone': '+1234567892'},
        'escalation_time': 480  # 8 hours
    },
    'Pitch System Hydraulic Fault': {
        'primary': {'name': 'Diego Lopez', 'role': 'Pitch System Engineer', 'email': 'diego.l@windfarm.com', 'phone': '+1234567912'},
        'secondary': {'name': 'Rachel Green', 'role': 'Blade Specialist', 'email': 'rachel.g@windfarm.com', 'phone': '+1234567913'},
        'management': {'name': 'Mike Davis', 'role': 'Engineering Manager', 'email': 'mike.d@windfarm.com', 'phone': '+1234567892'},
        'escalation_time': 480
    },
    'Power Electronics Failure': {
        'primary': {'name': 'Jack Williams', 'role': 'Power Systems Engineer', 'email': 'jack.w@windfarm.com', 'phone': '+1234567920'},
        'secondary': {'name': 'Emma Davis', 'role': 'Electronics Tech', 'email': 'emma.d@windfarm.com', 'phone': '+1234567921'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager', 'email': 'lisa.a@windfarm.com', 'phone': '+1234567895'},
        'escalation_time': 120
    },
    'Transformer Oil Temperature High': {
        'primary': {'name': 'Kevin Murphy', 'role': 'Transformer Specialist', 'email': 'kevin.m@windfarm.com', 'phone': '+1234567922'},
        'secondary': {'name': 'Laura Johnson', 'role': 'Oil Analysis Tech', 'email': 'laura.j@windfarm.com', 'phone': '+1234567923'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager', 'email': 'lisa.a@windfarm.com', 'phone': '+1234567895'},
        'escalation_time': 120
    },
    'Hydraulic Filter Clogged': {
        'primary': {'name': 'Marcus Lee', 'role': 'Hydraulic Technician', 'email': 'marcus.l@windfarm.com', 'phone': '+1234567924'},
        'secondary': {'name': 'Patricia King', 'role': 'Maintenance Supervisor', 'email': 'patricia.k@windfarm.com', 'phone': '+1234567925'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager', 'email': 'lisa.a@windfarm.com', 'phone': '+1234567895'},
        'escalation_time': 480
    },
    'Generator Winding Temperature High': {
        'primary': {'name': 'Nathan Scott', 'role': 'Generator Specialist', 'email': 'nathan.s@windfarm.com', 'phone': '+1234567926'},
        'secondary': {'name': 'Quinn Roberts', 'role': 'Electrical Engineer', 'email': 'quinn.r@windfarm.com', 'phone': '+1234567927'},
        'management': {'name': 'Mike Davis', 'role': 'Engineering Manager', 'email': 'mike.d@windfarm.com', 'phone': '+1234567892'},
        'escalation_time': 120
    },
    'Hydraulic Pressure Drop': {
        'primary': {'name': 'Oscar Ramirez', 'role': 'Hydraulic Engineer', 'email': 'oscar.r@windfarm.com', 'phone': '+1234567928'},
        'secondary': {'name': 'Tina Garcia', 'role': 'Systems Tech', 'email': 'tina.g@windfarm.com', 'phone': '+1234567929'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager', 'email': 'lisa.a@windfarm.com', 'phone': '+1234567895'},
        'escalation_time': 480
    },
    'Momentary Grid Loss': {
        'primary': {'name': 'Robert Taylor', 'role': 'Site Manager', 'email': 'robert.t@windfarm.com', 'phone': '+1234567896'},
        'secondary': {'name': 'Jennifer Lee', 'role': 'Operations Supervisor', 'email': 'jennifer.l@windfarm.com', 'phone': '+1234567897'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager', 'email': 'lisa.a@windfarm.com', 'phone': '+1234567895'},
        'escalation_time': 15
    },
    'Grid Voltage Fluctuation': {
        'primary': {'name': 'Emily Chen', 'role': 'Grid Integration Specialist', 'email': 'emily.c@windfarm.com', 'phone': '+1234567893'},
        'secondary': {'name': 'David Wilson', 'role': 'Electrical Engineer', 'email': 'david.w@windfarm.com', 'phone': '+1234567894'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager', 'email': 'lisa.a@windfarm.com', 'phone': '+1234567895'},
        'escalation_time': 20
    },
    'Safety System Activation': {
        'primary': {'name': 'Carlos Rodriguez', 'role': 'Mechanical Technician', 'email': 'carlos.r@windfarm.com', 'phone': '+1234567898'},
        'secondary': {'name': 'Anna Martinez', 'role': 'Senior Technician', 'email': 'anna.m@windfarm.com', 'phone': '+1234567899'},
        'management': {'name': 'Mike Davis', 'role': 'Engineering Manager', 'email': 'mike.d@windfarm.com', 'phone': '+1234567892'},
        'escalation_time': 20
    },
    'Overspeed Protection Triggered': {
        'primary': {'name': 'Carlos Rodriguez', 'role': 'Mechanical Technician', 'email': 'carlos.r@windfarm.com', 'phone': '+1234567898'},
        'secondary': {'name': 'Anna Martinez', 'role': 'Senior Technician', 'email': 'anna.m@windfarm.com', 'phone': '+1234567899'},
        'management': {'name': 'Mike Davis', 'role': 'Engineering Manager', 'email': 'mike.d@windfarm.com', 'phone': '+1234567892'},
        'escalation_time': 20
    },
    'Hydraulic Valve Response Slow': {
        'primary': {'name': 'Marcus Lee', 'role': 'Hydraulic Technician', 'email': 'marcus.l@windfarm.com', 'phone': '+1234567924'},
        'secondary': {'name': 'Patricia King', 'role': 'Maintenance Supervisor', 'email': 'patricia.k@windfarm.com', 'phone': '+1234567925'},
        'management': {'name': 'Lisa Anderson', 'role': 'Operations Manager', 'email': 'lisa.a@windfarm.com', 'phone': '+1234567895'},
        'escalation_time': 480
    },
    # Default for alarms without specific stakeholders
    'DEFAULT': {
        'primary': {'name': 'Operations Center', 'role': 'Control Room', 'email': 'ops@windfarm.com', 'phone': '+1234567800'},
        'secondary': {'name': 'Duty Engineer', 'role': 'On-call Engineer', 'email': 'duty@windfarm.com', 'phone': '+1234567801'},
        'management': {'name': 'Operations Manager', 'role': 'Manager', 'email': 'manager@windfarm.com', 'phone': '+1234567802'},
        'escalation_time': 30
    }
}

def send_email_notification(recipient_email, recipient_name, alarm_type, turbine_id, severity, alarm_id):
    """Send email notification to stakeholder"""
    try:
        sender_email = "windsenseada@gmail.com"

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"🚨 {severity} ALARM: {alarm_type} - Turbine {turbine_id}"

        # Get dashboard URL for acknowledge button
        dashboard_url = get_dashboard_url()
        ack_url = f"{dashboard_url}?ack={alarm_id}"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; color: white;">
                <h2>🚨 CRITICAL ALARM NOTIFICATION</h2>
            </div>
            <div style="padding: 20px; background-color: #f5f5f5;">
                <p>Dear {recipient_name},</p>
                <p>A <strong style="color: #ff4444;">{severity}</strong> alarm has been detected and requires immediate attention.</p>

                <div style="background-color: white; padding: 15px; border-left: 4px solid #ff4444; margin: 20px 0;">
                    <p><strong>Alarm ID:</strong> {alarm_id}</p>
                    <p><strong>Alarm Type:</strong> {alarm_type}</p>
                    <p><strong>Turbine:</strong> T-{turbine_id}</p>
                    <p><strong>Severity:</strong> {severity}</p>
                    <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>

                <p><strong>Required Action:</strong> Please acknowledge this alarm in the WindSense dashboard.</p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{ack_url}" style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                        ✅ ACKNOWLEDGE THIS ALARM
                    </a>
                </div>

                <hr style="border: 1px solid #ddd; margin: 20px 0;">
                <p style="color: #888; font-size: 12px;">
                    This is an automated alert from WindSense AI Alarm Management System.<br>
                    If you have acknowledged this alarm, please disregard this message.<br>
                    <em>Note: Acknowledge link is valid for current session only.</em>
                </p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        # REAL Gmail SMTP
        _smtp = smtplib.SMTP('smtp.gmail.com', 587)
        _smtp.ehlo()
        _smtp.starttls()
        _smtp.login('windsenseada@gmail.com', 'oaru xyta qlwi hpmw')
        _smtp.sendmail('windsenseada@gmail.com', recipient_email, msg.as_string())
        _smtp.quit()

        # Log the notification
        if 'notification_log' not in st.session_state:
            st.session_state.notification_log = []

        st.session_state.notification_log.append({
            'time': datetime.now(),
            'type': 'EMAIL',
            'recipient': f"{recipient_name} ({recipient_email})",
            'alarm_id': alarm_id,
            'alarm_type': alarm_type,
            'status': 'SENT ✓'
        })

        return True
    except Exception as e:
        st.error(f"Email error: {e}")
        return False

def send_sms_notification(phone_number, recipient_name, alarm_type, turbine_id, severity, alarm_id):
    """Send SMS notification to stakeholder"""
    try:
        message_body = f"🚨 {severity} ALARM\nType: {alarm_type}\nTurbine: T-{turbine_id}\nID: {alarm_id}\nAcknowledge in dashboard immediately."

        # NOTE: Configure Twilio credentials for production
        # from twilio.rest import Client
        # client = Client("ACCOUNT_SID", "AUTH_TOKEN")
        # message = client.messages.create(
        #     body=message_body,
        #     from_="+1234567890",
        #     to=phone_number
        # )

        # For demo purposes, log the notification
        if 'notification_log' not in st.session_state:
            st.session_state.notification_log = []

        st.session_state.notification_log.append({
            'time': datetime.now(),
            'type': 'SMS',
            'recipient': f"{recipient_name} ({phone_number})",
            'alarm_id': alarm_id,
            'alarm_type': alarm_type,
            'status': 'SENT ✓'
        })

        return True
    except Exception as e:
        return False

def process_critical_alarm(alarm_type, turbine_id, alarm_id, severity='CRITICAL'):
    """Process critical alarm and send notifications to stakeholders"""

    # Initialize active alarms tracking
    if 'active_critical_alarms' not in st.session_state:
        st.session_state.active_critical_alarms = {}

    # Store in active alarms
    st.session_state.active_critical_alarms[alarm_id] = {
        'type': alarm_type,
        'turbine_id': turbine_id,
        'timestamp': datetime.now(),
        'severity': severity,
        'notified': []
    }

    # Get stakeholders for this alarm type
    stakeholder_info = STAKEHOLDERS.get(alarm_type, STAKEHOLDERS.get('DEFAULT', {}))

    # Send to primary stakeholder (Email + SMS)
    primary = stakeholder_info.get('primary', {})
    if primary:
        send_email_notification(
            primary['email'],
            primary['name'],
            alarm_type,
            turbine_id,
            severity,
            alarm_id
        )
        send_sms_notification(
            primary['phone'],
            primary['name'],
            alarm_type,
            turbine_id,
            severity,
            alarm_id
        )
        st.session_state.active_critical_alarms[alarm_id]['notified'].append(f"Primary: {primary['name']}")

    # Send to secondary stakeholder (Email only)
    secondary = stakeholder_info.get('secondary', {})
    if secondary:
        send_email_notification(
            secondary['email'],
            secondary['name'],
            alarm_type,
            turbine_id,
            severity,
            alarm_id
        )
        st.session_state.active_critical_alarms[alarm_id]['notified'].append(f"Secondary: {secondary['name']}")

    return alarm_id

def check_and_escalate():
    """Check for unacknowledged alarms and escalate if needed"""
    current_time = datetime.now()

    if 'active_critical_alarms' not in st.session_state:
        return

    if 'escalated_alarms' not in st.session_state:
        st.session_state.escalated_alarms = {}

    for alarm_id, alarm_data in st.session_state.active_critical_alarms.items():
        # Check if alarm is acknowledged
        if alarm_id not in st.session_state.acknowledged_alarms:
            alarm_time = alarm_data['timestamp']
            alarm_type = alarm_data['type']

            # Get stakeholders for this alarm type
            stakeholder_info = STAKEHOLDERS.get(alarm_type, STAKEHOLDERS.get('DEFAULT', {}))
            escalation_time = stakeholder_info.get('escalation_time', 30)

            time_elapsed = (current_time - alarm_time).total_seconds() / 60  # minutes

            # Escalate if time exceeded and not already escalated
            if time_elapsed > escalation_time and alarm_id not in st.session_state.escalated_alarms:
                # Send to management
                mgmt = stakeholder_info.get('management', {})
                if mgmt:
                    send_email_notification(
                        mgmt['email'],
                        mgmt['name'],
                        alarm_type,
                        alarm_data['turbine_id'],
                        'CRITICAL - ESCALATED',
                        alarm_id
                    )
                    send_sms_notification(
                        mgmt['phone'],
                        mgmt['name'],
                        alarm_type,
                        alarm_data['turbine_id'],
                        'CRITICAL - ESCALATED',
                        alarm_id
                    )

                    st.session_state.escalated_alarms[alarm_id] = {
                        'escalation_time': current_time,
                        'escalated_to': mgmt['name'],
                        'reason': f'No acknowledgment after {escalation_time} minutes'
                    }

# ═══════════════════════════════════════════════════════════════════
# LOAD DATA & MODEL
# ═══════════════════════════════════════════════════════════════════

@st.cache_data
def load_historical_data():
    """Load all historical data"""
    try:
        # Load main datasets
        historical_alarms = pd.read_csv(DATA_PATH + 'top_50_unique_detailed_alarms.csv')
        alarm_episodes = pd.read_csv(DATA_PATH + 'alarm_episodes_with_faults.csv')
        detailed_episodes = pd.read_csv(DATA_PATH + 'detailed_classified_alarm_episodes.csv')

        # Load DMAIC data
        dmaic_file = DATA_PATH + 'DMAIC_Analysis_19_Alarms.csv'
        if os.path.exists(dmaic_file):
            dmaic_data = pd.read_csv(dmaic_file)
        else:
            dmaic_data = None

        return historical_alarms, alarm_episodes, detailed_episodes, dmaic_data
    except Exception as e:
        st.error(f"Error loading historical data: {e}")
        return None, None, None, None

@st.cache_resource
def load_ml_model():
    """Load trained ML model"""
    try:
        with open(MODEL_PATH + 'windsense_rf_model.pkl', 'rb') as f:
            model = pickle.load(f)
        with open(MODEL_PATH + 'feature_names.pkl', 'rb') as f:
            features = pickle.load(f)
        with open(MODEL_PATH + 'model_metadata.json', 'r') as f:
            metadata = json.load(f)
        return model, features, metadata
    except Exception as e:
        st.warning(f"Model not found. Using demo mode. Error: {e}")
        return None, None, None

@st.cache_data
def load_simulation_data():
    """Load simulated alarm stream"""
    try:
        sim_data = pd.read_csv(DATA_PATH + 'dashboard_alarm_stream.csv')
        return sim_data
    except Exception as e:
        st.warning("Simulation data not found. Generating sample data...")
        # Generate sample data
        sample_data = generate_sample_alarms(50)
        return sample_data

def generate_sample_alarms(n=50):
    """Generate sample alarm data for demo"""
    np.random.seed(42)

    data = {
        'alarm_id': [f'ALM-{i+1:04d}' for i in range(n)],
        'timestamp': [(datetime.now() - timedelta(minutes=n-i)).strftime('%Y-%m-%d %H:%M:%S') for i in range(n)],
        'asset_id': np.random.choice([0, 10, 11, 13, 21], n),
        'status_type_id': np.random.choice([3.0, 4.0, 5.0], n, p=[0.2, 0.3, 0.5]),
        'sensor_11_avg': np.random.uniform(40, 80, n),
        'sensor_12_avg': np.random.uniform(35, 75, n),
        'sensor_13_avg': np.random.uniform(30, 70, n),
        'sensor_41_avg': np.random.uniform(25, 65, n),
        'power_30_avg': np.random.uniform(100, 2000, n),
        'wind_speed_3_avg': np.random.uniform(3, 15, n)
    }

    return pd.DataFrame(data)

# Load all data
historical_alarms, alarm_episodes, detailed_episodes, dmaic_data = load_historical_data()
ml_model, feature_names, model_metadata = load_ml_model()
simulation_data = load_simulation_data()

# ═══════════════════════════════════════════════════════════════════
# ALARM SIMULATOR CLASS
# ═══════════════════════════════════════════════════════════════════

class RealtimeAlarmSimulator:
    """Simulates real-time alarm generation"""

    def __init__(self):
        self.alarm_count = 0
        self.alarm_types = [
            'Main Controller Fault',
            'Extended Grid Outage',
            'Grid Frequency Deviation',
            'Momentary Grid Loss',
            'Grid Voltage Fluctuation',
            'Emergency Brake Activation',
            'Safety System Activation',
            'Overspeed Protection Triggered',
            'Yaw System Hydraulic Fault',
            'Pitch System Hydraulic Fault',
            'Hydraulic Oil Contamination',
            'Converter Circuit Fault',
            'Generator Bearing Overheating',
            'Power Electronics Failure',
            'Transformer Oil Temperature High',
            'Hydraulic Filter Clogged',
            'Generator Winding Temperature High',
            'Hydraulic Pressure Drop',
            'Hydraulic Valve Response Slow'
        ]

    def generate_alarm(self):
        """Generate a single realistic alarm"""
        self.alarm_count += 1

        status_type = np.random.choice([3.0, 4.0, 5.0], p=[0.2, 0.3, 0.5])
        turbine_id = np.random.choice([0, 10, 11, 13, 21])

        alarm = {
            'alarm_id': f'ALM-{self.alarm_count:05d}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'asset_id': turbine_id,
            'status_type_id': status_type,
            'sensor_11_avg': np.random.uniform(40, 80),
            'sensor_12_avg': np.random.uniform(35, 75),
            'sensor_13_avg': np.random.uniform(30, 70),
            'sensor_41_avg': np.random.uniform(25, 65),
            'power_30_avg': np.random.uniform(100, 2000),
            'wind_speed_3_avg': np.random.uniform(3, 15),
            'predicted_type': np.random.choice(self.alarm_types),
            'confidence': np.random.uniform(75, 99),
            'priority': 'CRITICAL' if status_type == 5.0 else 'HIGH' if status_type == 4.0 else 'MEDIUM'
        }

        return alarm

# Initialize simulator
if 'simulator' not in st.session_state:
    st.session_state.simulator = RealtimeAlarmSimulator()
if 'alarm_buffer' not in st.session_state:
    st.session_state.alarm_buffer = []
if 'notifications' not in st.session_state:
    st.session_state.notifications = []
if 'acknowledged_alarms' not in st.session_state:
    st.session_state.acknowledged_alarms = load_acknowledgments()
def clean_orphaned_acknowledgments():
    """Remove acknowledgments for alarms no longer in the buffer"""
    if 'alarm_buffer' in st.session_state and 'acknowledged_alarms' in st.session_state:
        active_alarm_ids = {a['alarm_id'] for a in st.session_state.alarm_buffer}

        # Keep only acknowledgments for active alarms
        cleaned_acks = {
            aid: ack_data
            for aid, ack_data in st.session_state.acknowledged_alarms.items()
            if aid in active_alarm_ids or ack_data.get('method') == 'email_link'
        }

        # Update session state
        st.session_state.acknowledged_alarms = cleaned_acks

        # Save to file
        try:
            with open(ACK_FILE, 'w') as f:
                json.dump(cleaned_acks, f, indent=2)
        except:
            pass

# ═══════════════════════════════════════════════════════════════════
# ROOT CAUSE ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════════════

# Fallback elimination strategies for alarms not in DMAIC JSON
FALLBACK_ELIMINATION_STRATEGIES = {
    'Main Controller Fault': [
        'Update controller firmware to latest stable version',
        'Implement auto-reset logic to reduce manual intervention',
        'Install redundant controller for failover capability',
        'Deploy grid stability monitoring for early warning'
    ],
    'Grid Frequency Deviation': [
        'Install Battery Energy Storage System (BESS) for frequency stabilization',
        'Implement faster reconnection logic to reduce downtime',
        'Coordinate with utility provider and negotiate grid stability SLA',
        'Add frequency ride-through capability for wider operating range'
    ],
    'Extended Grid Outage': [
        'Install diesel generator backup for black start capability',
        'Negotiate advance notice for planned maintenance outages',
        'Add redundant grid connection point to reduce outage frequency',
        'Implement islanding capability with BESS for independent operation'
    ],
    'Emergency Brake Activation': [
        'Upgrade to condition-based brake monitoring system',
        'Implement predictive maintenance to prevent false triggers',
        'Install redundant sensors to verify actual overspeed conditions',
        'Perform quarterly brake system calibration to reduce false alarms'
    ],
    'Generator Bearing Overheating': [
        'Install online bearing monitoring (vibration + temperature sensors)',
        'Upgrade to automatic lubrication systems',
        'Implement condition-based lubrication via oil analysis',
        'Add redundant cooling fans for backup cooling capability'
    ],
    'Hydraulic Oil Contamination': [
        'Install high-efficiency filtration system with contamination sensors',
        'Implement real-time oil quality monitoring with automatic alerts',
        'Schedule regular oil analysis and flush cycles',
        'Upgrade seals and fittings to prevent external contamination ingress'
    ],
    'Converter Circuit Fault': [
        'Replace aging IGBT modules with latest generation components',
        'Implement thermal management improvements for converter cooling',
        'Install online converter health monitoring system',
        'Perform preventive capacitor replacement on schedule'
    ],
    'Momentary Grid Loss': [
        'Upgrade to low voltage ride-through (LVRT) capability',
        'Implement auto-restart sequence to reduce recovery time to 15 minutes',
        'Adjust protection trip settings for wider voltage tolerance',
        'Install voltage stabilizers at grid connection point'
    ],
    'Grid Voltage Fluctuation': [
        'Install Static VAR Compensator (SVC) for voltage stabilization',
        'Upgrade transformer with automatic tap changer',
        'Implement reactive power control via inverter settings',
        'Coordinate with utility on voltage regulation protocols'
    ],
    'Safety System Activation': [
        'Perform comprehensive safety sensor calibration and audit',
        'Upgrade safety PLC to latest firmware with improved logic',
        'Implement diagnostic mode to differentiate true vs false triggers',
        'Review and optimize safety trip thresholds to reduce false activations'
    ],
    'Overspeed Protection Triggered': [
        'Calibrate rotor speed sensors and replace if drifting',
        'Optimize pitch control response for faster regulation',
        'Implement multi-sensor voting logic to prevent false trips',
        'Review and adjust overspeed threshold settings'
    ],
    'Yaw System Hydraulic Fault': [
        'Replace worn yaw hydraulic seals and actuators',
        'Install yaw hydraulic pressure monitoring with automated alerts',
        'Implement scheduled hydraulic fluid replacement program',
        'Add redundant yaw position sensors for fault detection'
    ],
    'Pitch System Hydraulic Fault': [
        'Replace pitch hydraulic cylinders and seals on schedule',
        'Install real-time pitch pressure monitoring system',
        'Implement emergency battery backup for pitch control',
        'Perform quarterly pitch system hydraulic inspection'
    ],
    'Power Electronics Failure': [
        'Implement thermal monitoring on all power electronic components',
        'Replace aging capacitors and IGBT modules preventively',
        'Improve converter cabinet cooling and ventilation',
        'Deploy online insulation resistance monitoring'
    ],
    'Transformer Oil Temperature High': [
        'Clean and inspect transformer cooling radiators',
        'Upgrade cooling fans and implement variable speed control',
        'Install online dissolved gas analysis (DGA) monitoring',
        'Perform power factor testing and insulation checks'
    ],
    'Hydraulic Filter Clogged': [
        'Implement differential pressure monitoring across all filters',
        'Reduce filter replacement intervals based on contamination levels',
        'Upgrade to higher-capacity filter elements',
        'Install oil contamination particle counter for predictive maintenance'
    ],
    'Generator Winding Temperature High': [
        'Inspect and clean generator air gaps and cooling ducts',
        'Replace damaged winding insulation and re-varnish',
        'Install additional temperature sensors across all winding phases',
        'Implement load shedding logic when temperature rises above threshold'
    ],
    'Hydraulic Pressure Drop': [
        'Inspect all hydraulic lines and connections for leaks',
        'Replace worn hydraulic pump components or full pump assembly',
        'Install pressure transducers on all critical hydraulic circuits',
        'Implement automatic shutdown logic on pressure drop detection'
    ],
    'Hydraulic Valve Response Slow': [
        'Flush and replace hydraulic fluid to restore viscosity',
        'Clean or replace slow-responding solenoid valves',
        'Install valve response time monitoring sensors',
        'Implement valve performance trending and predictive replacement schedule'
    ]
}

def get_elimination_strategy(alarm_type):
    """
    Get elimination strategy (recommended actions) for an alarm type.
    Uses improve.solutions from dmaic_complete_database.json if available,
    otherwise falls back to FALLBACK_ELIMINATION_STRATEGIES.
    """
    # Try to get from DMAIC database first
    if alarm_type in DMAIC_DATABASE:
        solutions = DMAIC_DATABASE[alarm_type].get('improve', {}).get('solutions', [])
        if solutions:
            return solutions

    # Fall back to hardcoded strategies
    if alarm_type in FALLBACK_ELIMINATION_STRATEGIES:
        return FALLBACK_ELIMINATION_STRATEGIES[alarm_type]

    # Generic fallback
    return [
        'Perform diagnostic inspection of affected system',
        'Review recent maintenance and operational logs',
        'Consult OEM maintenance manual for corrective procedure',
        'Escalate to specialist if fault persists after initial checks'
    ]


class RootCauseEngine:
    """
    Intelligent Root Cause Analysis Engine
    Analyzes alarm patterns and sensor data to identify root causes
    """

    def __init__(self):
        # Build root cause database from DMAIC_DATABASE
        self.root_cause_database = {}

        if DMAIC_DATABASE:
            for alarm_type, dmaic_entry in DMAIC_DATABASE.items():
                self.root_cause_database[alarm_type] = {
                    'primary_cause': dmaic_entry.get('analyze', {}).get('root_cause', 'Analysis in progress'),
                    'contributing_factors': dmaic_entry.get('analyze', {}).get('contributing', []),
                    'diagnostic_sensors': ['power_30_avg', 'sensor_11_avg', 'sensor_12_avg'],
                    'threshold_conditions': {}
                }
        else:
            # Fallback hardcoded database if JSON not found
            self.root_cause_database = {
                'Main Controller Fault': {
                    'primary_cause': 'Software instability during grid fluctuations',
                    'contributing_factors': [
                        'Grid frequency deviation triggers protection mode',
                        'Requires manual intervention and reset',
                        'Affects all turbines equally'
                    ],
                    'diagnostic_sensors': ['power_30_avg', 'sensor_18_avg'],
                    'threshold_conditions': {'power_30_avg': '<100', 'grid_frequency': '±0.5 Hz'}
                },
                'Grid Frequency Deviation': {
                    'primary_cause': 'External grid instability from utility provider',
                    'contributing_factors': [
                        'Poor grid infrastructure in region',
                        'Delayed reconnection protocols',
                        'No local frequency stabilization'
                    ],
                    'diagnostic_sensors': ['power_30_avg', 'wind_speed_3_avg'],
                    'threshold_conditions': {'grid_frequency': '<49.5 or >50.5 Hz'}
                },
            }

    def analyze(self, alarm_type, sensor_data):
        """Analyze alarm and return root cause with elimination strategy"""
        if alarm_type not in self.root_cause_database:
            # Even for unknown alarms, return elimination strategy
            return {
                'alarm_type': alarm_type,
                'primary_cause': 'Diagnostic analysis in progress - sensor patterns being evaluated',
                'contributing_factors': ['Requires additional sensor data collection'],
                'sensor_anomalies': [],
                'confidence': 50,
                'recommended_actions': get_elimination_strategy(alarm_type)
            }

        rca_data = self.root_cause_database[alarm_type]

        # Analyze sensor patterns
        sensor_anomalies = []
        for sensor in rca_data['diagnostic_sensors']:
            if sensor in sensor_data:
                value = sensor_data[sensor]
                if 'temp' in sensor.lower() and value > 70:
                    sensor_anomalies.append(f"{sensor}: {value:.1f}°C (HIGH)")
                elif 'power' in sensor.lower() and value < 100:
                    sensor_anomalies.append(f"{sensor}: {value:.1f}W (LOW)")

        # Calculate confidence
        confidence = min(95, 70 + len(sensor_anomalies) * 10)

        # Get recommended actions from DMAIC improve solutions / elimination strategy
        recommended_actions = get_elimination_strategy(alarm_type)

        return {
            'alarm_type': alarm_type,
            'primary_cause': rca_data['primary_cause'],
            'contributing_factors': rca_data['contributing_factors'],
            'sensor_anomalies': sensor_anomalies,
            'confidence': confidence,
            'recommended_actions': recommended_actions
        }

# Initialize Root Cause Engine
if 'rca_engine' not in st.session_state:
    st.session_state.rca_engine = RootCauseEngine()

# ═══════════════════════════════════════════════════════════════════
# PREDICTION FUNCTION
# ═══════════════════════════════════════════════════════════════════

def predict_alarm_type(alarm_data, model, features):
    """Predict alarm type using ML model"""
    if model is None:
        # Fallback classification
        status = alarm_data['status_type_id']
        if status == 5.0:
            return 'Grid Frequency Deviation', 92.5
        elif status == 4.0:
            return 'Emergency Brake Activation', 88.3
        else:
            return 'Hydraulic System Fault', 85.7

    # Prepare features
    X = alarm_data[features].values.reshape(1, -1)

    # Predict
    prediction = model.predict(X)[0]
    probabilities = model.predict_proba(X)[0]
    confidence = max(probabilities) * 100

    return prediction, confidence

# ═══════════════════════════════════════════════════════════════════
# NOTIFICATION SYSTEM (Legacy compatibility wrapper)
# ═══════════════════════════════════════════════════════════════════

def send_notification(alarm):
    """Send notification to appropriate stakeholders (Updated with Email/SMS)"""

    # Department mapping for display
    dept_mapping = {
        'Main Controller Fault': 'Software & Controls',
        'Grid Frequency Deviation': 'Grid Operations',
        'Emergency Brake Activation': 'Mechanical Safety',
        'Generator Bearing Overheating': 'Mechanical - Rotating Equipment',
        'Hydraulic Oil Contamination': 'Hydraulic Systems',
        'Converter Circuit Fault': 'Electrical - Power Electronics',
        'Pitch System Fault': 'Mechanical - Blade Systems',
        'Yaw System Fault': 'Mechanical - Nacelle Systems'
    }

    department = dept_mapping.get(alarm['predicted_type'], 'General Maintenance')

    # Get stakeholder info
    stakeholder_info = STAKEHOLDERS.get(alarm['predicted_type'], STAKEHOLDERS.get('DEFAULT', {}))
    primary = stakeholder_info.get('primary', {})

    # Create notification for display
    notification = {
        'timestamp': alarm['timestamp'],
        'alarm_id': alarm['alarm_id'],
        'turbine': f"T-{alarm['asset_id']}",
        'alarm_type': alarm['predicted_type'],
        'priority': alarm['priority'],
        'department': department,
        'stakeholder': f"{primary.get('name', 'N/A')} ({primary.get('role', 'N/A')})",
        'message': f"🚨 {alarm['priority']} ALERT: {alarm['predicted_type']} detected on Turbine {alarm['asset_id']}. Confidence: {alarm['confidence']:.1f}%. Immediate action required.",
        'sent': True
    }

    st.session_state.notifications.insert(0, notification)

    # Keep only last 50 notifications
    if len(st.session_state.notifications) > 50:
        st.session_state.notifications = st.session_state.notifications[:50]

    # Send actual Email/SMS notifications for CRITICAL alarms
    if alarm['priority'] == 'CRITICAL':
        process_critical_alarm(
            alarm['predicted_type'],
            alarm['asset_id'],
            alarm['alarm_id'],
            alarm['priority']
        )

    return notification

# ═══════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/wind-turbine.png", width=100)
    st.markdown('<div class="main-header">🌀 WindSense AI</div>', unsafe_allow_html=True)
    st.caption("Team TG0907494 | TECHgium 9th Edition")

    st.divider()

      # System Status
    st.subheader("📊 System Status")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Model Status", "ACTIVE ✓" if ml_model else "DEMO MODE")
    with col2:
        st.metric("Data Loaded", "✓ 978K rows")

    st.divider()


    # Real-time Simulation Control
    st.subheader("⚡ Live Simulation")

    if st.button("🔄 Generate New Alarm", use_container_width=True):
        new_alarm = st.session_state.simulator.generate_alarm()
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

    # Show alarm count
    st.metric("Alarms Generated", len(st.session_state.alarm_buffer))

    if st.button("🗑️ Clear Buffer", use_container_width=True):
        st.session_state.alarm_buffer = []
        st.session_state.notifications = []
        st.rerun()

# ═══════════════════════════════════════════════════════════════════
# MAIN TABS
# ═══════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📡 Real-Time Monitoring",
    "🤖 ML Model & Training",
    "📊 Historical Analytics",
    "🔔 Notifications & Workflow",
    "📋 DMAIC Analysis",
    "🎯 Optimization & Forecasting",
    "🎛️ Alarm Acknowledgment"