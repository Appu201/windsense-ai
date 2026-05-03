# utils/model_trainer.py
import pandas as pd
import numpy as np
import pickle
import gzip
import json
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, RandomizedSearchCV, StratifiedKFold
from sklearn.metrics import classification_report, accuracy_score

BASE_PATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DATA_PATH  = os.path.join(BASE_PATH, 'data')
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

    # ── Duration features ────────────────────────────────────────
    df['duration_hours']     = df['Duration_Hours'].fillna(0)
    df['duration_minutes']   = df['duration_hours'] * 60
    df['duration_log']       = np.log1p(df['duration_hours'])
    df['is_long_duration']   = (df['duration_hours'] > 5).astype(int)
    df['is_short_duration']  = (df['duration_hours'] < 0.5).astype(int)
    df['is_medium_duration'] = ((df['duration_hours'] >= 0.5) & (df['duration_hours'] <= 5)).astype(int)

    # ── Time features ────────────────────────────────────────────
    df['hour_of_day']   = df['Start_Time'].dt.hour
    df['day_of_week']   = df['Start_Time'].dt.dayofweek
    df['month']         = df['Start_Time'].dt.month
    df['quarter']       = df['Start_Time'].dt.quarter
    df['is_weekend']    = (df['day_of_week'] >= 5).astype(int)
    df['is_peak_hours'] = df['hour_of_day'].apply(
        lambda h: 1 if (7 <= h <= 10 or 17 <= h <= 21) else 0
    )
    df['season'] = df['month'].apply(
        lambda m: 0 if m in [10,11,12,1,2] else (1 if m in [3,4,5,6] else 2)
    )
    df['hour_sin'] = np.sin(2 * np.pi * df['hour_of_day'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour_of_day'] / 24)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

    # ── Turbine features ─────────────────────────────────────────
    df['turbine_id_num']  = pd.to_numeric(df['Asset_ID'], errors='coerce').fillna(-1)
    df['status_type_num'] = df['Status_Type'].fillna(0)
    df['is_status_5']     = (df['status_type_num'] == 5).astype(int)
    df['is_status_4']     = (df['status_type_num'] == 4).astype(int)
    df['is_status_3']     = (df['status_type_num'] == 3).astype(int)

    # ── Turbine-level aggregates ─────────────────────────────────
    df['turbine_alarm_frequency'] = df.groupby('Asset_ID')['Alarm_Type'].transform('count')
    df['turbine_avg_duration']    = df.groupby('Asset_ID')['Duration_Hours'].transform('mean').fillna(0)
    df['turbine_max_duration']    = df.groupby('Asset_ID')['Duration_Hours'].transform('max').fillna(0)
    df['turbine_min_duration']    = df.groupby('Asset_ID')['Duration_Hours'].transform('min').fillna(0)
    df['turbine_std_duration']    = df.groupby('Asset_ID')['Duration_Hours'].transform('std').fillna(0)
    df['duration_rank']           = df.groupby('Asset_ID')['duration_hours'].rank(pct=True).fillna(0)
    df['duration_vs_turbine_avg'] = df['duration_hours'] - df['turbine_avg_duration']

    # ── Department encoding ──────────────────────────────────────
    dept_map = {d: i for i, d in enumerate(df['Primary_Department'].unique())}
    df['dept_encoded'] = df['Primary_Department'].map(dept_map).fillna(-1)

    # ── Status × duration interactions ───────────────────────────
    df['status5_x_duration'] = df['is_status_5'] * df['duration_hours']
    df['status4_x_duration'] = df['is_status_4'] * df['duration_hours']
    df['status3_x_duration'] = df['is_status_3'] * df['duration_hours']
    df['status5_x_log']      = df['is_status_5'] * df['duration_log']
    df['status4_x_log']      = df['is_status_4'] * df['duration_log']

    # ── Turbine × status interactions ────────────────────────────
    df['turbine_x_status']   = df['turbine_id_num'] * df['status_type_num']
    df['turbine_x_duration'] = df['turbine_id_num'] * df['duration_log']

    feature_cols = [
        # Duration
        'duration_hours', 'duration_minutes', 'duration_log',
        'is_long_duration', 'is_short_duration', 'is_medium_duration',
        # Time
        'hour_of_day', 'day_of_week', 'month', 'quarter', 'season',
        'is_weekend', 'is_peak_hours',
        'hour_sin', 'hour_cos', 'month_sin', 'month_cos',
        # Turbine & status
        'turbine_id_num', 'status_type_num',
        'is_status_5', 'is_status_4', 'is_status_3',
        # Aggregates
        'turbine_alarm_frequency', 'turbine_avg_duration',
        'turbine_max_duration', 'turbine_min_duration',
        'turbine_std_duration', 'duration_rank',
        'duration_vs_turbine_avg',
        # Encoded
        'dept_encoded',
        # Interactions
        'status5_x_duration', 'status4_x_duration', 'status3_x_duration',
        'status5_x_log', 'status4_x_log',
        'turbine_x_status', 'turbine_x_duration',
    ]

    X = df[feature_cols].fillna(0)
    y = df['Alarm_Type']
    print(f"\nFeature matrix: {X.shape}")
    return X, y, feature_cols

def train_model(X, y):
    # Drop singleton classes
    class_counts  = y.value_counts()
    valid_classes = class_counts[class_counts >= 2].index
    mask = y.isin(valid_classes)
    X = X[mask]
    y = y[mask]
    print(f"\nClasses after filtering singletons: {y.nunique()}")

    # SMOTETomek resampling
    try:
        from imblearn.combine import SMOTETomek
        smt = SMOTETomek(random_state=42)
        X_res, y_res = smt.fit_resample(X, y)
        print(f"After SMOTETomek: {len(X_res)} samples")
    except ImportError:
        print("imblearn not installed — pip install imbalanced-learn")
        print("Continuing without resampling (accuracy will be lower)")
        X_res, y_res = X, y

    X_train, X_test, y_train, y_test = train_test_split(
        X_res, y_res, test_size=0.2, random_state=42, stratify=y_res
    )
    print(f"Train: {len(X_train)} | Test: {len(X_test)}")

    # Hyperparameter search
    param_grid = {
        'n_estimators':      [200, 350, 500],
        'max_depth':         [20, 30, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf':  [1, 2, 4],
        'max_features':      ['sqrt', 'log2'],
    }

    rf     = RandomForestClassifier(class_weight='balanced', random_state=42, n_jobs=-1)
    cv     = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    search = RandomizedSearchCV(
        rf, param_grid,
        n_iter=30,
        cv=cv,
        scoring='accuracy',
        n_jobs=-1,
        random_state=42,
        verbose=1
    )

    print("\nRunning hyperparameter search (10–20 min)...")
    search.fit(X_train, y_train)

    best_model = search.best_estimator_
    print(f"\nBest params:      {search.best_params_}")
    print(f"Best CV accuracy: {search.best_score_*100:.2f}%")

    # Evaluate
    y_pred   = best_model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nTest accuracy: {accuracy*100:.2f}%")
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    cv_scores = cross_val_score(best_model, X_res, y_res, cv=5, scoring='accuracy')
    print(f"\nCV scores: {cv_scores}")
    print(f"CV Mean:   {cv_scores.mean()*100:.2f}% (+/- {cv_scores.std()*100:.2f}%)")

    return best_model, accuracy, cv_scores, y_res

def save_model(rf, feature_cols, accuracy, cv_scores, y):
    os.makedirs(MODEL_PATH, exist_ok=True)

    # Save as gzip (matches what Realtime.py loads)
    model_gz = os.path.join(MODEL_PATH, 'windsense_rf_model.pkl.gz')
    with gzip.open(model_gz, 'wb') as f:
        pickle.dump(rf, f)
    print(f"\nModel saved: {model_gz}")
    print(f"Model size:  {os.path.getsize(model_gz)/1e6:.1f} MB")

    # Also save plain pkl for compatibility
    model_pkl = os.path.join(MODEL_PATH, 'windsense_rf_model.pkl')
    with open(model_pkl, 'wb') as f:
        pickle.dump(rf, f, protocol=4)

    features_file = os.path.join(MODEL_PATH, 'feature_names.pkl')
    with open(features_file, 'wb') as f:
        pickle.dump(feature_cols, f)

    metadata_file = os.path.join(MODEL_PATH, 'model_metadata.json')
    metadata = {
        "model_type":         "RandomForestClassifier",
        "n_estimators":       rf.n_estimators,
        "max_depth":          str(rf.max_depth),
        "min_samples_split":  rf.min_samples_split,
        "min_samples_leaf":   rf.min_samples_leaf,
        "max_features":       rf.max_features,
        "accuracy":           round(accuracy * 100, 2),
        "cv_mean_accuracy":   round(cv_scores.mean() * 100, 2),
        "cv_std":             round(cv_scores.std() * 100, 2),
        "n_features":         len(feature_cols),
        "n_classes":          y.nunique(),
        "classes":            sorted(y.unique().tolist()),
        "training_date":      str(pd.Timestamp.now()),
        "feature_names":      feature_cols,
        "phase":              "Phase 3 — SMOTETomek + RandomizedSearchCV + interaction features"
    }
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved: {metadata_file}")

def run_retraining():
    print("=" * 60)
    print("WINDSENSE AI — PHASE 3 ML RETRAINING")
    print("SMOTETomek + RandomizedSearchCV + 37 features")
    print("=" * 60)

    episodes              = load_training_data()
    X, y, feature_cols    = engineer_features(episodes)
    rf, accuracy, cv_scores, y_res = train_model(X, y)
    save_model(rf, feature_cols, accuracy, cv_scores, y_res)

    print("\n" + "=" * 60)
    print(f"DONE — Test Accuracy: {accuracy*100:.2f}% | CV Mean: {cv_scores.mean()*100:.2f}%")
    print("=" * 60)

if __name__ == "__main__":
    run_retraining()