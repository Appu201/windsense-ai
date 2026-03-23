# utils/model_trainer.py
# Phase 2: Retrain RF model with better grid alarm separation
# Key fix: add duration_hours and time-based features to separate
# Extended Grid Outage / Grid Frequency Deviation / Momentary Grid Loss
# which all bleed together because sensor readings are nearly identical

import pandas as pd
import numpy as np
import pickle
import json
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score

BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DATA_PATH = os.path.join(BASE_PATH, 'data')
MODEL_PATH = os.path.join(BASE_PATH, 'models')

def load_training_data():
    """Load and prepare training data with engineered features"""
    episodes_path = os.path.join(DATA_PATH, 'detailed_classified_alarm_episodes.csv')
    episodes = pd.read_csv(episodes_path)

    print(f"Loaded {len(episodes)} alarm episodes")
    print(f"Alarm types: {episodes['Alarm_Type'].nunique()}")
    print(f"Distribution:\n{episodes['Alarm_Type'].value_counts()}")

    return episodes

def engineer_features(episodes):
    """
    Create features that help SEPARATE the 5 confused grid alarm types:
    - Extended Grid Outage (long duration, very low power)
    - Grid Frequency Deviation (short duration, moderate power drop)
    - Momentary Grid Loss (very short, near-zero power)
    - Main Controller Fault (medium duration, affects all turbines)
    - Grid Voltage Fluctuation (short, power fluctuates not zero)
    """

    df = episodes.copy()

    # Convert times
    df['Start_Time'] = pd.to_datetime(df['Start_Time'])
    df['End_Time'] = pd.to_datetime(df['End_Time'])

    # Duration is the #1 separator for grid alarms
    df['duration_hours'] = df['Duration_Hours'].fillna(0)
    df['duration_minutes'] = df['duration_hours'] * 60
    df['is_long_duration'] = (df['duration_hours'] > 5).astype(int)    # Extended Grid Outage
    df['is_short_duration'] = (df['duration_hours'] < 0.5).astype(int) # Momentary / Frequency
    df['is_medium_duration'] = ((df['duration_hours'] >= 0.5) & (df['duration_hours'] <= 5)).astype(int)

    # Time of day features
    df['hour_of_day'] = df['Start_Time'].dt.hour
    df['is_peak_hours'] = df['hour_of_day'].apply(
        lambda h: 1 if (7 <= h <= 10 or 17 <= h <= 21) else 0
    )

    # Season (Indian context: winter = Oct-Feb, summer = Mar-Jun, monsoon = Jul-Sep)
    df['month'] = df['Start_Time'].dt.month
    df['season'] = df['month'].apply(
        lambda m: 0 if m in [10, 11, 12, 1, 2] else (1 if m in [3, 4, 5, 6] else 2)
    )

    # Turbine ID as numeric
    df['turbine_id_num'] = pd.to_numeric(df['Asset_ID'], errors='coerce').fillna(-1)

    # Status type (3/4/5) — already a strong separator between hydraulic/electrical/emergency
    df['status_type_num'] = df['Status_Type'].fillna(0)

    # Alarm frequency per turbine — recurring alarm indicator
    turbine_counts = df.groupby('Asset_ID')['Alarm_Type'].transform('count')
    df['turbine_alarm_frequency'] = turbine_counts

    feature_cols = [
        'duration_hours',
        'duration_minutes',
        'is_long_duration',
        'is_short_duration',
        'is_medium_duration',
        'hour_of_day',
        'is_peak_hours',
        'season',
        'month',
        'turbine_id_num',
        'status_type_num',
        'turbine_alarm_frequency'
    ]

    X = df[feature_cols].fillna(0)
    y = df['Alarm_Type']

    return X, y, feature_cols

def train_model(X, y):
    """Train Random Forest with optimised parameters"""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\nTraining samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")
    print(f"Classes: {y.nunique()}")

    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=25,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight='balanced',  # handles class imbalance
        random_state=42,
        n_jobs=-1
    )

    print("\nTraining model...")
    rf.fit(X_train, y_train)

    y_pred = rf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\nAccuracy: {accuracy*100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    # Cross validation
    cv_scores = cross_val_score(rf, X, y, cv=5, scoring='accuracy')
    print(f"\nCross-validation scores: {cv_scores}")
    print(f"CV Mean: {cv_scores.mean()*100:.2f}% (+/- {cv_scores.std()*100:.2f}%)")

    return rf, X_train, X_test, y_train, y_test, accuracy, cv_scores

def save_model(rf, feature_cols, accuracy, cv_scores, y):
    """Save retrained model and metadata"""
    model_file = os.path.join(MODEL_PATH, 'windsense_rf_model.pkl')
    features_file = os.path.join(MODEL_PATH, 'feature_names.pkl')
    metadata_file = os.path.join(MODEL_PATH, 'model_metadata.json')

    with open(model_file, 'wb') as f:
        pickle.dump(rf, f)
    print(f"\nModel saved: {model_file}")

    with open(features_file, 'wb') as f:
        pickle.dump(feature_cols, f)
    print(f"Features saved: {features_file}")

    metadata = {
        "model_type": "RandomForestClassifier",
        "n_estimators": 200,
        "max_depth": 25,
        "accuracy": round(accuracy * 100, 2),
        "cv_mean_accuracy": round(cv_scores.mean() * 100, 2),
        "cv_std": round(cv_scores.std() * 100, 2),
        "training_samples": "all episodes",
        "n_features": len(feature_cols),
        "n_classes": y.nunique(),
        "classes": sorted(y.unique().tolist()),
        "training_date": str(pd.Timestamp.now()),
        "feature_names": feature_cols,
        "phase": "Phase 2 retrain — duration + time features for grid alarm separation"
    }

    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved: {metadata_file}")

def run_retraining():
    """Full pipeline: load → engineer → train → save"""
    print("=" * 60)
    print("WINDSENSE AI — PHASE 2 ML RETRAINING")
    print("Fix: Grid alarm separation via duration + time features")
    print("=" * 60)

    episodes = load_training_data()
    X, y, feature_cols = engineer_features(episodes)
    rf, X_train, X_test, y_train, y_test, accuracy, cv_scores = train_model(X, y)
    save_model(rf, feature_cols, accuracy, cv_scores, y)

    print("\n" + "=" * 60)
    print("RETRAINING COMPLETE")
    print(f"New accuracy: {accuracy*100:.2f}%")
    print(f"CV mean: {cv_scores.mean()*100:.2f}%")
    print("Model saved. Restart dashboard to use new model.")
    print("=" * 60)

if __name__ == "__main__":
    run_retraining()
