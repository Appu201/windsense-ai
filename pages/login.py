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
    initial_sidebar_state="expanded"
)

ack_id = st.query_params.get('ack', '')
if ack_id:
    st.session_state['pending_ack'] = ack_id

if st.session_state.get('authenticated', False):
    st.switch_page("pages/1_Realtime.py")

st.markdown("""
<style>
    .stApp { background-color: #0D1B2A; color: white; }
    .main .block-container { background-color: #0D1B2A; }
    [data-testid="stSidebar"] {
        background-color: #0D1B2A !important;
        border-right: 1px solid #00C9B1 !important;
    }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    [data-testid="stForm"] {
        background: linear-gradient(135deg, #1a2a3a 0%, #0D1B2A 100%);
        border: 1px solid #00C9B1;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 0 30px rgba(0,201,177,0.2);
    }
    h1, h2, h3 { color: #00C9B1 !important; }
    p, label { color: #FFFFFF !important; }
    .stTextInput input {
        background-color: #1a2a3a !important;
        border: 1px solid #00C9B1 !important;
        color: #E8F4FD !important;
        border-radius: 8px;
        caret-color: #00C9B1 !important;
    }
    [data-testid="InputInstructions"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style='text-align:center; margin-bottom:1rem;'>
    <img src='data:image/png;base64,{__import__('base64').b64encode(open('assets/windsense_logo_full.png','rb').read()).decode()}' width='320'/>
</div>
<p style='text-align:center; color:#4FC3F7; font-size:0.95rem;'>Team TG0907494 | TECHgium 9th Edition</p>
<p style='text-align:center; color:#6B8FA8; font-size:0.85rem;'>Intelligent Alarm Classification & Optimization</p>
""", unsafe_allow_html=True)

st.divider()

pending_ack = st.session_state.get('pending_ack', '')
if pending_ack:
    st.info(f"🔔 You're acknowledging alarm **{pending_ack}**. Please log in to continue.")

with st.form("login_form"):
    st.subheader("🔐 Sign In")

    username = st.text_input("Username", placeholder="Enter username")
    password = st.text_input("Password", type="password", placeholder="Enter password")

    submit = st.form_submit_button("🔓 Login", use_container_width=True, type="primary")

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
                st.success(f"✅ Welcome, {user_data['name']}!")
                import time
                time.sleep(1)
                st.switch_page("pages/1_Realtime.py")
            else:
                st.error("❌ Invalid username or password.")
        else:
            st.warning("⚠️ Please enter both username and password.")

st.divider()

with st.expander("🔑 Forgot Password?"):
    st.write("Enter your registered email address and we'll send you a reset link.")
    reset_email = st.text_input("Email Address", placeholder="Enter your email", key="reset_email_input")
    
    if st.button("📧 Send Reset Link", key="reset_btn"):
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        known_emails = {
            "windsenseada@gmail.com": "Wind Farm Admin",
            "divyajay.1612@gmail.com": "Divya",
            "muhammadhaarif2000@gmail.com": "Aarif",
            "ts.aparajithaa@gmail.com": "Aparajithaa",
            "team@tg0907494.com": "Team TG0907494",
            "demo@windsense.ai": "Demo User"
        }

        if reset_email and reset_email.strip().lower() in {k.lower() for k in known_emails}:
            matched_name = next((v for k, v in known_emails.items() if k.lower() == reset_email.strip().lower()), "User")
            try:
                sender = "windsenseada@gmail.com"
                app_password = "oaru xyta qlwi hpmw"

                msg = MIMEMultipart()
                msg['From'] = sender
                msg['To'] = reset_email.strip()
                msg['Subject'] = "WindSense AI — Password Reset Request"

                body = f"""
<html>
<body style="font-family: Arial, sans-serif; background-color: #0D1B2A; color: #E8F4FD; padding: 20px;">
    <div style="background: linear-gradient(135deg, #00796B 0%, #004D40 100%); padding: 20px; border-radius: 10px;">
        <h2 style="color: white;">🌀 WindSense AI — Password Reset</h2>
    </div>
    <div style="padding: 20px; background-color: #1a2a3a; border-radius: 10px; margin-top: 10px;">
        <p>Dear {matched_name},</p>
        <p>A password reset was requested for your WindSense AI account.</p>
        <div style="background-color: #0D1B2A; padding: 15px; border-left: 4px solid #00C9B1; margin: 20px 0; border-radius: 4px;">
            <p><strong>Your login credentials are:</strong></p>
            <p>🔗 Dashboard: <a href="https://windsense-ai.streamlit.app" style="color: #00C9B1;">https://windsense-ai.streamlit.app</a></p>
            <p>Please contact your team admin if you need your password reset.</p>
        </div>
        <p style="color: #4FC3F7; font-size: 0.85rem;">If you did not request this, please ignore this email.</p>
    </div>
    <div style="text-align: center; padding: 10px; color: #4FC3F7; font-size: 0.75rem;">
        WindSense AI © 2026 | TECHgium 9th Edition | Team TG0907494
    </div>
</body>
</html>
"""
                msg.attach(MIMEText(body, 'html'))

                smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
                smtp_server.ehlo()
                smtp_server.starttls()
                smtp_server.login(sender, app_password)
                smtp_server.sendmail(sender, reset_email.strip(), msg.as_string())
                smtp_server.quit()

                st.success(f"✅ Reset link sent to {reset_email.strip()}. Please check your inbox.")
            except Exception as e:
                st.error(f"❌ Failed to send email: {e}")
        elif reset_email:
            st.warning("⚠️ Email address not found in our system. Please contact your admin.")
        else:
            st.warning("⚠️ Please enter an email address.")

st.divider()

with st.expander("ℹ️ Demo Credentials (for judges)"):
    st.write("**Username:** demo | **Password:** demo123")
    st.write("**Username:** teamtg | **Password:** TECHgium2026")
    st.write("**Username:** admin | **Password:** windsense2026")

st.markdown("""
<div style='text-align:center; color:#4FC3F7; padding:1rem 0; font-size:0.8rem;'>
WindSense AI © 2026 | TECHgium 9th Edition
</div>
""", unsafe_allow_html=True)