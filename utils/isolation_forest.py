# utils/isolation_forest.py
# WindSense AI — Isolation Forest Anomaly Detector
# Person B (Divya) — FINAL VERSION

import numpy as np
import json
import os
from datetime import datetime

class IsolationForestDetector:
    SENSOR_FEATURES = [
        'sensor_11_avg',
        'sensor_12_avg',
        'sensor_41_avg',
        'power_30_avg',
        'wind_speed_3_avg'
    ]

    def __init__(self, contamination=0.1, random_state=42):
        self.contamination = contamination
        self.random_state = random_state
        self.model = None
        self.is_trained = False
        self.training_sample_count = 0
        self.anomaly_log_path = os.path.join(
            os.path.dirname(os.path.abspath('app.py')), 'data', 'anomaly_log.json'
        )

    def _extract_features(self, alarm_dict):
        return [float(alarm_dict.get(f, 0) or 0) for f in self.SENSOR_FEATURES]

    def train(self, alarm_buffer):
        if len(alarm_buffer) < 10:
            return False, f"Need at least 10 alarms to train. Currently have {len(alarm_buffer)}."
        try:
            from sklearn.ensemble import IsolationForest
            X = np.array([self._extract_features(a) for a in alarm_buffer])
            self.model = IsolationForest(
                contamination=self.contamination,
                random_state=self.random_state,
                n_estimators=100
            )
            self.model.fit(X)
            self.is_trained = True
            self.training_sample_count = len(alarm_buffer)
            return True, f"Trained on {len(alarm_buffer)} alarms using {len(self.SENSOR_FEATURES)} sensor features."
        except Exception as e:
            return False, f"Training failed: {e}"

    def predict(self, alarm_dict):
        if not self.is_trained or self.model is None:
            return False, 0.0
        try:
            X = np.array([self._extract_features(alarm_dict)])
            prediction = self.model.predict(X)[0]
            score = self.model.decision_function(X)[0]
            is_anomaly = (prediction == -1)
            normalized_score = max(0.0, min(1.0, (0.5 - score)))
            return is_anomaly, round(float(normalized_score), 3)
        except Exception as e:
            return False, 0.0

    def log_anomaly(self, alarm_dict, anomaly_score):
        try:
            existing = []
            if os.path.exists(self.anomaly_log_path):
                try:
                    with open(self.anomaly_log_path, 'r') as f:
                        existing = json.load(f)
                except:
                    existing = []
            log_entry = {
                'logged_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'alarm_id': alarm_dict.get('alarm_id', 'UNKNOWN'),
                'asset_id': alarm_dict.get('asset_id', 'UNKNOWN'),
                'anomaly_score': anomaly_score,
                'sensor_values': {f: alarm_dict.get(f, 0) for f in self.SENSOR_FEATURES},
                'predicted_type': alarm_dict.get('predicted_type', 'UNKNOWN'),
                'status': 'pending_review'
            }
            existing.append(log_entry)
            if len(existing) > 100:
                existing = existing[-100:]
            with open(self.anomaly_log_path, 'w') as f:
                json.dump(existing, f, indent=2)
            return True
        except Exception as e:
            return False

    def load_anomaly_log(self):
        try:
            if os.path.exists(self.anomaly_log_path):
                with open(self.anomaly_log_path, 'r') as f:
                    return json.load(f)
            return []
        except:
            return []

    def mark_as_known(self, alarm_id):
        try:
            log = self.load_anomaly_log()
            for entry in log:
                if entry.get('alarm_id') == alarm_id:
                    entry['status'] = 'known'
            with open(self.anomaly_log_path, 'w') as f:
                json.dump(log, f, indent=2)
            return True
        except:
            return False

    def get_stats(self):
        log = self.load_anomaly_log()
        pending = sum(1 for e in log if e.get('status') == 'pending_review')
        known = sum(1 for e in log if e.get('status') == 'known')
        return {
            'is_trained': self.is_trained,
            'training_samples': self.training_sample_count,
            'total_anomalies_logged': len(log),
            'pending_review': pending,
            'marked_as_known': known
        }