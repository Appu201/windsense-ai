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

    def add_to_alarm_database(self, alarm_id, new_alarm_type, department='Anomaly Detection', team='AI Monitoring System'):
        """
        When a new anomaly type is marked as known, add it to the alarm database CSV.
        Returns (success: bool, message: str)
        """
        import pandas as pd
        try:
            db_path = os.path.join(
                os.path.dirname(os.path.abspath('app.py')), 'data', 'top_50_unique_detailed_alarms.csv'
            )
            if not os.path.exists(db_path):
                return False, "Alarm database CSV not found."

            df = pd.read_csv(db_path)

            # Check if already exists
            existing_types = df['Alarm_Type'].tolist() if 'Alarm_Type' in df.columns else []
            if new_alarm_type in existing_types:
                return False, f"'{new_alarm_type}' already exists in alarm database."

            # Build new row — all columns default to None then fill what we know
            new_rank = int(df['Rank'].max()) + 1 if 'Rank' in df.columns else 99
            new_row = {col: None for col in df.columns}
            new_row['Rank'] = new_rank
            new_row['Alarm_Type'] = new_alarm_type
            new_row['Frequency'] = 1
            new_row['Avg_Duration'] = 0.0
            new_row['Total_Downtime'] = 0.0
            new_row['Turbines_Affected'] = 1
            new_row['Department'] = department
            new_row['Team'] = team
            new_row['Criticality_Score'] = 0.0
            new_row['Notification_Priority'] = '🟡 Medium - Within 8 hours'
            new_row['Response_Time'] = '8 hours'
            new_row['Root_Cause_Category'] = 'Unknown — requires investigation'

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(db_path, index=False)

            # Also mark this anomaly as known in the log
            self.mark_as_known(alarm_id)

            return True, f"'{new_alarm_type}' added to alarm database at Rank {new_rank}."
        except Exception as e:
            return False, f"DB update failed: {e}"

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