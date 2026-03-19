# TAB 7: ALARM ACKNOWLEDGMENT SYSTEM
# ═══════════════════════════════════════════════════════════════════

with tab7:
    st.markdown('<div class="main-header">🎛️ Alarm Acknowledgment & Management</div>', unsafe_allow_html=True)

    # Clean up orphaned acknowledgments
    clean_orphaned_acknowledgments()

    # Initialize acknowledgment tracking
    if 'acknowledged_alarms' not in st.session_state:
        st.session_state.acknowledged_alarms = {}

    # Key metrics - Only show stats for active alarms

    # Reload acknowledgments from file to ensure we have latest
    st.session_state.acknowledged_alarms = load_acknowledgments()

    # Get count of active alarms (those in the buffer)
    total_alarms = len(st.session_state.alarm_buffer)

    # Count acknowledged alarms that are IN the current alarm buffer
    active_alarm_ids = {a['alarm_id'] for a in st.session_state.alarm_buffer}
    acknowledged_count = len([aid for aid in st.session_state.acknowledged_alarms.keys()
                             if aid in active_alarm_ids])

    # Calculate pending based on active alarms only
    pending_count = max(0, total_alarms - acknowledged_count)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Alarms", total_alarms)

    with col2:
        st.metric("✅ Acknowledged", acknowledged_count,
                 delta=f"{(acknowledged_count/total_alarms*100) if total_alarms > 0 else 0:.1f}%")

    with col3:
        st.metric("⏳ Pending", pending_count,
                 delta=f"-{pending_count} to clear", delta_color="inverse")

    with col4:
        # Calculate average response time only for dashboard acks
        dashboard_acks = [a for a in st.session_state.acknowledged_alarms.values()
                         if 'response_time' in a]
        avg_response = np.mean([a['response_time'] for a in dashboard_acks]) if dashboard_acks else 0
        st.metric("Avg Response Time", f"{avg_response:.1f} min")

    st.divider()
     # Refresh acknowledgments
    if st.button("🔄 Refresh Acknowledgments", use_container_width=True):
        st.session_state.acknowledged_alarms = load_acknowledgments()
        st.success("✅ Acknowledgments reloaded from storage")
        st.rerun()

    st.divider()

    st.subheader("🚨 Active Alarms Requiring Acknowledgment")

    # Active alarms requiring acknowledgment
    st.subheader("🚨 Active Alarms Requiring Acknowledgment")

    if not st.session_state.alarm_buffer:
        st.info("✅ No active alarms. All systems operating normally!")
    else:
        # Filter unacknowledged alarms
        unack_alarms = [a for a in st.session_state.alarm_buffer
                       if a['alarm_id'] not in st.session_state.acknowledged_alarms]

        if not unack_alarms:
            st.success("✅ All alarms have been acknowledged!")
        else:
            st.warning(f"⚠️ {len(unack_alarms)} alarms awaiting acknowledgment")

            # Display each unacknowledged alarm
            for alarm in unack_alarms[:10]:  # Show top 10
                priority_color = {
                    'CRITICAL': '#ff4444',
                    'HIGH': '#ff8800',
                    'MEDIUM': '#ffbb33'
                }[alarm['priority']]

                with st.expander(
                    f"🚨 {alarm['alarm_id']} - {alarm['predicted_type']} | "
                    f"Turbine T-{alarm['asset_id']} | {alarm['timestamp']}",
                    expanded=True
                ):
                    col_a, col_b = st.columns([2, 1])

                    with col_a:
                        # Alarm details
                        st.markdown(f"""
                        <div style="background-color: {priority_color}; padding: 10px; border-radius: 5px; color: white;">
                            <strong>Priority:</strong> {alarm['priority']}<br>
                            <strong>Confidence:</strong> {alarm['confidence']:.1f}%<br>
                            <strong>Turbine:</strong> T-{alarm['asset_id']}<br>
                            <strong>Status Type:</strong> {alarm['status_type_id']}
                        </div>
                        """, unsafe_allow_html=True)

                        # Root Cause Analysis
                        st.write("**🔍 Root Cause Analysis:**")
                        sensor_data = {k: v for k, v in alarm.items()
                                     if 'sensor' in k or 'power' in k or 'wind' in k}
                        rca_result = st.session_state.rca_engine.analyze(
                            alarm['predicted_type'],
                            sensor_data
                        )

                        st.write(f"**Primary Cause:** {rca_result['primary_cause']}")
                        st.write(f"**Confidence:** {rca_result['confidence']}%")

                        if rca_result['contributing_factors']:
                            st.write("**Contributing Factors:**")
                            for factor in rca_result['contributing_factors']:
                                st.write(f"  • {factor}")

                        if rca_result['recommended_actions']:
                            st.write("**📋 Recommended Actions (Elimination Strategy):**")
                            for action in rca_result['recommended_actions']:
                                st.write(f"  ✓ {action}")

                    with col_b:
                        # Acknowledgment form
                        st.write("**Acknowledge Alarm:**")

                        technician_name = st.text_input(
                            "Technician Name",
                            key=f"tech_{alarm['alarm_id']}"
                        )

                        action_taken = st.selectbox(
                            "Action Taken",
                            ["Investigating", "Repairing", "Monitoring", "Resolved", "Escalated"],
                            key=f"action_{alarm['alarm_id']}"
                        )

                        notes = st.text_area(
                            "Notes",
                            key=f"notes_{alarm['alarm_id']}",
                            height=100
                        )

                        if st.button("✅ Acknowledge", key=f"ack_{alarm['alarm_id']}", type="primary"):
                            if technician_name:
                                # Record acknowledgment
                                ack_time = datetime.now()
                                alarm_time = datetime.strptime(alarm['timestamp'], '%Y-%m-%d %H:%M:%S')
                                response_time = (ack_time - alarm_time).total_seconds() / 60

                                ack_data = {
                                    'technician': technician_name,
                                    'ack_time': ack_time.strftime('%Y-%m-%d %H:%M:%S'),
                                    'action_taken': action_taken,
                                    'notes': notes,
                                    'response_time': response_time,
                                    'alarm_data': alarm,
                                    'method': 'dashboard'
                                }

                                # Save to persistent storage
                                save_acknowledgment(alarm['alarm_id'], ack_data)

                                # Update session state
                                st.session_state.acknowledged_alarms[alarm['alarm_id']] = ack_data

                                st.success(f"✅ Alarm {alarm['alarm_id']} acknowledged by {technician_name}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Please enter technician name")

    st.divider()

    # Acknowledgment history
    st.subheader("📜 Acknowledgment History")

    if st.session_state.acknowledged_alarms:
        # Create DataFrame
        ack_data = []
        for alarm_id, ack_info in st.session_state.acknowledged_alarms.items():
            # Handle both email and dashboard acknowledgments
            alarm_data = ack_info.get('alarm_data', {})

            # Determine acknowledgment method
            method = ack_info.get('method', 'unknown')

            if method == 'email_link':
                # Email acknowledgment - better display
                ack_data.append({
                    'Alarm ID': alarm_id,
                    'Type': 'Email Acknowledgment',
                    'Turbine': 'See Email',
                    'Priority': 'CRITICAL',
                    'Acknowledged By': 'Email Link',
                    'Ack Time': ack_info.get('time', 'N/A'),
                    'Action': 'Acknowledged via Email',
                    'Response Time (min)': 'N/A'
                })
            else:
                # Dashboard acknowledgment
                ack_data.append({
                    'Alarm ID': alarm_id,
                    'Type': alarm_data.get('predicted_type', 'N/A'),
                    'Turbine': f"T-{alarm_data.get('asset_id', 'N/A')}",
                    'Priority': alarm_data.get('priority', 'N/A'),
                    'Acknowledged By': ack_info.get('technician', 'Unknown'),
                    'Ack Time': ack_info.get('ack_time', 'N/A'),
                    'Action': ack_info.get('action_taken', 'N/A'),
                    'Response Time (min)': f"{ack_info.get('response_time', 0):.1f}"
                })

        ack_df = pd.DataFrame(ack_data)
        st.dataframe(ack_df, use_container_width=True, height=400)

        # Download log
        csv = ack_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Acknowledgment Log",
            csv,
            "alarm_acknowledgments.csv",
            "text/csv",
            use_container_width=True
        )

        # Statistics (only for dashboard acknowledgments)
        dashboard_acks = [a for a in st.session_state.acknowledged_alarms.values()
                         if a.get('method') != 'email_link' and 'response_time' in a]

        if dashboard_acks:
            st.subheader("📊 Acknowledgment Statistics (Dashboard Only)")

            col1, col2, col3 = st.columns(3)

            with col1:
                avg_response = np.mean([a['response_time'] for a in dashboard_acks])
                st.metric("Avg Response Time", f"{avg_response:.1f} min")

            with col2:
                actions = [a.get('action_taken', 'N/A') for a in dashboard_acks]
                by_action = pd.Series(actions).value_counts()
                most_common = by_action.index[0] if len(by_action) > 0 else "N/A"
                st.metric("Most Common Action", most_common)

            with col3:
                techs = [a.get('technician', 'N/A') for a in dashboard_acks]
                by_tech = pd.Series(techs).value_counts()
                most_active = by_tech.index[0] if len(by_tech) > 0 else "N/A"
                st.metric("Most Active Technician", most_active)

            # Response time chart
            response_times = [a['response_time'] for a in dashboard_acks]
            fig = px.histogram(
                x=response_times,
                nbins=20,
                title='Response Time Distribution',
                labels={'x': 'Response Time (min)', 'y': 'Count'}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

        # Show email acknowledgments separately
        email_acks = sum(1 for a in st.session_state.acknowledged_alarms.values()
                        if a.get('method') == 'email_link')
        if email_acks > 0:
            st.info(f"📧 {email_acks} alarm(s) acknowledged via email link")

    else:
        st.info("No alarms have been acknowledged yet")

# ═══════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════

st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <strong>WindSense AI © 2026</strong> | Team TG0907494 | TECHgium 9th Edition<br>
    Intelligent Predictive Control and Alarm Optimization in Wind Turbine Systems
</div>
""", unsafe_allow_html=True)