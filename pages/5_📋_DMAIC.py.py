# TAB 5: DMAIC ANALYSIS
# ═══════════════════════════════════════════════════════════════════

with tab5:
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

    # Select alarm for DMAIC display
    alarm_classes = [
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

    selected_alarm = st.selectbox(
        "Select Alarm Type for Detailed DMAIC Analysis:",
        alarm_classes
    )

    # Load DMAIC data from dmaic_complete_database.json for all 19 alarms
    if DMAIC_DATABASE and selected_alarm in DMAIC_DATABASE:
        dmaic = DMAIC_DATABASE[selected_alarm]

        # Define
        st.subheader("📝 DEFINE")
        define_data = dmaic.get('define', {})
        st.write(f"**What:** {define_data.get('what', 'N/A')}")
        st.write(f"**When:** {define_data.get('when', 'N/A')}")
        st.write(f"**Impact:** {define_data.get('impact', 'N/A')}")

        st.divider()

        # Measure section - use st.write instead of st.metric to avoid truncation
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

        # Analyze
        st.subheader("🔍 ANALYZE")
        analyze_data = dmaic.get('analyze', {})
        st.write(f"**Root Cause:** {analyze_data.get('root_cause', 'N/A')}")
        contributing = analyze_data.get('contributing', [])
        if contributing:
            st.write("**Contributing Factors:**")
            for factor in contributing:
                st.write(f"- {factor}")

        st.divider()

        # Improve
        st.subheader("⚙️ IMPROVE")
        improve_data = dmaic.get('improve', {})
        solutions = improve_data.get('solutions', [])
        if solutions:
            st.write("**Recommended Solutions (Elimination Strategy):**")
            for i, solution in enumerate(solutions, 1):
                st.write(f"{i}. {solution}")
        expected_benefit = improve_data.get('expected_benefit', '')
        if expected_benefit:
            st.success(f"**Expected Benefit:** {expected_benefit}")

        st.divider()

        # Control
        st.subheader("🎛️ CONTROL")
        control_data = dmaic.get('control', {})
        monitoring = control_data.get('monitoring', 'N/A')
        st.write(f"**Monitoring Plan:** {monitoring}")
        alerts = control_data.get('alerts', [])
        if alerts:
            st.write("**Alert Thresholds:**")
            for alert in alerts:
                st.write(f"- {alert}")
        review = control_data.get('review', 'N/A')
        st.write(f"**Review Frequency:** {review}")

    else:
        # If DMAIC_DATABASE not loaded yet (file path issue), show helpful message
        st.warning(
            f"⚠️ DMAIC database not loaded from file. "
            f"Please ensure `dmaic_complete_database.json` exists at: `{DATA_PATH}dmaic_complete_database.json`"
        )
        st.info("Once the file is available, all 19 alarm types will display full DMAIC analysis automatically.")

# ═══════════════════════════════════════════════════════════════════