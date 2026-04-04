# utils/model_trainer.py
import pandas as pd
import numpy as np
import pickle
import json
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder

BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DATA_PATH = os.path.join(BASE_PATH, 'data')
MODEL_PATH = os.path.join(BASE_PATH, 'models')

def load_training_data():
    episodes_path = os.path.join(DATA_PATH, 'detailed_classified_alarm_episodes.csv')
    episodes = pd.read_csv(episodes_path)
    print(f"Loaded {len(episodes)} alarm episodes")
    print(f"Alarm types: {episodes['Alarm_Type'].nunique()}")
    print(f"Distribution:\n{episodes['Alarm_Type'].value_counts()}")
    return episodes

def engineer_features(episodes):
    df = episodes.copy()

    df['Start_Time'] = pd.to_datetime(df['Start_Time'])
    df['End_Time']   = pd.to_datetime(df['End_Time'])

    # Duration features — #1 separator
    df['duration_hours']     = df['Duration_Hours'].fillna(0)
    df['duration_minutes']   = df['duration_hours'] * 60
    df['duration_log']       = np.log1p(df['duration_hours'])
    df['is_long_duration']   = (df['duration_hours'] > 5).astype(int)
    df['is_short_duration']  = (df['duration_hours'] < 0.5).astype(int)
    df['is_medium_duration'] = ((df['duration_hours'] >= 0.5) & (df['duration_hours'] <= 5)).astype(int)

    # Time features
    df['hour_of_day']  = df['Start_Time'].dt.hour
    df['day_of_week']  = df['Start_Time'].dt.dayofweek
    df['month']        = df['Start_Time'].dt.month
    df['is_weekend']   = (df['day_of_week'] >= 5).astype(int)
    df['is_peak_hours'] = df['hour_of_day'].apply(lambda h: 1 if (7 <= h <= 10 or 17 <= h <= 21) else 0)
    df['season']       = df['month'].apply(lambda m: 0 if m in [10,11,12,1,2] else (1 if m in [3,4,5,6] else 2))

    # Turbine
    df['turbine_id_num'] = pd.to_numeric(df['Asset_ID'], errors='coerce').fillna(-1)

    # Status type
    df['status_type_num'] = df['Status_Type'].fillna(0)
    df['is_status_5'] = (df['status_type_num'] == 5).astype(int)
    df['is_status_4'] = (df['status_type_num'] == 4).astype(int)
    df['is_status_3'] = (df['status_type_num'] == 3).astype(int)

    # Turbine-level stats
    df['turbine_alarm_frequency'] = df.groupby('Asset_ID')['Alarm_Type'].transform('count')
    df['turbine_avg_duration']    = df.groupby('Asset_ID')['Duration_Hours'].transform('mean').fillna(0)

    # Duration percentile within turbine
    df['duration_rank'] = df.groupby('Asset_ID')['duration_hours'].rank(pct=True).fillna(0)

    feature_cols = [
        'duration_hours', 'duration_minutes', 'duration_log',
        'is_long_duration', 'is_short_duration', 'is_medium_duration',
        'hour_of_day', 'day_of_week', 'month', 'season',
        'is_weekend', 'is_peak_hours',
        'turbine_id_num', 'status_type_num',
        'is_status_5', 'is_status_4', 'is_status_3',
        'turbine_alarm_frequency', 'turbine_avg_duration', 'duration_rank'
    ]

    X = df[feature_cols].fillna(0)
    y = df['Alarm_Type']
    return X, y, feature_cols

def train_model(X, y):
    # Drop classes with fewer than 2 samples (can't stratify or SMOTE)
    class_counts = y.value_counts()
    valid_classes = class_counts[class_counts >= 2].index
    mask = y.isin(valid_classes)
    X = X[mask]
    y = y[mask]
    print(f"\nClasses after filtering singletons: {y.nunique()}")

    # SMOTE oversample minority classes
    try:
        from imblearn.over_sampling import SMOTE
        min_samples = y.value_counts().min()
        k = min(5, min_samples - 1)
        if k >= 1:
            sm = SMOTE(random_state=42, k_neighbors=k)
            X_res, y_res = sm.fit_resample(X, y)
            print(f"After SMOTE: {len(X_res)} samples")
        else:
            X_res, y_res = X, y
            print("SMOTE skipped — too few minority samples")
    except ImportError:
        print("imblearn not found — install with: pip install imbalanced-learn")
        print("Continuing without SMOTE (accuracy will be lower)")
        X_res, y_res = X, y

    X_train, X_test, y_train, y_test = train_test_split(
        X_res, y_res, test_size=0.2, random_state=42, stratify=y_res
    )

    print(f"Training samples: {len(X_train)}")
    print(f"Test samples:     {len(X_test)}")

    rf = RandomForestClassifier(
        n_estimators=50,
        max_depth=20,
        min_samples_split=2,
        min_samples_leaf=1,
        class_weight='balanced',
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

    cv_scores = cross_val_score(rf, X_res, y_res, cv=5, scoring='accuracy')
    print(f"\nCV scores: {cv_scores}")
    print(f"CV Mean:   {cv_scores.mean()*100:.2f}% (+/- {cv_scores.std()*100:.2f}%)")

    return rf, accuracy, cv_scores, y_res

def save_model(rf, feature_cols, accuracy, cv_scores, y):
    os.makedirs(MODEL_PATH, exist_ok=True)

    model_file    = os.path.join(MODEL_PATH, 'windsense_rf_model.pkl')
    features_file = os.path.join(MODEL_PATH, 'feature_names.pkl')
    metadata_file = os.path.join(MODEL_PATH, 'model_metadata.json')

    with open(model_file, 'wb') as f:
        pickle.dump(rf, f, protocol=4)
    print(f"\nModel saved: {model_file}")
    print(f"Model size:  {os.path.getsize(model_file)/1e6:.1f} MB")

    with open(features_file, 'wb') as f:
        pickle.dump(feature_cols, f)

    metadata = {
        "model_type": "RandomForestClassifier",
        "n_estimators": 50,
        "max_depth": 20,
        "accuracy": round(accuracy * 100, 2),
        "cv_mean_accuracy": round(cv_scores.mean() * 100, 2),
        "cv_std": round(cv_scores.std() * 100, 2),
        "n_features": len(feature_cols),
        "n_classes": y.nunique(),
        "classes": sorted(y.unique().tolist()),
        "training_date": str(pd.Timestamp.now()),
        "feature_names": feature_cols,
        "phase": "Phase 2 retrain — SMOTE + balanced RF"
    }
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved: {metadata_file}")

def run_retraining():
    print("=" * 60)
    print("WINDSENSE AI — PHASE 2 ML RETRAINING (SMOTE + Balanced RF)")
    print("=" * 60)

    episodes = load_training_data()
    X, y, feature_cols = engineer_features(episodes)
    rf, accuracy, cv_scores, y_res = train_model(X, y)
    save_model(rf, feature_cols, accuracy, cv_scores, y_res)

    print("\n" + "=" * 60)
    print(f"DONE — Accuracy: {accuracy*100:.2f}% | CV: {cv_scores.mean()*100:.2f}%")
    print("=" * 60)

if __name__ == "__main__":
    run_retraining()