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

ack_id = st.query_params.get('ack', '')
if ack_id:
    st.session_state['pending_ack'] = ack_id

if st.session_state.get('authenticated', False):
    st.switch_page("pages/1_Realtime.py")

st.markdown("""
<style>
    [data-testid="stSidebarNav"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    button[data-testid="baseButton-header"] { display: none !important; }
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
        outline: none !important;
        box-shadow: none !important;
    }

    .stTextInput > div > div > input:focus {
        border: 1px solid #4FC3F7 !important;
        box-shadow: 0 0 0 2px rgba(0,201,177,0.15) !important;
    }

    div[data-baseweb] { border: none !important; box-shadow: none !important; }
    div[data-baseweb] > div { border: none !important; box-shadow: none !important; }

    [data-testid="InputInstructions"] { display: none !important; }

    .stButton > button {
        background: linear-gradient(135deg, #004D40, #00796B);
        color: white !important;
        border: 1px solid #00C9B1 !important;
        border-radius: 8px;
        font-weight: 600;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #00796B, #00C9B1) !important;
    }
</style>
""", unsafe_allow_html=True)

try:
    logo_bytes = open('assets/windsense_logo_full.png', 'rb').read()
    import base64
    logo_b64 = base64.b64encode(logo_bytes).decode()
    st.markdown(f"""
    <div style='text-align:center; margin-bottom:1rem;'>
        <img src='data:image/png;base64,{logo_b64}' width='300'/>
    </div>
    """, unsafe_allow_html=True)
except Exception:
    st.markdown("<h1 style='text-align:center; color:#00C9B1;'>🌀 WindSense AI</h1>", unsafe_allow_html=True)

st.markdown("<p style='text-align:center; color:#4FC3F7;'>Team TG0907494 | TECHgium 9th Edition</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#6B8FA8;'>Intelligent Alarm Classification & Optimization</p>", unsafe_allow_html=True)

st.divider()

pending_ack = st.session_state.get('pending_ack', '')
if pending_ack:
    st.info(f"🔔 You're acknowledging alarm **{pending_ack}**. Please log in to continue.")

with st.form("login_form"):
    st.subheader("🔐 Sign In")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submit = st.form_submit_button("🔓 Login", use_container_width=True)

    if submit:
        if username and password:
            success, user_data = verify_login(username, password)
            if success:
                st.session_state.authenticated = True
                st.session_state.username = user_data['name']
                st.session_state.user_role = user_data['role']
                st.session_state.user_email = user_data.get('email', '')
                st.session_state.login_time = datetime.now().isoformat()
                st.success(f"✅ Welcome, {user_data['name']}!")
                import time
                time.sleep(1)
                st.switch_page("pages/1_Realtime.py")
            else:
                st.error("❌ Invalid username or password.")
        else:
            st.warning("⚠️ Please enter both username and password.")

st.divider()

with st.expander("ℹ️ Demo Credentials"):
    st.write("admin / windsense2026")
    st.write("teamtg / TECHgium2026")
    st.write("demo / demo123")

st.markdown("""
<div style='text-align:center; color:#4FC3F7; padding:1rem 0; font-size:0.8rem;'>
WindSense AI © 2026 | TECHgium 9th Edition
</div>
""", unsafe_allow_html=True)