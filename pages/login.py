import streamlit as st
import hashlib
import json
import os
import smtplib
import secrets
import string
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── Constants ─────────────────────────────────────────────────────────────────
SENDER_EMAIL    = "windsenseada@gmail.com"
SENDER_PASSWORD = "oaru xyta qlwi hpmw"
DASHBOARD_URL   = "https://windsense-ai.streamlit.app"
ACK_FILE        = os.path.join(os.path.dirname(os.path.abspath('app.py')), 'data', 'acknowledgments.json')
USERS_FILE      = os.path.join(os.path.dirname(os.path.abspath('app.py')), 'data', 'registered_users.json')

# ── Wind Farm Registry — 5 real farms with secret codes ──────────────────────
WIND_FARMS = {
    "GREENVALE WIND FARM": {
        "secret":      "GVW-2026-SECURE",
        "location":    "Rajasthan, India",
        "turbines":    12,
        "description": "Greenvale Wind Energy Ltd — Rajasthan Operations"
    },
    "COASTAL BREEZE FARM": {
        "secret":      "CBF-SHORE-9981",
        "location":    "Tamil Nadu, India",
        "turbines":    8,
        "description": "Coastal Breeze Power — Tamil Nadu Offshore"
    },
    "HIGHLAND WINDS": {
        "secret":      "HLW-APEX-7742",
        "location":    "Gujarat, India",
        "turbines":    20,
        "description": "Highland Winds Infrastructure — Gujarat Grid"
    },
    "DELTA ENERGY PARK": {
        "secret":      "DEP-DELTA-4456",
        "location":    "Andhra Pradesh, India",
        "turbines":    15,
        "description": "Delta Energy Renewables — AP Southern Corridor"
    },
    "SUMMIT POWER STATION": {
        "secret":      "SPS-MOUNT-3310",
        "location":    "Maharashtra, India",
        "turbines":    10,
        "description": "Summit Power Holdings — Maharashtra Western"
    }
}

