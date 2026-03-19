# TAB 6: OPTIMIZATION & FORECASTING
# ═══════════════════════════════════════════════════════════════════

with tab6:
    st.markdown('<div class="main-header">🎯 Optimization & Predictive Forecasting</div>', unsafe_allow_html=True)

    # LPF Optimization
    st.subheader("📈 Lost Production Factor (LPF) Optimization")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Current LPF", "3.64%", delta="-1.36% from baseline")

    with col2:
        st.metric("Target LPF", "<2.0%", delta="Industry best practice")

    with col3:
        st.metric("Potential Savings", "₹24.9-41.5 Crore/year", delta="After full implementation")

    st.divider()

    # LPF Breakdown
    st.subheader("🔍 LPF Breakdown by Category")

    lpf_data = pd.DataFrame({
        'Category': ['Grid-Related', 'Mechanical', 'Electrical', 'Hydraulic', 'Software'],
        'LPF_Percentage': [2.85, 0.35, 0.25, 0.12, 0.07],
        'Downtime_Hours': [28500, 3500, 2500, 1200, 700]
    })

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('LPF Distribution', 'Downtime Distribution'),
        specs=[[{'type': 'pie'}, {'type': 'bar'}]]
    )

    fig.add_trace(
        go.Pie(labels=lpf_data['Category'], values=lpf_data['LPF_Percentage'], hole=0.4),
        row=1, col=1
    )

    fig.add_trace(
        go.Bar(x=lpf_data['Category'], y=lpf_data['Downtime_Hours'], marker_color='lightblue'),
        row=1, col=2
    )

    fig.update_layout(height=400, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Predictive Forecasting
    st.subheader("🔮 6-Month Alarm Forecast")

    # Generate sample forecast data
    months = ['Month 1', 'Month 2', 'Month 3', 'Month 4', 'Month 5', 'Month 6']
    forecast_data = {
        'Month': months,
        'Grid Alarms': [850, 820, 800, 780, 750, 720],
        'Mechanical Alarms': [120, 115, 110, 105, 100, 95],
        'Electrical Alarms': [80, 78, 75, 72, 70, 68]
    }

    forecast_df = pd.DataFrame(forecast_data)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=forecast_df['Month'],
        y=forecast_df['Grid Alarms'],
        mode='lines+markers',
        name='Grid Alarms',
        line=dict(color='red', width=3)
    ))

    fig.add_trace(go.Scatter(
        x=forecast_df['Month'],
        y=forecast_df['Mechanical Alarms'],
        mode='lines+markers',
        name='Mechanical Alarms',
        line=dict(color='blue', width=3)
    ))

    fig.add_trace(go.Scatter(
        x=forecast_df['Month'],
        y=forecast_df['Electrical Alarms'],
        mode='lines+markers',
        name='Electrical Alarms',
        line=dict(color='green', width=3)
    ))

    fig.update_layout(
        title="Predicted Alarm Trends (Next 6 Months)",
        xaxis_title="Time Period",
        yaxis_title="Number of Alarms",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Implementation Roadmap - MATCHING SLIDE 10
    st.subheader("🗺️ 5-Phase Implementation Roadmap")

    phases = [
        {
            'phase': 'Phase 1: Foundation Setup',
            'investment': '₹12,000',
            'timeline': '2 weeks',
            'actions': [
                'Establish data warehouse using PostgreSQL or MongoDB',
                'Setup SCADA and CSV database integration',
                'Collect and organize historical data (6-12 months)',
                'Create data infrastructure for real-time processing',
                'Configure cloud storage (Google Cloud - 4 months)'
            ],
            'expected_lpf': 'Baseline established',
            'key_milestones': [
                'Week 1: Data warehouse deployment complete',
                'Week 2: Historical data collection and validation done'
            ]
        },
        {
            'phase': 'Phase 2: AI Model Development & Training',
            'investment': '₹15,000',
            'timeline': '4 weeks',
            'actions': [
                'Train Machine Learning Models (Random Forest, SVM, LSTM)',
                'Develop AI classifier for alarm categorization',
                'Build Root Cause Engine with 85% accuracy',
                'Create Predictive Model for 24-72hr forecasting',
                'Optimize model parameters using GPU training (Google Colab Pro+)'
            ],
            'expected_lpf': 'Model accuracy: ~88% (F1)',
            'key_milestones': [
                'Week 3: Random Forest classifier trained',
                'Week 4: LSTM predictive model developed',
                'Week 5: Root Cause Engine integrated',
                'Week 6: Model validation and testing complete'
            ]
        },
        {
            'phase': 'Phase 3: Backend & Frontend Development',
            'investment': '₹9,500',
            'timeline': '3 weeks',
            'actions': [
                'API & Dashboard interfacing using Streamlit/Flask',
                'Build Real-Time Dashboard with live monitoring',
                'Setup REST API Gateway (FastAPI/Django)',
                'Implement notification system (SMS/Email alerts via Twilio, Gmail, SendGrid)',
                'Create smart team routing and assignment logic'
            ],
            'expected_lpf': 'Dashboard operational',
            'key_milestones': [
                'Week 7: REST API deployment',
                'Week 8: Dashboard UI completed',
                'Week 9: Notification system tested and live'
            ]
        },
        {
            'phase': 'Phase 4: Integration & Pilot Deployment',
            'investment': '₹10,000',
            'timeline': '2 weeks',
            'actions': [
                'Live turbine pilot integration & test reports',
                'SCADA connection via OPC UA client library',
                'User acceptance testing (UAT)',
                'Configure notifications and escalation workflows',
                'Field testing with mechanical, electrical, and software teams'
            ],
            'expected_lpf': 'Initial reduction: 10-15%',
            'key_milestones': [
                'Week 10: SCADA integration successful',
                'Week 11: Pilot testing complete with positive results'
            ]
        },
        {
            'phase': 'Phase 5: Validation & Full-Scale Rollout',
            'investment': '₹5,000',
            'timeline': '3 weeks',
            'actions': [
                'Measure Key Performance Indicators (KPI) report',
                'Project rollout strategy and scaling plan',
                'Operator training and documentation',
                'DMAIC loop implementation for continuous improvement',
                'Performance validation and optimization'
            ],
            'expected_lpf': 'Target: <2.5% LPF, ~35% reduction',
            'key_milestones': [
                'Week 12: KPI measurement and reporting',
                'Week 13: Full team training completed',
                'Week 14: System handover and go-live'
            ]
        }
    ]

    for phase in phases:
        with st.expander(f"**{phase['phase']}** - Investment: {phase['investment']} | Timeline: {phase['timeline']}", expanded=True):
            st.write("**Key Deliverables:**")
            for action in phase['actions']:
                st.write(f"✓ {action}")

            st.success(f"**Expected Outcome:** {phase['expected_lpf']}")

            if phase['key_milestones']:
                st.write("**Key Milestones:**")
                for milestone in phase['key_milestones']:
                    st.write(f"  📌 {milestone}")

    st.info("⏱️ **Total Prototype Timeline:** 14 weeks (3.5 months)  \n**Note:** This timeline is for student prototype. Full-scale deployment takes 6-12 months.")

    st.divider()

    # ROI Calculation
    st.subheader("💰 Return on Investment (ROI)")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Pilot Cost", "₹51,500", delta="Student prototype")

    with col2:
        st.metric("Annual Savings", "₹50+ Lakh", delta="Per farm/year")

    with col3:
        st.metric("ROI Year 1", "900%+", delta="Industry-leading")

    with col4:
        st.metric("Payback Period", "~3 weeks", delta="Fast return")

    st.caption("*Costs shown are for student prototype. Full-scale deployment costs and ROI will differ based on farm size and requirements.")

# ═══════════════════════════════════════════════════════════════════