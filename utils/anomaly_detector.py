# utils/anomaly_detector.py — Isolation Forest Anomaly Detection
import numpy as np
import pandas as pd
import json
import os

ANOMALY_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'anomaly_log.json')

SENSOR_FEATURES = [
    'sensor_11_avg',
    'sensor_12_avg',
    'sensor_41_avg',
    'power_30_avg',
    'wind_speed_3_avg',
    'sensor_13_avg',
    'sensor_14_avg'
]

class AnomalyDetector:
    def __init__(self, contamination=0.1):
        self.contamination = contamination
        self.model = None
        self.is_trained = False
        self.features_used = []
        self.training_samples = 0

    def train(self, alarm_buffer):
        if len(alarm_buffer) < 10:
            return False, f"Need at least 10 alarms to train. Have {len(alarm_buffer)}."
        try:
            from sklearn.ensemble import IsolationForest
            df = pd.DataFrame(alarm_buffer)
            available = [f for f in SENSOR_FEATURES if f in df.columns]
            if not available:
                return False, "No sensor features found in alarm buffer."
            X = df[available].fillna(0).values
            self.model = IsolationForest(contamination=self.contamination, random_state=42, n_estimators=100)
            self.model.fit(X)
            self.is_trained = True
            self.features_used = available
            self.training_samples = len(X)
            return True, f"Trained on {len(X)} alarms using {len(available)} features."
        except Exception as e:
            return False, f"Training failed: {str(e)}"

    def predict(self, alarm_row):
        if not self.is_trained or self.model is None:
            return {'is_anomaly': False, 'anomaly_score': 0.0, 'confidence': 0.0, 'reason': 'Model not trained'}
        try:
            X = [[alarm_row.get(f, 0) for f in self.features_used]]
            prediction = self.model.predict(X)[0]
            score = self.model.decision_function(X)[0]
            normalized = max(0, min(100, (score + 0.5) * 100))
            is_anomaly = (prediction == -1)
            return {
                'is_anomaly': is_anomaly,
                'anomaly_score': round(float(score), 4),
                'confidence': round(float(normalized), 1),
                'reason': 'Sensor pattern deviates significantly from known alarm profiles' if is_anomaly else 'Matches known alarm patterns'
            }
        except Exception as e:
            return {'is_anomaly': False, 'anomaly_score': 0.0, 'confidence': 0.0, 'reason': str(e)}

    def predict_batch(self, alarm_buffer):
        results = []
        for alarm in alarm_buffer:
            result = self.predict(alarm)
            result['alarm_id'] = alarm.get('alarm_id', 'N/A')
            results.append(result)
        return results

def load_anomaly_log():
    if os.path.exists(ANOMALY_LOG_FILE):
        try:
            with open(ANOMALY_LOG_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_anomaly_to_log(alarm_id, alarm_data, anomaly_result):
    log = load_anomaly_log()
    log.append({
        'alarm_id': alarm_id,
        'alarm_type': alarm_data.get('predicted_type', 'Unknown'),
        'turbine': alarm_data.get('asset_id', 'N/A'),
        'timestamp': alarm_data.get('timestamp', ''),
        'anomaly_score': anomaly_result.get('anomaly_score', 0),
        'reason': anomaly_result.get('reason', ''),
        'reviewed': False,
        'added_to_known': False
    })
    try:
        with open(ANOMALY_LOG_FILE, 'w') as f:
            json.dump(log, f, indent=2)
        return True
    except:
        return False

def mark_anomaly_reviewed(alarm_id, add_to_known=False):
    log = load_anomaly_log()
    for entry in log:
        if entry['alarm_id'] == alarm_id:
            entry['reviewed'] = True
            entry['added_to_known'] = add_to_known
            break
    try:
        with open(ANOMALY_LOG_FILE, 'w') as f:
            json.dump(log, f, indent=2)
        return True
    except:
        return False