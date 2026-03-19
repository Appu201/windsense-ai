# TAB 4: NOTIFICATIONS & WORKFLOW
# ═══════════════════════════════════════════════════════════════════

with tab4:
    st.markdown('<div class="main-header">🔔 Real-Time Notifications & Workflow</div>', unsafe_allow_html=True)

    # Auto-check for escalations
    check_and_escalate()

    # Workflow Diagram
    st.subheader("🔄 Alarm Resolution Workflow")

    workflow_steps = [
        {"step": 1, "name": "DETECT", "desc": "SCADA system detects abnormal condition"},
        {"step": 2, "name": "CLASSIFY", "desc": "AI model classifies alarm type (92% accuracy)"},
        {"step": 3, "name": "ANALYZE", "desc": "DMAIC root cause analysis applied"},
        {"step": 4, "name": "NOTIFY", "desc": "Stakeholders notified via SMS/Email"},
        {"step": 5, "name": "RESOLVE", "desc": "Team implements solution"},
        {"step": 6, "name": "MONITOR", "desc": "Track resolution and prevent recurrence"}
    ]

    cols = st.columns(6)
    for i, step in enumerate(workflow_steps):
        with cols[i]:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 1rem;
                        border-radius: 10px;
                        color: white;
                        text-align: center;
                        min-height: 150px;">
                <div style="font-size: 2rem; font-weight: bold;">{step['step']}</div>
                <div style="font-size: 1.2rem; font-weight: bold; margin: 0.5rem 0;">{step['name']}</div>
                <div style="font-size: 0.85rem;">{step['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Notification Statistics
    st.subheader("📊 Notification Statistics")

    col1, col2, col3, col4 = st.columns(4)

    notification_log = st.session_state.get('notification_log', [])
    active_alarms = st.session_state.get('active_critical_alarms', {})
    escalated = st.session_state.get('escalated_alarms', {})

    with col1:
        email_count = sum(1 for n in notification_log if n['type'] == 'EMAIL')
        st.metric("📧 Emails Sent", email_count)

    with col2:
        sms_count = sum(1 for n in notification_log if n['type'] == 'SMS')
        st.metric("📱 SMS Sent", sms_count)

    with col3:
        st.metric("🚨 Active Critical", len(active_alarms))

    with col4:
        st.metric("⚠️ Escalated", len(escalated), delta_color="inverse")

    st.divider()

    # Email/SMS Notification Log
    st.subheader("📨 Email & SMS Notification Log")

    if notification_log:
        # Create DataFrame for better display
        log_data = []
        for notif in notification_log[-50:]:  # Last 50
            log_data.append({
                'Time': notif['time'].strftime('%Y-%m-%d %H:%M:%S'),
                'Type': notif['type'],
                'Recipient': notif['recipient'],
                'Alarm ID': notif['alarm_id'],
                'Alarm Type': notif['alarm_type'],
                'Status': notif['status']
            })

        if log_data:
            log_df = pd.DataFrame(log_data)
            st.dataframe(log_df, use_container_width=True, height=300)

            # Download button
            csv = log_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download Notification Log",
                csv,
                "notification_log.csv",
                "text/csv",
                use_container_width=True
            )
    else:
        st.info("No email/SMS notifications sent yet. Critical alarms trigger automatic notifications.")

    st.divider()

    # Escalation Status
    if escalated:
        st.subheader("⚠️ Escalated Alarms")

        for alarm_id, esc_info in escalated.items():
            alarm_data = active_alarms.get(alarm_id, {})

            st.markdown(f"""
            <div style="background-color: #ff8800; padding: 15px; border-radius: 8px; color: white; margin: 10px 0;">
                <strong>🚨 ESCALATED: {alarm_id}</strong><br>
                Type: {alarm_data.get('type', 'N/A')}<br>
                Turbine: T-{alarm_data.get('turbine_id', 'N/A')}<br>
                Escalated To: {esc_info['escalated_to']}<br>
                Reason: {esc_info['reason']}<br>
                Escalation Time: {esc_info['escalation_time'].strftime('%Y-%m-%d %H:%M:%S')}
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Alarm Notifications (Legacy display)
    st.subheader("📬 Recent Alarm Notifications")

    if st.session_state.notifications:
        for notif in st.session_state.notifications[:20]:
            priority_emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡'}[notif['priority']]

            with st.expander(f"{priority_emoji} {notif['alarm_id']} - {notif['alarm_type']} | {notif['timestamp']}"):
                st.write(f"**Turbine:** {notif['turbine']}")
                st.write(f"**Department:** {notif['department']}")
                st.write(f"**Assigned To:** {notif.get('stakeholder', 'N/A')}")
                st.write(f"**Priority:** {notif['priority']}")
                st.write(f"**Message:** {notif['message']}")

                # Show who was notified
                alarm_id = notif['alarm_id']
                if alarm_id in active_alarms:
                    notified_list = active_alarms[alarm_id].get('notified', [])
                    if notified_list:
                        st.write(f"**Notified:** {', '.join(notified_list)}")

                st.write(f"**Status:** ✅ Sent to {notif['department']}")
    else:
        st.info("No notifications yet. Generate alarms to see notifications in action!")

    st.divider()

    # Stakeholder Directory
    st.subheader("👥 Stakeholder Directory")

    st.info("📋 Primary stakeholders are automatically notified via Email + SMS for their assigned alarm types. Secondary stakeholders receive email copies. Management receives escalations if alarms are not acknowledged within the threshold time.")

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
                st.caption("Receives: Email + SMS (Immediate)")

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
                st.caption(f"Receives: Email + SMS (After {stakeholder_info.get('escalation_time', 30)} min)")

    # Default contacts
    st.divider()
    st.subheader("🔧 Default Contacts (For unassigned alarms)")

    default_info = STAKEHOLDERS.get('DEFAULT', {})
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🎯 Primary**")
        primary = default_info.get('primary', {})
        st.write(f"{primary.get('name', 'N/A')} - {primary.get('role', 'N/A')}")
        st.write(f"📧 {primary.get('email', 'N/A')}")
        st.write(f"📞 {primary.get('phone', 'N/A')}")

    with col2:
        st.markdown("**📧 Secondary**")
        secondary = default_info.get('secondary', {})
        st.write(f"{secondary.get('name', 'N/A')} - {secondary.get('role', 'N/A')}")
        st.write(f"📧 {secondary.get('email', 'N/A')}")
        st.write(f"📞 {secondary.get('phone', 'N/A')}")

    with col3:
        st.markdown("**⚠️ Management**")
        management = default_info.get('management', {})
        st.write(f"{management.get('name', 'N/A')} - {management.get('role', 'N/A')}")
        st.write(f"📧 {management.get('email', 'N/A')}")
        st.write(f"📞 {management.get('phone', 'N/A')}")

# ═══════════════════════════════════════════════════════════════════