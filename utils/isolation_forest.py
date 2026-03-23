# utils/isolation_forest.py
# Phase 2: Isolation Forest anomaly detection
# Detects new/unseen alarm patterns not in the 19 trained classes
<<<<<<< HEAD
=======
# Integrates with live alarm buffer from dashboard
>>>>>>> 55311577d983769b61efb68407e7614d72adb055

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import json
import os

BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DATA_PATH = os.path.join(BASE_PATH, 'data')

SENSOR_FEATURES = [
    'sensor_11_avg',
    'sensor_12_avg',
    'sensor_13_avg',
    'sensor_14_avg',
    'sensor_41_avg',
    'sensor_38_avg',
    'sensor_39_avg',
    'sensor_40_avg',
    'power_30_avg',
    'sensor_18_avg',
    'wind_speed_3_avg'
]

ANOMALY_LOG_FILE = os.path.join(DATA_PATH, 'anomaly_log.json')


class IsolationForestDetector:
<<<<<<< HEAD
=======
    """
    Isolation Forest wrapper for WindSense AI.
    Trains on the current alarm buffer.
    Flags alarms that don't match any known pattern.
    Logs anomalies to anomaly_log.json for review.
    """

>>>>>>> 55311577d983769b61efb68407e7614d72adb055
    def __init__(self, contamination=0.1):
        self.contamination = contamination
        self.model = None
        self.is_trained = False
        self.features_used = []
        self.anomaly_log = self._load_anomaly_log()
        self.training_sample_count = 0

    def _load_anomaly_log(self):
<<<<<<< HEAD
=======
        """Load existing anomaly log or return empty dict"""
>>>>>>> 55311577d983769b61efb68407e7614d72adb055
        if os.path.exists(ANOMALY_LOG_FILE):
            try:
                with open(ANOMALY_LOG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_anomaly_log(self):
<<<<<<< HEAD
=======
        """Save anomaly log to file"""
>>>>>>> 55311577d983769b61efb68407e7614d72adb055
        try:
            with open(ANOMALY_LOG_FILE, 'w') as f:
                json.dump(self.anomaly_log, f, indent=2)
        except Exception as e:
            print(f"Could not save anomaly log: {e}")

    def _prepare_features(self, alarm_buffer):
<<<<<<< HEAD
        df = pd.DataFrame(alarm_buffer)
        available = [f for f in SENSOR_FEATURES if f in df.columns]
        self.features_used = available
        if not available:
            return None
=======
        """Extract available sensor features from alarm buffer"""
        df = pd.DataFrame(alarm_buffer)

        # Use whichever sensor features exist in this data
        available = [f for f in SENSOR_FEATURES if f in df.columns]
        self.features_used = available

        if not available:
            return None

>>>>>>> 55311577d983769b61efb68407e7614d72adb055
        X = df[available].fillna(0).values
        return X

    def train(self, alarm_buffer):
<<<<<<< HEAD
        if len(alarm_buffer) < 10:
            return False
        X = self._prepare_features(alarm_buffer)
        if X is None:
            return False
=======
        """
        Train the Isolation Forest on current alarm buffer.
        Returns True if training succeeded, False if not enough data.
        """
        if len(alarm_buffer) < 10:
            return False

        X = self._prepare_features(alarm_buffer)
        if X is None:
            return False

>>>>>>> 55311577d983769b61efb68407e7614d72adb055
        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=100,
            random_state=42
        )
        self.model.fit(X)
        self.is_trained = True
        self.training_sample_count = len(alarm_buffer)
        return True

    def predict(self, alarm_dict):
<<<<<<< HEAD
        if not self.is_trained or self.model is None:
            return False, 0.0
        try:
            feature_vector = [alarm_dict.get(f, 0) for f in self.features_used]
            X = np.array(feature_vector).reshape(1, -1)
            prediction = self.model.predict(X)[0]
            score = self.model.score_samples(X)[0]
            normalised = max(0.0, min(1.0, (-score - 0.1) / 0.6))
            is_anomaly = (prediction == -1)
            return is_anomaly, round(normalised, 3)
=======
        """
        Predict if a single alarm is anomalous.
        Returns: (is_anomaly: bool, anomaly_score: float)
        anomaly_score: higher = more anomalous (0 to 1 scale)
        """
        if not self.is_trained or self.model is None:
            return False, 0.0

        try:
            feature_vector = [alarm_dict.get(f, 0) for f in self.features_used]
            X = np.array(feature_vector).reshape(1, -1)

            prediction = self.model.predict(X)[0]  # -1 = anomaly, 1 = normal
            score = self.model.score_samples(X)[0]  # more negative = more anomalous

            # Normalise score to 0-1 where 1 = most anomalous
            # Typical range is -0.7 to 0.1, so we clip and scale
            normalised = max(0.0, min(1.0, (-score - 0.1) / 0.6))

            is_anomaly = (prediction == -1)
            return is_anomaly, round(normalised, 3)

>>>>>>> 55311577d983769b61efb68407e7614d72adb055
        except Exception:
            return False, 0.0

    def log_anomaly(self, alarm_dict, anomaly_score):
<<<<<<< HEAD
=======
        """Log a detected anomaly for operator review"""
>>>>>>> 55311577d983769b61efb68407e7614d72adb055
        alarm_id = alarm_dict.get('alarm_id', 'unknown')
        self.anomaly_log[alarm_id] = {
            'alarm_id': alarm_id,
            'timestamp': alarm_dict.get('timestamp', ''),
            'turbine': alarm_dict.get('asset_id', ''),
            'anomaly_score': anomaly_score,
            'sensor_snapshot': {f: alarm_dict.get(f, 0) for f in self.features_used},
            'status': 'pending_review',
            'operator_label': None
        }
        self._save_anomaly_log()

    def label_anomaly(self, alarm_id, operator_label):
<<<<<<< HEAD
=======
        """Operator provides a label for a flagged anomaly (learning loop)"""
>>>>>>> 55311577d983769b61efb68407e7614d72adb055
        if alarm_id in self.anomaly_log:
            self.anomaly_log[alarm_id]['operator_label'] = operator_label
            self.anomaly_log[alarm_id]['status'] = 'labelled'
            self._save_anomaly_log()
            return True
        return False

    def get_pending_reviews(self):
<<<<<<< HEAD
=======
        """Return all anomalies awaiting operator review"""
>>>>>>> 55311577d983769b61efb68407e7614d72adb055
        return {
            aid: data for aid, data in self.anomaly_log.items()
            if data.get('status') == 'pending_review'
        }

    def get_stats(self):
<<<<<<< HEAD
=======
        """Return summary statistics"""
>>>>>>> 55311577d983769b61efb68407e7614d72adb055
        total = len(self.anomaly_log)
        pending = len(self.get_pending_reviews())
        labelled = total - pending
        return {
            'total_anomalies_detected': total,
            'pending_review': pending,
            'labelled': labelled,
            'training_samples': self.training_sample_count,
            'features_used': len(self.features_used)
        }