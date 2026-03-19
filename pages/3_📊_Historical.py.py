# TAB 3: HISTORICAL ANALYTICS
# ═══════════════════════════════════════════════════════════════════

with tab3:
    st.markdown('<div class="main-header">📊 Historical Analysis (9.9 Years)</div>', unsafe_allow_html=True)

    if historical_alarms is not None:
        try:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Episodes", "15,517")

            with col2:
                st.metric("Total Downtime", "45,110 hrs")

            with col3:
                st.metric("Alarm Types", "19")

            with col4:
                st.metric("Departments", "11")

            st.divider()

            # Top Alarms Table
            st.subheader("🏆 Top Critical Alarms (Ranked by Impact)")

            # Check which columns exist and adapt
            available_cols = historical_alarms.columns.tolist()

            # Try different possible column name variations
            col_mapping = {
                'Rank': ['Rank', 'rank', 'index'],
                'Alarm_Type': ['Alarm_Type', 'alarm_type', 'Alarm Type', 'type'],
                'Frequency': ['Frequency', 'frequency', 'count'],
                'Total_Downtime': ['Total_Downtime', 'total_downtime', 'Downtime', 'downtime'],
                'Department': ['Department', 'department', 'dept']
            }

            # Find the actual column names
            display_cols = []
            col_names = []
            for target_col, variations in col_mapping.items():
                for var in variations:
                    if var in available_cols:
                        display_cols.append(var)
                        col_names.append(target_col.replace('_', ' '))
                        break

            if display_cols:
                display_df = historical_alarms[display_cols].copy()
                display_df.columns = col_names
                st.dataframe(display_df, use_container_width=True, height=600)
            else:
                # If columns don't match, just display the whole dataframe
                st.dataframe(historical_alarms, use_container_width=True, height=600)

            st.divider()

        except Exception as e:
            st.error(f"Error displaying historical data: {e}")
            st.info("Available columns: " + ", ".join(historical_alarms.columns.tolist()))
    else:
        st.info("Historical data not available. Please check data file paths.")

# ═══════════════════════════════════════════════════════════════════