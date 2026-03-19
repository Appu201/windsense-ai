# utils/sidebar.py — Clean navigation sidebar for WindSense AI
import streamlit as st
import time

def render_sidebar():
    """Render the WindSense AI sidebar. Returns action string."""

    with st.sidebar:

        # Logo + Title
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0 0.5rem 0;">
            <img src="https://img.icons8.com/fluency/96/wind-turbine.png" width="65">
            <h2 style="color: #00C9B1; margin: 0.4rem 0 0 0; font-size: 1.4rem;">WindSense AI</h2>
            <p style="color: #4FC3F7; font-size: 0.7rem; margin: 0;">
                Team TG0907494 | TECHgium 9th Edition
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Navigation
        st.markdown("<p style='color:#8899AA; font-size:0.75rem; margin:0;'>NAVIGATION</p>",
                   unsafe_allow_html=True)

        pages = [
            ("📡 Real-Time Monitoring", "pages/1_Realtime.py"),
            ("🤖 ML Model & Training", "pages/2_ML_Model.py"),
            ("📊 Historical Analytics", "pages/3_Historical.py"),
            ("🔔 Notifications", "pages/4_Notifications.py"),
            ("📋 DMAIC Analysis", "pages/5_DMAIC.py"),
            ("🎯 Optimization", "pages/6_Optimization.py"),
            ("🎛️ Acknowledgment", "pages/7_Acknowledgment.py"),
        ]

        for page_name, page_path in pages:
            if st.button(page_name, use_container_width=True, key=f"nav_{page_name}"):
                st.switch_page(page_path)

        st.divider()

        # Live stats
        st.markdown("<p style='color:#8899AA; font-size:0.75rem; margin:0;'>LIVE STATUS</p>",
                   unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            alarm_count = len(st.session_state.get('alarm_buffer', []))
            st.metric("Alarms", alarm_count)
        with col2:
            ack_count = len(st.session_state.get('acknowledged_alarms', {}))
            st.metric("Acked", ack_count)

        # Critical count
        critical_count = sum(
            1 for a in st.session_state.get('alarm_buffer', [])
            if a.get('priority') == 'CRITICAL'
            and a.get('alarm_id') not in st.session_state.get('acknowledged_alarms', {})
        )
        if critical_count > 0:
            st.markdown(f"""
            <div style="background:#FF4444; padding:0.5rem; border-radius:6px;
                        text-align:center; color:white; font-weight:bold; margin:0.3rem 0;">
                🚨 {critical_count} CRITICAL UNACKED
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # Quick actions
        st.markdown("<p style='color:#8899AA; font-size:0.75rem; margin:0;'>QUICK ACTIONS</p>",
                   unsafe_allow_html=True)

        action = None

        if st.button("🔄 Generate Alarm", use_container_width=True, type="primary"):
            action = "generate_alarm"

        auto_mode = st.checkbox("🤖 Auto-Generate (5s)")
        if auto_mode:
            action = "auto"

        if st.button("🗑️ Clear All Alarms", use_container_width=True):
            st.session_state.alarm_buffer = []
            st.session_state.notifications = []
            st.rerun()

        st.divider()

        # User info + logout
        username = st.session_state.get('username', 'Unknown')
        role = st.session_state.get('user_role', 'Viewer')

        st.markdown(f"""
        <div style="font-size:0.8rem; color:#4FC3F7; margin-bottom:0.5rem;">
            👤 {username}<br>
            <span style="color:#8899AA;">{role}</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.user_role = None
            st.switch_page("pages/login.py")

    return action