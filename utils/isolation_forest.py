# utils/isolation_forest.py
# WindSense AI — Isolation Forest Anomaly Detector
# Person B (Divya) — Phase 3 FINAL CLEAN VERSION

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

    ANOMALY_DESCRIPTIONS = {
        'sensor_11_avg': 'Gearbox Bearing Temp',
        'sensor_12_avg': 'Gearbox Oil Temp',
        'sensor_41_avg': 'Hydraulic Oil Temp',
        'power_30_avg': 'Grid Power Output',
        'wind_speed_3_avg': 'Wind Speed'
    }

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

    def _get_anomalous_sensors(self, alarm_dict):
        anomalous = []
        for f, desc in self.ANOMALY_DESCRIPTIONS.items():
            val = float(alarm_dict.get(f, 0) or 0)
            if f == 'sensor_11_avg' and val > 75:
                anomalous.append(f"{desc}: {val:.1f}°C (HIGH)")
            elif f == 'sensor_12_avg' and val > 70:
                anomalous.append(f"{desc}: {val:.1f}°C (HIGH)")
            elif f == 'sensor_41_avg' and val > 65:
                anomalous.append(f"{desc}: {val:.1f}°C (HIGH)")
            elif f == 'power_30_avg' and val < 50:
                anomalous.append(f"{desc}: {val:.1f} kW (CRITICALLY LOW)")
            elif f == 'wind_speed_3_avg' and val > 20:
                anomalous.append(f"{desc}: {val:.1f} m/s (EXTREME)")
        return anomalous if anomalous else ["Unusual multi-sensor pattern detected"]

    def train(self, alarm_buffer):
        if len(alarm_buffer) < 10:
            return False, f"Need at least 10 alarms to train. Have {len(alarm_buffer)}."
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
            return True, f"Trained on {len(alarm_buffer)} alarms."
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
        except Exception:
            return False, 0.0

    def log_anomaly(self, alarm_dict, anomaly_score, source='alarm_stream'):
        try:
            existing = []
            if os.path.exists(self.anomaly_log_path):
                try:
                    with open(self.anomaly_log_path, 'r') as f:
                        existing = json.load(f)
                except Exception:
                    existing = []

            turbine_id = alarm_dict.get('asset_id', alarm_dict.get('turbine_id', 'Unknown'))
            anomalous_sensors = self._get_anomalous_sensors(alarm_dict)

            log_entry = {
                'logged_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'alarm_id': alarm_dict.get('alarm_id', f'ANOM-{len(existing)+1:04d}'),
                'turbine': f"T-{turbine_id}",
                'anomaly_score': round(anomaly_score, 3),
                'severity': 'HIGH' if anomaly_score > 0.75 else 'MEDIUM',
                'anomalous_sensors': anomalous_sensors,
                'source': source,
                'status': 'pending_review'
            }
            existing.append(log_entry)
            if len(existing) > 50:
                existing = existing[-50:]
            with open(self.anomaly_log_path, 'w') as f:
                json.dump(existing, f, indent=2)
            return True
        except Exception:
            return False

    def load_anomaly_log(self):
        try:
            if os.path.exists(self.anomaly_log_path):
                with open(self.anomaly_log_path, 'r') as f:
                    return json.load(f)
            return []
        except Exception:
            return []

    def mark_as_reviewed(self, alarm_id):
        try:
            log = self.load_anomaly_log()
            for entry in log:
                if entry.get('alarm_id') == alarm_id:
                    entry['status'] = 'reviewed'
                    entry['reviewed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.anomaly_log_path, 'w') as f:
                json.dump(log, f, indent=2)
            return True
        except Exception:
            return False

    def clear_log(self):
        try:
            with open(self.anomaly_log_path, 'w') as f:
                json.dump([], f)
            return True
        except Exception:
            return False

    def get_stats(self):
        log = self.load_anomaly_log()
        pending = sum(1 for e in log if e.get('status') == 'pending_review')
        reviewed = sum(1 for e in log if e.get('status') == 'reviewed')
        high = sum(1 for e in log if e.get('severity') == 'HIGH')
        return {
            'is_trained': self.is_trained,
            'training_samples': self.training_sample_count,
            'total_logged': len(log),
            'pending_review': pending,
            'reviewed': reviewed,
            'high_severity': high
        }