])

# ═══════════════════════════════════════════════════════════════════
# TAB 1: REAL-TIME MONITORING
# ═══════════════════════════════════════════════════════════════════

with tab1:
    st.markdown('<div class="main-header">📡 Real-Time Alarm Monitoring</div>', unsafe_allow_html=True)

    # Key Metrics
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

    # Live Alarm Stream
    st.subheader("🔴 LIVE ALARM STREAM")

    if st.session_state.alarm_buffer:
        # Display latest 10 alarms
        latest_alarms = st.session_state.alarm_buffer[:10]

        for alarm in latest_alarms:
            priority_color = {
                'CRITICAL': 'alert-critical',
                'HIGH': 'alert-high',
                'MEDIUM': 'alert-medium'
            }[alarm['priority']]

            st.markdown(f"""
            <div class="{priority_color}">
                <strong>{alarm['alarm_id']}</strong> | {alarm['timestamp']} | Turbine {alarm['asset_id']}<br>
                <strong>Type:</strong> {alarm['predicted_type']} | <strong>Confidence:</strong> {alarm['confidence']:.1f}%
            </div>
            """, unsafe_allow_html=True)

        # Detailed table
        st.subheader("📋 Detailed Alarm Data")
        alarm_df = pd.DataFrame(st.session_state.alarm_buffer)
        st.dataframe(
            alarm_df[['alarm_id', 'timestamp', 'asset_id', 'predicted_type', 'confidence', 'priority']],
            use_container_width=True,
            height=400
        )

        # Download button
        csv = alarm_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Alarm Log (CSV)",
            csv,
            "windsense_alarm_log.csv",
            "text/csv",
            use_container_width=True
        )
    else:
        st.info("👈 Click 'Generate New Alarm' in the sidebar to start real-time monitoring")

    # Visualizations
    if st.session_state.alarm_buffer:
        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Alarms by Type")
            type_counts = pd.DataFrame(st.session_state.alarm_buffer)['predicted_type'].value_counts()
            fig = px.bar(
                x=type_counts.index,
                y=type_counts.values,
                labels={'x': 'Alarm Type', 'y': 'Count'},
                color=type_counts.values,
                color_continuous_scale='Reds'
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("🌀 Alarms by Turbine")
            turbine_counts = pd.DataFrame(st.session_state.alarm_buffer)['asset_id'].value_counts()
            fig = px.pie(
                values=turbine_counts.values,
                names=[f"T-{tid}" for tid in turbine_counts.index],
                hole=0.4
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        # Root Cause Analysis Display
        st.divider()
        st.subheader("🔍 Root Cause Analysis - Latest Alarm")
        if st.session_state.alarm_buffer:
            latest_alarm = st.session_state.alarm_buffer[0]
            sensor_data = {k: v for k, v in latest_alarm.items()
                          if 'sensor' in k or 'power' in k or 'wind' in k}

            rca_result = st.session_state.rca_engine.analyze(
                latest_alarm['predicted_type'],
                sensor_data
            )

            st.write(f"**🔍 Root Cause:** {rca_result['primary_cause']}")
            st.write(f"**Confidence:** {rca_result['confidence']}%")

            # Always show recommended actions (elimination strategy) - never blank
            st.write("**Recommended Actions (Elimination Strategy):**")
            for action in rca_result['recommended_actions']:
                st.write(f"  ✓ {action}")

# ═══════════════════════════════════════════════════════════════════