import streamlit as st
import hashlib
import json
import os
from datetime import datetime

USERS = {
    "admin": {
        "password_hash": hashlib.sha256("windsense2026".encode()).hexdigest(),
        "role": "Admin",
        "name": "Wind Farm Admin",
        "email": "windsenseada@gmail.com"
    },
    "teamtg": {
        "password_hash": hashlib.sha256("TECHgium2026".encode()).hexdigest(),
        "role": "Engineer",
        "name": "Team TG0907494",
        "email": "team@tg0907494.com"
    },
    "demo": {
        "password_hash": hashlib.sha256("demo123".encode()).hexdigest(),
        "role": "Viewer",
        "name": "Demo User",
        "email": "demo@windsense.ai"
    }
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_login(username, password):
    username = username.lower().strip()
    if username in USERS:
        if USERS[username]["password_hash"] == hash_password(password):
            return True, USERS[username]
    return False, None

st.set_page_config(
    page_title="WindSense AI — Login",
    page_icon="🌀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Hide sidebar completely
st.markdown("""
<style>
    [data-testid="stSidebarNav"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    header { display: none !important; }
    footer { display: none !important; }

    .stApp { background-color: #0D1B2A; color: white; }
    .main .block-container { background-color: #0D1B2A; }

    [data-testid="stForm"] {
        background: linear-gradient(135deg, #1a2a3a 0%, #0D1B2A 100%);
        border: 1px solid #00C9B1;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 0 30px rgba(0,201,177,0.2);
    }

    h1, h2, h3 { color: #00C9B1 !important; }
    p, label { color: #FFFFFF !important; }

    .stTextInput > div > div > input {
        background-color: #1a2a3a !important;
        border: 1px solid #00C9B1 !important;
        border-radius: 8px !important;
        color: #E8F4FD !important;
        caret-color: #00C9B1 !important;
    }

    .stTextInput > div > div > input:focus {
        border: 1px solid #4FC3F7 !important;
        box-shadow: 0 0 0 2px rgba(0,201,177,0.15) !important;
    }

    div[data-baseweb] { border: none !important; box-shadow: none !important; }

    /* ── Animated particle background ── */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background:
            radial-gradient(ellipse at 20% 50%, rgba(0,201,177,0.08) 0%, transparent 60%),
            radial-gradient(ellipse at 80% 20%, rgba(79,195,247,0.06) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 80%, rgba(0,77,64,0.10) 0%, transparent 60%);
        animation: bgPulse 8s ease-in-out infinite alternate;
        pointer-events: none;
        z-index: 0;
    }
    @keyframes bgPulse {
        0%   { opacity: 0.6; transform: scale(1); }
        100% { opacity: 1.0; transform: scale(1.04); }
    }

    /* ── Fix invisible white form buttons ── */
    .stFormSubmitButton > button,
    .stButton > button {
        background: linear-gradient(135deg, #004D40, #00796B) !important;
        color: #FFFFFF !important;
        border: 1px solid #00C9B1 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 0.5rem 1rem !important;
    }
    .stFormSubmitButton > button:hover,
    .stButton > button:hover {
        background: linear-gradient(135deg, #00796B, #00C9B1) !important;
        color: #0D1B2A !important;
    }

    /* ── Remove emoji clutter from expanders ── */
    .streamlit-expanderHeader {
        background-color: #1a2a3a !important;
        color: #00C9B1 !important;
        border: 1px solid #2a3a4a !important;
        border-radius: 6px !important;
        font-size: 0.95rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Process ACK links WITHOUT requiring login ────────────────────
import json, os
from datetime import datetime

ACK_FILE = os.path.join(os.path.dirname(os.path.abspath('app.py')), 'data', 'acknowledgments.json')

def _load_acks():
    if os.path.exists(ACK_FILE):
        try:
            with open(ACK_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_ack(alarm_id, ack_data):
    try:
        acks = _load_acks()
        acks[alarm_id] = ack_data
        with open(ACK_FILE, 'w') as f:
            json.dump(acks, f, indent=2)
        return True
    except Exception:
        return False

ack_id = st.query_params.get('ack', '')
channel = st.query_params.get('channel', 'email')

if ack_id:
    existing = _load_acks()
    if ack_id in existing:
        prev = existing[ack_id]
        st.markdown(f"""
        <div style="text-align:center; padding:50px;">
            <h1 style="color:#FF8800;">⚠️ Already Acknowledged</h1>
            <p style="font-size:1.5rem;">Alarm <strong>{ack_id}</strong> was already acknowledged.</p>
            <p style="color:#aaa;">At: {prev.get('time', prev.get('ack_time', 'Unknown'))}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        ack_data = {
            'time':     datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'method':   f'{channel}_link',
            'channel':  channel,
            'alarm_id': ack_id
        }
        if _save_ack(ack_id, ack_data):
            st.markdown(f"""
            <div style="text-align:center; padding:50px;">
                <h1 style="color:#4CAF50;">✅ Acknowledged!</h1>
                <p style="font-size:1.5rem;">Alarm <strong>{ack_id}</strong> has been acknowledged.</p>
                <p style="color:#aaa;">At: {ack_data['time']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.balloons()
        else:
            st.error("❌ Failed to save acknowledgment.")
    st.stop()

# Redirect if already logged in
if st.session_state.get('authenticated', False):
    st.switch_page("pages/1_Realtime.py")

# Logo
try:
    import base64
    logo_bytes = open('assets/windsense_logo_full.png', 'rb').read()
    logo_b64 = base64.b64encode(logo_bytes).decode()
    st.markdown(f"""
    <div style='text-align:center; margin-bottom:1rem;'>
        <img src='data:image/png;base64,{logo_b64}' width='300'/>
    </div>
    """, unsafe_allow_html=True)
except:
    st.markdown("<h1 style='text-align:center; color:#00C9B1;'>🌀 WindSense AI</h1>", unsafe_allow_html=True)

st.markdown("<p style='text-align:center; color:#4FC3F7;'>Team TG0907494 | TECHgium 9th Edition</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#6B8FA8;'>Intelligent Alarm Classification & Optimization</p>", unsafe_allow_html=True)

st.divider()

# Pending acknowledgment notice
pending_ack = st.session_state.get('pending_ack', '')
if pending_ack:
    st.info(f"🔔 You're acknowledging alarm **{pending_ack}**. Please log in.")

# Login form
with st.form("login_form"):
    st.subheader("Sign In")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    submit = st.form_submit_button("Login", use_container_width=True)

    if submit:
        if username and password:
            success, user_data = verify_login(username, password)
            if success:
                st.session_state.authenticated = True
                st.session_state.username = user_data['name']
                st.session_state.user_role = user_data['role']
                st.session_state.user_email = user_data.get('email', '')
                st.session_state.login_time = datetime.now().isoformat()
                st.session_state.acknowledged_alarms = {}

                st.success(f"Welcome, {user_data['name']}!")
                import time
                time.sleep(1)
                st.switch_page("pages/1_Realtime.py")
            else:
                st.error("Invalid username or password.")
        else:
            st.warning("Enter username and password.")

st.divider()

# ===== FORGOT PASSWORD =====
with st.expander("Forgot Password?"):
    st.write("Enter your registered email address.")

    reset_email = st.text_input("Email Address", key="reset_email")

    if st.button("Send Reset Link"):
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        known_emails = {
            "windsenseada@gmail.com": "Wind Farm Admin",
            "team@tg0907494.com": "Team TG0907494",
            "demo@windsense.ai": "Demo User",
            "ts.aparajithaa@gmail.com": "Aparajithaa"
        }

        if reset_email and reset_email.lower() in known_emails:
            try:
                sender = "windsenseada@gmail.com"
                app_password = "oaru xyta qlwi hpmw"

                msg = MIMEMultipart()
                msg['From'] = sender
                msg['To'] = reset_email
                msg['Subject'] = "WindSense AI — Password Reset"

                body = f"""
                Dear {known_emails[reset_email.lower()]},

                A password reset was requested.

                Dashboard:
                https://windsense-ai.streamlit.app

                Contact admin for password reset.

                WindSense AI Team
                """

                msg.attach(MIMEText(body, 'plain'))

                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(sender, app_password)
                server.sendmail(sender, reset_email, msg.as_string())
                server.quit()

                st.success("✅ Email sent successfully!")

            except Exception as e:
                st.error(f"❌ Error: {e}")
        else:
            st.warning("Email not found.")

st.divider()

# Demo credentials
with st.expander("Demo Credentials"):
    st.write("demo / demo123")
    st.write("teamtg / TECHgium2026")
    st.write("admin / windsense2026")

st.markdown("""
<div style='text-align:center; color:#4FC3F7; font-size:0.8rem;'>
WindSense AI © 2026 | TECHgium 9th Edition
</div>
""", unsafe_allow_html=True)