# ── Built-in admin accounts (always available) ───────────────────────────────
BUILTIN_USERS = {
    "admin": {
        "password_hash": hashlib.sha256("windsense2026".encode()).hexdigest(),
        "role":       "Admin",
        "name":       "Wind Farm Admin",
        "email":      "windsenseada@gmail.com",
        "wind_farm":  "SYSTEM",
        "builtin":    True
    },
    "teamtg": {
        "password_hash": hashlib.sha256("TECHgium2026".encode()).hexdigest(),
        "role":       "Engineer",
        "name":       "Team TG0907494",
        "email":      "team@tg0907494.com",
        "wind_farm":  "SYSTEM",
        "builtin":    True
    },
    "demo": {
        "password_hash": hashlib.sha256("demo123".encode()).hexdigest(),
        "role":       "Viewer",
        "name":       "Demo User",
        "email":      "demo@windsense.ai",
        "wind_farm":  "SYSTEM",
        "builtin":    True
    }
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_registered_users() -> dict:
    """Load dynamically registered users from JSON file."""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_registered_users(users: dict) -> bool:
    try:
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception:
        return False

def get_all_users() -> dict:
    """Merge built-in users + registered users. Registered users take NO priority over builtins."""
    merged = {}
    merged.update(load_registered_users())
    merged.update(BUILTIN_USERS)   # builtins always win
    return merged

def verify_login(username: str, password: str):
    username = username.lower().strip()
    all_users = get_all_users()
    if username in all_users:
        user = all_users[username]
        if user["password_hash"] == hash_password(password):
            return True, user
    return False, None

def username_exists(username: str) -> bool:
    username = username.lower().strip()
    return username in get_all_users()

def email_registered(email: str) -> bool:
    email = email.lower().strip()
    all_users = get_all_users()
    return any(u.get("email", "").lower() == email for u in all_users.values())

def get_user_by_email(email: str):
    email = email.lower().strip()
    all_users = get_all_users()
    for uname, udata in all_users.items():
        if udata.get("email", "").lower() == email:
            return uname, udata
    return None, None

def verify_farm_secret(farm_name: str, secret: str) -> bool:
    farm = WIND_FARMS.get(farm_name.upper().strip())
    if farm is None:
        return False
    return farm["secret"].upper().strip() == secret.upper().strip()

def generate_temp_password(length=10) -> str:
    chars = string.ascii_letters + string.digits + "!@#$"
    return ''.join(secrets.choice(chars) for _ in range(length))

def send_email(to_email: str, subject: str, html_body: str) -> tuple:
    try:
        msg = MIMEMultipart()
        msg['From']    = SENDER_EMAIL
        msg['To']      = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        server.ehlo()
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        return True, "Sent"
    except Exception as e:
        return False, str(e)

def email_template(title: str, body_html: str) -> str:
    return f"""
    <html><body style="font-family:Arial,sans-serif; background:#0D1B2A; margin:0; padding:0;">
        <div style="max-width:600px; margin:auto; background:#112233;
                    border:1px solid #00C9B1; border-radius:12px; overflow:hidden;">
            <div style="background:linear-gradient(135deg,#003D35,#005C51);
                        padding:24px 28px; border-bottom:2px solid #00C9B1;">
                <h2 style="color:#00C9B1; margin:0; font-size:1.4rem;">🌀 WindSense AI</h2>
                <p style="color:#7FB9D4; margin:4px 0 0 0; font-size:0.9rem;">
                    Intelligent Alarm Management System
                </p>
            </div>
            <div style="padding:28px; color:#D0D8E0;">
                <h3 style="color:#00C9B1; margin-top:0;">{title}</h3>
                {body_html}
            </div>
            <div style="padding:14px 28px; background:#0D1B2A; text-align:center;
                        color:#4FC3F7; font-size:0.78rem; border-top:1px solid #1E3A5F;">
                WindSense AI © 2026 | Team TG0907494 | TECHgium 9th Edition
            </div>
        </div>
    </body></html>
    """

# ── Acknowledgment helpers (no login required) ────────────────────────────────
def _load_acks() -> dict:
    if os.path.exists(ACK_FILE):
        try:
            with open(ACK_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_ack(alarm_id: str, ack_data: dict) -> bool:
    try:
        acks = _load_acks()
        acks[alarm_id] = ack_data
        with open(ACK_FILE, 'w') as f:
            json.dump(acks, f, indent=2)
        return True
    except Exception:
        return False

# ═════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="WindSense AI — Login",
    page_icon="🌀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    [data-testid="stSidebarNav"]    { display: none !important; }
    [data-testid="stSidebar"]       { display: none !important; }
    [data-testid="collapsedControl"]{ display: none !important; }
    section[data-testid="stSidebar"]{ display: none !important; }
    header  { display: none !important; }
    footer  { display: none !important; }

    .stApp { background-color: #0D1B2A; color: white; }
    .main .block-container { background-color: #0D1B2A; max-width: 560px; }

    .stApp::before {
        content: '';
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background:
            radial-gradient(ellipse at 20% 50%, rgba(0,201,177,0.08) 0%, transparent 60%),
            radial-gradient(ellipse at 80% 20%, rgba(79,195,247,0.06) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 80%, rgba(0,77,64,0.10) 0%, transparent 60%);
        animation: bgPulse 8s ease-in-out infinite alternate;
        pointer-events: none; z-index: 0;
    }
    @keyframes bgPulse {
        0%   { opacity: 0.6; transform: scale(1); }
        100% { opacity: 1.0; transform: scale(1.04); }
    }

    h1, h2, h3 { color: #00C9B1 !important; }
    p, label   { color: #FFFFFF !important; }

    .stTextInput > div > div > input,
    .stTextArea  > div > div > textarea,
    .stSelectbox > div > div {
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

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background-color: #0D1B2A;
        border-bottom: 2px solid #00C9B1;
    }
    .stTabs [data-baseweb="tab"] {
        height: 2.8rem;
        font-size: 0.95rem;
        font-weight: 700;
        color: #4FC3F7 !important;
        background-color: #1a2a3a;
        border-radius: 8px 8px 0 0;
        padding: 0 1.5rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00C9B1 !important;
        color: #0D1B2A !important;
    }

    /* Farm card */
    .farm-card {
        background: linear-gradient(135deg, #112233, #1E3A5F);
        border: 1px solid #00C9B1;
        border-radius: 8px;
        padding: 0.7rem 1rem;
        margin: 0.3rem 0;
        color: #D0D8E0;
        font-size: 0.83rem;
    }
    .farm-card strong { color: #00C9B1; }

    /* Step indicator */
    .step-badge {
        display: inline-block;
        background: #00C9B1;
        color: #0D1B2A;
        font-weight: 800;
        font-size: 0.75rem;
        border-radius: 50%;
        width: 22px; height: 22px;
        line-height: 22px;
        text-align: center;
        margin-right: 8px;
    }
    .step-label {
        color: #00C9B1;
        font-weight: 700;
        font-size: 0.9rem;
    }

    /* Arrow-free expanders */
    .ws-help-details {
        background-color: #112233;
        border: 1px solid #1E3A5F;
        border-radius: 8px;
        margin-bottom: 0.4rem;
        overflow: hidden;
    }
    .ws-help-details summary {
        list-style: none !important;
        cursor: pointer;
        padding: 0.5rem 0.85rem;
        color: #4FC3F7;
        font-size: 0.83rem;
        background-color: #112233;
    }
    .ws-help-details summary::-webkit-details-marker { display: none !important; }
    .ws-help-details summary::marker { display: none !important; }
    .ws-help-body {
        padding: 0.6rem 0.85rem;
        color: #D0D8E0;
        font-size: 0.8rem;
        background-color: #0D1B2A;
    }
</style>
""", unsafe_allow_html=True)

# ── Handle ACK links before any login check ───────────────────────────────────
ack_id  = st.query_params.get('ack', '')
channel = st.query_params.get('channel', 'email')

if ack_id:
    existing = _load_acks()
    if ack_id in existing:
        prev = existing[ack_id]
        st.markdown(f"""
        <div style="text-align:center; padding:50px;">
            <h1 style="color:#FF8800;">⚠️ Already Acknowledged</h1>
            <p style="font-size:1.4rem; color:#E8F4FD;">
                Alarm <strong>{ack_id}</strong> was already acknowledged.
            </p>
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
                <p style="font-size:1.4rem; color:#E8F4FD;">
                    Alarm <strong>{ack_id}</strong> has been acknowledged.
                </p>
                <p style="color:#aaa;">At: {ack_data['time']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.balloons()
        else:
            st.error("❌ Failed to save acknowledgment.")
    st.stop()

# ── Redirect if already logged in ─────────────────────────────────────────────
if st.session_state.get('authenticated', False):
    st.switch_page("pages/1_Realtime.py")

# ── Session state defaults ─────────────────────────────────────────────────────
for _key in ['signup_step', 'signup_farm_verified', 'signup_farm_name']:
    if _key not in st.session_state:
        st.session_state[_key] = 0 if _key == 'signup_step' else (False if _key == 'signup_farm_verified' else '')

# ── Logo ──────────────────────────────────────────────────────────────────────
try:
    import base64
    logo_bytes = open('assets/windsense_logo_full.png', 'rb').read()
    logo_b64   = base64.b64encode(logo_bytes).decode()
    st.markdown(f"""
    <div style='text-align:center; margin-bottom:0.8rem;'>
        <img src='data:image/png;base64,{logo_b64}' width='280'/>
    </div>
    """, unsafe_allow_html=True)
except Exception:
    st.markdown("<h1 style='text-align:center; color:#00C9B1;'>🌀 WindSense AI</h1>", unsafe_allow_html=True)

st.markdown("<p style='text-align:center; color:#4FC3F7; margin:0;'>Team TG0907494 | TECHgium 9th Edition</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#6B8FA8; margin:0 0 1rem 0;'>Intelligent Alarm Classification & Optimization</p>", unsafe_allow_html=True)

st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# MAIN TABS — Sign In | Sign Up
# ═════════════════════════════════════════════════════════════════════════════
tab_signin, tab_signup = st.tabs(["🔑  Sign In", "📋  Sign Up"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — SIGN IN
# ─────────────────────────────────────────────────────────────────────────────
with tab_signin:
    pending_ack_notice = st.session_state.get('pending_ack', '')
    if pending_ack_notice:
        st.info(f"🔔 Acknowledging alarm **{pending_ack_notice}** — please log in first.")

    with st.form("login_form"):
        st.markdown("<p style='color:#00C9B1; font-weight:700; font-size:1rem; margin-bottom:0.5rem;'>Sign In to WindSense AI</p>", unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit   = st.form_submit_button("🔑 Login", use_container_width=True)

        if submit:
            if username and password:
                success, user_data = verify_login(username, password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.username      = user_data['name']
                    st.session_state.user_role     = user_data['role']
                    st.session_state.user_email    = user_data.get('email', '')
                    st.session_state.user_farm     = user_data.get('wind_farm', 'SYSTEM')
                    st.session_state.login_time    = datetime.now().isoformat()
                    st.session_state.acknowledged_alarms = {}
                    st.success(f"✅ Welcome, {user_data['name']}!")
                    import time; time.sleep(0.8)
                    st.switch_page("pages/1_Realtime.py")
                else:
                    st.error("❌ Invalid username or password.")
            else:
                st.warning("Please enter both username and password.")

    st.divider()

    # ── Forgot Password ───────────────────────────────────────────────────────
    st.markdown("""
    <details class="ws-help-details" style="margin-top:0.3rem;">
    <summary>🔒 Forgot Password?</summary>
    </details>
    """, unsafe_allow_html=True)

    # Use Streamlit widgets below the fake expander header
    with st.expander("", expanded=False):
        st.markdown("<p style='color:#00C9B1; font-weight:700;'>Reset Your Password</p>", unsafe_allow_html=True)
        st.markdown("<p style='color:#8899AA; font-size:0.82rem;'>Enter your registered email address. If found, a temporary password will be sent to you.</p>", unsafe_allow_html=True)

        reset_email = st.text_input("Registered Email Address", key="reset_email_input", placeholder="you@example.com")

        if st.button("📧 Send Reset Email", key="btn_reset_pw", use_container_width=True):
            if not reset_email.strip():
                st.warning("Please enter your email address.")
            else:
                _uname, _udata = get_user_by_email(reset_email.strip())
                if _uname is None:
                    st.error("❌ Email not found. Please check the address or sign up for a new account.")
                else:
                    temp_pw = generate_temp_password(10)
                    # Update password in registered users file (not for builtins)
                    reg_users = load_registered_users()
                    if _uname in reg_users:
                        reg_users[_uname]['password_hash'] = hash_password(temp_pw)
                        save_registered_users(reg_users)
                        pw_note = f"Your temporary password is: <strong style='color:#00C9B1; font-size:1.1rem; letter-spacing:2px;'>{temp_pw}</strong>"
                    else:
                        pw_note = "Your account uses a system password. Please contact the administrator at windsenseada@gmail.com to reset it."

                    html_body = f"""
                    <p>Dear <strong>{_udata['name']}</strong>,</p>
                    <p>A password reset was requested for your WindSense AI account.</p>
                    <div style="background:#0D1B2A; border-left:4px solid #00C9B1;
                                padding:14px 18px; border-radius:0 8px 8px 0; margin:16px 0;">
                        <p style="margin:0;"><strong>Username:</strong> {_uname}</p>
                        <p style="margin:8px 0 0 0;">{pw_note}</p>
                    </div>
                    <p>Log in at: <a href="{DASHBOARD_URL}" style="color:#00C9B1;">{DASHBOARD_URL}</a></p>
                    <p style="color:#888; font-size:0.85rem;">
                        After logging in, please change your password. If you did not request this reset,
                        contact windsenseada@gmail.com immediately.
                    </p>
                    """
                    ok, err = send_email(
                        reset_email.strip(),
                        "WindSense AI — Password Reset",
                        email_template("Password Reset Request", html_body)
                    )
                    if ok:
                        st.success(f"✅ Reset email sent to {reset_email.strip()}. Check your inbox.")
                    else:
                        st.error(f"❌ Failed to send email: {err}. Please contact windsenseada@gmail.com directly.")

    st.divider()

    # ── Demo credentials ──────────────────────────────────────────────────────
    st.markdown("""
    <details class="ws-help-details">
    <summary>👁️ Demo Credentials (click to reveal)</summary>
    <div class="ws-help-body">
        <strong>demo</strong> / demo123 — Viewer access<br>
        <strong>teamtg</strong> / TECHgium2026 — Engineer access<br>
        <strong>admin</strong> / windsense2026 — Admin access
    </div>
    </details>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — SIGN UP (2-step: Farm Verification → Account Creation)
# ─────────────────────────────────────────────────────────────────────────────
with tab_signup:

    st.markdown("""
    <p style='color:#4FC3F7; font-size:0.85rem; margin-bottom:0.8rem;'>
        New users must first verify their Wind Farm credentials before creating an account.
        Contact your Wind Farm administrator for the farm name and secret code.
    </p>
    """, unsafe_allow_html=True)

    # ── Step progress indicator ───────────────────────────────────────────────
    _step = st.session_state.signup_step
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        _s1_style = "background:#00C9B1; color:#0D1B2A;" if _step >= 0 else "background:#1a2a3a; color:#888;"
        st.markdown(f"""
        <div style="{_s1_style} border-radius:8px; padding:0.5rem 0.8rem; text-align:center;
                    font-weight:700; font-size:0.85rem; border:1px solid #00C9B1;">
            {'✅' if _step > 0 else '①'} Farm Verification
        </div>
        """, unsafe_allow_html=True)
    with col_s2:
        _s2_style = "background:#00C9B1; color:#0D1B2A;" if _step >= 1 else "background:#1a2a3a; color:#888;"
        st.markdown(f"""
        <div style="{_s2_style} border-radius:8px; padding:0.5rem 0.8rem; text-align:center;
                    font-weight:700; font-size:0.85rem; border:1px solid {'#00C9B1' if _step>=1 else '#2a3a4a'};">
            {'✅' if _step > 1 else '②'} Create Account
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # STEP 1 — FARM VERIFICATION
    # ══════════════════════════════════════════════════════════
    if st.session_state.signup_step == 0:
        st.markdown("""
        <span class="step-badge">1</span>
        <span class="step-label">Verify Your Wind Farm</span>
        """, unsafe_allow_html=True)
        st.markdown("<p style='color:#8899AA; font-size:0.82rem; margin:0.3rem 0 0.8rem 0;'>Select your wind farm and enter the secret code provided by your farm administrator.</p>", unsafe_allow_html=True)

        # ── Farm directory ────────────────────────────────────────────────────
        with st.expander("📋 View Registered Wind Farms"):
            for farm_name, farm_info in WIND_FARMS.items():
                st.markdown(f"""
                <div class="farm-card">
                    <strong>{farm_name}</strong><br>
                    📍 {farm_info['location']} &nbsp;|&nbsp;
                    🌀 {farm_info['turbines']} turbines<br>
                    <span style='color:#8899AA;'>{farm_info['description']}</span>
                </div>
                """, unsafe_allow_html=True)

        with st.form("farm_verify_form"):
            farm_options = ["— Select your Wind Farm —"] + list(WIND_FARMS.keys())
            selected_farm = st.selectbox(
                "Wind Farm Name",
                options=farm_options,
                key="farm_select_box"
            )
            farm_secret = st.text_input(
                "Farm Secret Code",
                type="password",
                placeholder="Enter the secret code from your administrator",
                key="farm_secret_input"
            )
            verify_btn = st.form_submit_button("🔓 Verify Farm", use_container_width=True)

            if verify_btn:
                if selected_farm == "— Select your Wind Farm —":
                    st.error("Please select your wind farm.")
                elif not farm_secret.strip():
                    st.error("Please enter the farm secret code.")
                elif not verify_farm_secret(selected_farm, farm_secret.strip()):
                    st.error("❌ Incorrect secret code for this farm. Contact your administrator.")
                else:
                    st.session_state.signup_step      = 1
                    st.session_state.signup_farm_name = selected_farm
                    st.session_state.signup_farm_verified = True
                    st.success(f"✅ Farm verified: {selected_farm}")
                    import time; time.sleep(0.6)
                    st.rerun()

    # ══════════════════════════════════════════════════════════
    # STEP 2 — CREATE ACCOUNT
    # ══════════════════════════════════════════════════════════
    elif st.session_state.signup_step == 1:
        farm_name = st.session_state.signup_farm_name
        farm_info = WIND_FARMS.get(farm_name, {})

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#003D35,#005C51);
                    border:1px solid #00C9B1; border-radius:8px;
                    padding:0.6rem 1rem; margin-bottom:0.8rem;">
            <span style="color:#00C9B1; font-weight:700;">✅ Verified Farm:</span>
            <span style="color:#E8F4FD; margin-left:8px;">{farm_name}</span>
            <span style="color:#7FB9D4; margin-left:12px; font-size:0.82rem;">
                📍 {farm_info.get('location','')}&nbsp;|&nbsp;
                🌀 {farm_info.get('turbines','')} turbines
            </span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <span class="step-badge">2</span>
        <span class="step-label">Create Your Account</span>
        """, unsafe_allow_html=True)
        st.markdown("<p style='color:#8899AA; font-size:0.82rem; margin:0.3rem 0 0.8rem 0;'>Your account will be linked to this wind farm. Use your work email address as your username login.</p>", unsafe_allow_html=True)

        with st.form("signup_form"):
            full_name = st.text_input(
                "Full Name",
                placeholder="e.g. Aarif Khan",
                key="signup_fullname"
            )
            email_addr = st.text_input(
                "Email Address (used as your identifier)",
                placeholder="yourname@example.com",
                key="signup_email"
            )
            new_username = st.text_input(
                "Choose a Username",
                placeholder="e.g. aarif_khan  (lowercase, no spaces)",
                key="signup_username"
            )
            role_choice = st.selectbox(
                "Your Role",
                ["Engineer", "Technician", "Operator", "Supervisor", "Viewer"],
                key="signup_role"
            )
            new_password = st.text_input(
                "Create Password",
                type="password",
                placeholder="Minimum 8 characters",
                key="signup_pw1"
            )
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter password",
                key="signup_pw2"
            )

            st.markdown("""
            <p style='color:#8899AA; font-size:0.78rem; margin:0.3rem 0;'>
            Password must be at least 8 characters and contain letters and numbers.
            </p>
            """, unsafe_allow_html=True)

            create_btn = st.form_submit_button("✅ Create Account", use_container_width=True)

            if create_btn:
                # ── Validation ────────────────────────────────────────────────
                errors = []

                if not full_name.strip():
                    errors.append("Full name is required.")
                if not email_addr.strip() or "@" not in email_addr or "." not in email_addr:
                    errors.append("Enter a valid email address.")
                if not new_username.strip():
                    errors.append("Username is required.")
                elif " " in new_username.strip():
                    errors.append("Username cannot contain spaces.")
                elif len(new_username.strip()) < 3:
                    errors.append("Username must be at least 3 characters.")
                elif not new_username.strip().replace("_","").replace("-","").isalnum():
                    errors.append("Username can only contain letters, numbers, underscores and hyphens.")
                if not new_password:
                    errors.append("Password is required.")
                elif len(new_password) < 8:
                    errors.append("Password must be at least 8 characters.")
                elif new_password.isdigit() or new_password.isalpha():
                    errors.append("Password must contain both letters and numbers.")
                if new_password != confirm_password:
                    errors.append("Passwords do not match.")

                clean_username = new_username.strip().lower()

                if not errors and username_exists(clean_username):
                    errors.append(f"Username '{clean_username}' is already taken. Choose another.")
                if not errors and email_registered(email_addr.strip()):
                    errors.append("This email address is already registered. Try signing in or resetting your password.")

                if errors:
                    for err in errors:
                        st.error(f"❌ {err}")
                else:
                    # ── Save new user ─────────────────────────────────────────
                    reg_users = load_registered_users()
                    reg_users[clean_username] = {
                        "password_hash": hash_password(new_password),
                        "role":          role_choice,
                        "name":          full_name.strip(),
                        "email":         email_addr.strip().lower(),
                        "wind_farm":     farm_name,
                        "created_at":    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "builtin":       False
                    }
                    saved = save_registered_users(reg_users)

                    if saved:
                        # ── Welcome email ──────────────────────────────────────
                        welcome_html = f"""
                        <p>Dear <strong>{full_name.strip()}</strong>,</p>
                        <p>Your WindSense AI account has been successfully created.</p>
                        <div style="background:#0D1B2A; border-left:4px solid #00C9B1;
                                    padding:14px 18px; border-radius:0 8px 8px 0; margin:16px 0;">
                            <p style="margin:0;"><strong>Username:</strong> {clean_username}</p>
                            <p style="margin:6px 0 0 0;"><strong>Role:</strong> {role_choice}</p>
                            <p style="margin:6px 0 0 0;"><strong>Wind Farm:</strong> {farm_name}</p>
                            <p style="margin:6px 0 0 0;"><strong>Registered At:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        </div>
                        <p>Log in at: <a href="{DASHBOARD_URL}" style="color:#00C9B1;">{DASHBOARD_URL}</a></p>
                        <p style="color:#888; font-size:0.85rem;">
                            Keep your credentials secure. If you did not create this account,
                            contact windsenseada@gmail.com immediately.
                        </p>
                        """
                        send_email(
                            email_addr.strip(),
                            "✅ WindSense AI — Account Created Successfully",
                            email_template("Account Created", welcome_html)
                        )

                        # ── Admin notification email ───────────────────────────
                        admin_html = f"""
                        <p>A new user has registered on WindSense AI.</p>
                        <div style="background:#0D1B2A; border-left:4px solid #FFB347;
                                    padding:14px 18px; border-radius:0 8px 8px 0; margin:16px 0;">
                            <p style="margin:0;"><strong>Name:</strong> {full_name.strip()}</p>
                            <p style="margin:6px 0 0 0;"><strong>Username:</strong> {clean_username}</p>
                            <p style="margin:6px 0 0 0;"><strong>Email:</strong> {email_addr.strip()}</p>
                            <p style="margin:6px 0 0 0;"><strong>Role:</strong> {role_choice}</p>
                            <p style="margin:6px 0 0 0;"><strong>Wind Farm:</strong> {farm_name}</p>
                            <p style="margin:6px 0 0 0;"><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        </div>
                        """
                        send_email(
                            SENDER_EMAIL,
                            f"🆕 WindSense AI — New Registration: {clean_username}",
                            email_template("New User Registration", admin_html)
                        )

                        # ── Reset signup state & show success ─────────────────
                        st.session_state.signup_step          = 0
                        st.session_state.signup_farm_name     = ''
                        st.session_state.signup_farm_verified = False
                        st.success(f"""
                        ✅ Account created! Welcome to WindSense AI, {full_name.strip()}.
                        A confirmation email has been sent to {email_addr.strip()}.
                        You can now sign in using username: **{clean_username}**
                        """)
                        st.balloons()
                    else:
                        st.error("❌ Failed to save account. Check that the `data/` folder exists and is writable.")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to Farm Verification", key="back_to_step1", use_container_width=False):
            st.session_state.signup_step          = 0
            st.session_state.signup_farm_name     = ''
            st.session_state.signup_farm_verified = False
            st.rerun()

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center; color:#4FC3F7; font-size:0.78rem; padding-bottom:1rem;'>
    WindSense AI © 2026 | Team TG0907494 | TECHgium 9th Edition
</div>
""", unsafe_allow_html=True)