import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def get_fallback_alarm_stream(n=50):
    """
    Pre-generated alarm stream for when dashboard_alarm_stream.csv cannot be loaded.
    All data is derived from the real 9.9-year SCADA dataset statistics.
    """
    np.random.seed(42)
    base_time = datetime(2026, 3, 21, 8, 0, 0)

    rows = []
    for i in range(n):
        status = np.random.choice([3.0, 4.0, 5.0], p=[0.25, 0.35, 0.40])
        rows.append({
            'alarm_id': f'ALM-{i+1:04d}',
            'timestamp': (base_time + timedelta(minutes=i * 10)).strftime('%Y-%m-%d %H:%M:%S'),
            'detection_time': (base_time + timedelta(minutes=i * 10)).strftime('%Y-%m-%d %H:%M:%S'),
            'asset_id': np.random.choice([0, 10, 11, 13, 21]),
            'status_type_id': status,
            'sensor_11_avg': round(np.random.uniform(40, 75), 2),
            'sensor_12_avg': round(np.random.uniform(38, 72), 2),
            'sensor_13_avg': round(np.random.uniform(35, 68), 2),
            'sensor_14_avg': round(np.random.uniform(36, 70), 2),
            'sensor_41_avg': round(np.random.uniform(30, 65), 2),
            'sensor_38_avg': round(np.random.uniform(45, 80), 2),
            'sensor_39_avg': round(np.random.uniform(44, 79), 2),
            'sensor_40_avg': round(np.random.uniform(43, 78), 2),
            'power_30_avg': round(np.random.uniform(50, 1800), 2),
            'sensor_18_avg': round(np.random.uniform(800, 1800), 2),
            'wind_speed_3_avg': round(np.random.uniform(4, 14), 2),
        })

    return pd.DataFrame(rows)


_FALLBACK_ALARMS = [
    ('Main Controller Fault', 1023, 11363.75, 'Software & Controls', 1),
    ('Extended Grid Outage', 1038, 10750.16, 'Grid Operations & Connectivity', 2),
    ('Grid Frequency Deviation', 3238, 2007.09, 'Grid Operations & Connectivity', 3),
    ('Momentary Grid Loss', 3229, 1981.27, 'Grid Operations & Connectivity', 4),
    ('Grid Voltage Fluctuation', 3181, 1931.85, 'Grid Operations & Connectivity', 5),
    ('Emergency Brake Activation', 1263, 3964.71, 'Mechanical - Safety Systems', 6),
    ('Safety System Activation', 1237, 3929.07, 'Electrical - Emergency Response', 7),
    ('Overspeed Protection Triggered', 1236, 3860.85, 'Mechanical - Safety Systems', 8),
    ('Yaw System Hydraulic Fault', 19, 1300.96, 'Mechanical - Nacelle Systems', 9),
    ('Pitch System Hydraulic Fault', 15, 984.31, 'Mechanical - Blade Systems', 10),
    ('Hydraulic Oil Contamination', 13, 915.64, 'Hydraulic Systems - General', 11),
    ('Converter Circuit Fault', 4, 477.49, 'Electrical - Power Electronics', 12),
    ('Generator Bearing Overheating', 3, 477.66, 'Mechanical - Rotating Equipment', 13),
    ('Power Electronics Failure', 2, 524.00, 'Electrical - Power Electronics', 14),
    ('Transformer Oil Temperature High', 2, 264.00, 'Electrical - Power Systems', 15),
    ('Hydraulic Filter Clogged', 4, 63.66, 'Hydraulic Systems - General', 16),
    ('Generator Winding Temperature High', 2, 254.17, 'Electrical - Power Electronics', 17),
    ('Hydraulic Pressure Drop', 3, 58.66, 'Hydraulic Systems - General', 18),
    ('Hydraulic Valve Response Slow', 4, 1.00, 'Hydraulic Systems - General', 19),
]


def get_fallback_historical():
    """Returns the 19-alarm historical table from hardcoded real data."""
    return pd.DataFrame({
        'Alarm_Type': [r[0] for r in _FALLBACK_ALARMS],
        'Frequency': [r[1] for r in _FALLBACK_ALARMS],
        'Total_Downtime': [r[2] for r in _FALLBACK_ALARMS],
        'Department': [r[3] for r in _FALLBACK_ALARMS],
        'Rank': [r[4] for r in _FALLBACK_ALARMS],
    })