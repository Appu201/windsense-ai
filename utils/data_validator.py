# utils/data_validator.py — Input data validation for WindSense AI
import pandas as pd
import os
import streamlit as st

REQUIRED_COLUMNS = {
    'dashboard_alarm_stream.csv': [
        'alarm_id', 'timestamp', 'asset_id', 'status_type_id',
        'sensor_11_avg', 'sensor_12_avg', 'power_30_avg', 'wind_speed_3_avg'
    ],
    'top_50_unique_detailed_alarms.csv': [
        'Alarm_Type', 'Frequency', 'Total_Downtime', 'Department'
    ],
    'detailed_classified_alarm_episodes.csv': [
        'Episode_ID', 'Asset_ID', 'Status_Type', 'Alarm_Type',
        'Duration_Hours', 'Start_Time', 'End_Time', 'Primary_Department'
    ],
    'alarm_episodes_with_faults.csv': [
        'asset_id', 'status_type', 'start_time', 'end_time', 'duration_hours'
    ]
}

VALID_STATUS_TYPES = [3.0, 4.0, 5.0]

def validate_file_exists(filepath, filename):
    if not os.path.exists(filepath):
        return False, f"❌ File not found: {filename}"
    if os.path.getsize(filepath) == 0:
        return False, f"❌ File is empty: {filename}"
    return True, f"✅ {filename} found"

def validate_columns(df, filename):
    required = REQUIRED_COLUMNS.get(filename, [])
    missing = [col for col in required if col not in df.columns]
    if missing:
        return False, f"❌ {filename} missing columns: {', '.join(missing)}"
    return True, f"✅ {filename} columns OK"

def validate_alarm_stream(df):
    issues = []
    invalid_status = df[~df['status_type_id'].isin(VALID_STATUS_TYPES)]
    if len(invalid_status) > 0:
        issues.append(f"⚠️ {len(invalid_status)} rows have invalid status_type_id")
    key_cols = ['alarm_id', 'asset_id', 'status_type_id']
    for col in key_cols:
        if col in df.columns:
            null_count = df[col].isna().sum()
            if null_count > 0:
                issues.append(f"⚠️ {col} has {null_count} null values")
    if 'alarm_id' in df.columns:
        dup_count = df['alarm_id'].duplicated().sum()
        if dup_count > 0:
            issues.append(f"⚠️ {dup_count} duplicate alarm IDs")
    return issues

def validate_all_files(data_path):
    report = {'passed': [], 'failed': [], 'warnings': [], 'overall_status': 'PASS'}

    for filename in REQUIRED_COLUMNS:
        filepath = os.path.join(data_path, filename)

        exists, msg = validate_file_exists(filepath, filename)
        if not exists:
            report['failed'].append(msg)
            report['overall_status'] = 'FAIL'
            continue

        try:
            df = pd.read_csv(filepath)
        except Exception as e:
            report['failed'].append(f"❌ Cannot read {filename}: {e}")
            report['overall_status'] = 'FAIL'
            continue

        col_ok, col_msg = validate_columns(df, filename)
        if col_ok:
            report['passed'].append(col_msg)
        else:
            report['failed'].append(col_msg)
            report['overall_status'] = 'FAIL'

        if filename == 'dashboard_alarm_stream.csv':
            report['warnings'].extend(validate_alarm_stream(df))

    return report

def show_validation_report(data_path):
    with st.expander("🔍 Data Validation Report", expanded=False):
        with st.spinner("Validating data files..."):
            report = validate_all_files(data_path)

        if report['overall_status'] == 'PASS':
            st.success("✅ All critical validations PASSED")
        else:
            st.error("❌ Validation FAILED — check files below")

        if report['passed']:
            st.write("**✅ Passed:**")
            for msg in report['passed']:
                st.write(f"  {msg}")

        if report['failed']:
            st.write("**❌ Failed:**")
            for msg in report['failed']:
                st.write(f"  {msg}")

        if report['warnings']:
            st.write("**⚠️ Warnings:**")
            for msg in report['warnings']:
                st.write(f"  {msg}")

        return report['overall_status'] == 'PASS'