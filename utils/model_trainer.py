# utils/model_trainer.py — UPGRADED: XGBoost + Ensemble + SMOTEENN + Tuning
import pandas as pd
import numpy as np
import pickle
import json
import os
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, VotingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, RandomizedSearchCV
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb

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

    # ── DURATION (strongest signal) ──────────────────────────────────────────
    df['duration_hours']     = df['Duration_Hours'].fillna(0)
    df['duration_minutes']   = df['duration_hours'] * 60
    df['duration_seconds']   = df['duration_hours'] * 3600        # NEW
    df['duration_log']       = np.log1p(df['duration_hours'])
    df['duration_sqrt']      = np.sqrt(df['duration_hours'])       # NEW
    df['duration_squared']   = df['duration_hours'] ** 2           # NEW
    df['is_long_duration']   = (df['duration_hours'] > 5).astype(int)
    df['is_short_duration']  = (df['duration_hours'] < 0.5).astype(int)
    df['is_micro_duration']  = (df['duration_hours'] < 0.083).astype(int)  # NEW <5min
    df['is_medium_duration'] = ((df['duration_hours'] >= 0.5) & (df['duration_hours'] <= 5)).astype(int)

    # ── TIME ─────────────────────────────────────────────────────────────────
    df['hour_of_day']    = df['Start_Time'].dt.hour
    df['day_of_week']    = df['Start_Time'].dt.dayofweek
    df['month']          = df['Start_Time'].dt.month
    df['quarter']        = df['Start_Time'].dt.quarter             # NEW
    df['day_of_year']    = df['Start_Time'].dt.dayofyear           # NEW
    df['week_of_year']   = df['Start_Time'].dt.isocalendar().week.astype(int)  # NEW
    df['is_weekend']     = (df['day_of_week'] >= 5).astype(int)
    df['is_peak_hours']  = df['hour_of_day'].apply(lambda h: 1 if (7<=h<=10 or 17<=h<=21) else 0)
    df['is_night']       = df['hour_of_day'].apply(lambda h: 1 if (h<6 or h>=22) else 0)  # NEW
    df['season']         = df['month'].apply(lambda m: 0 if m in [10,11,12,1,2] else (1 if m in [3,4,5,6] else 2))

    # Cyclical encoding — helps model understand circular time  # NEW
    df['hour_sin']  = np.sin(2 * np.pi * df['hour_of_day'] / 24)
    df['hour_cos']  = np.cos(2 * np.pi * df['hour_of_day'] / 24)
    df['dow_sin']   = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['dow_cos']   = np.cos(2 * np.pi * df['day_of_week'] / 7)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

    # ── TURBINE ───────────────────────────────────────────────────────────────
    df['turbine_id_num'] = pd.to_numeric(df['Asset_ID'], errors='coerce').fillna(-1)
    df['status_type_num'] = df['Status_Type'].fillna(0)
    df['is_status_5'] = (df['status_type_num'] == 5).astype(int)
    df['is_status_4'] = (df['status_type_num'] == 4).astype(int)
    df['is_status_3'] = (df['status_type_num'] == 3).astype(int)

    # ── TURBINE-LEVEL STATS ───────────────────────────────────────────────────
    df['turbine_alarm_frequency'] = df.groupby('Asset_ID')['Alarm_Type'].transform('count')
    df['turbine_avg_duration']    = df.groupby('Asset_ID')['Duration_Hours'].transform('mean').fillna(0)
    df['turbine_max_duration']    = df.groupby('Asset_ID')['Duration_Hours'].transform('max').fillna(0)   # NEW
    df['turbine_min_duration']    = df.groupby('Asset_ID')['Duration_Hours'].transform('min').fillna(0)   # NEW
    df['turbine_std_duration']    = df.groupby('Asset_ID')['Duration_Hours'].transform('std').fillna(0)   # NEW
    df['duration_rank']           = df.groupby('Asset_ID')['duration_hours'].rank(pct=True).fillna(0)

    # Duration vs turbine average (relative duration)  # NEW
    df['duration_vs_avg'] = df['duration_hours'] / (df['turbine_avg_duration'] + 1e-5)
    df['duration_vs_max'] = df['duration_hours'] / (df['turbine_max_duration'] + 1e-5)

    # ── INTERACTION FEATURES (cross-features) ─────────────────────────────────
    df['duration_x_hour']    = df['duration_hours'] * df['hour_of_day']      # NEW
    df['duration_x_dow']     = df['duration_hours'] * df['day_of_week']      # NEW
    df['duration_x_status']  = df['duration_hours'] * df['status_type_num']  # NEW
    df['turbine_x_status']   = df['turbine_id_num'] * df['status_type_num']  # NEW
    df['hour_x_season']      = df['hour_of_day'] * df['season']              # NEW
    df['status_x_season']    = df['status_type_num'] * df['season']          # NEW

    feature_cols = [
        # Duration
        'duration_hours', 'duration_minutes', 'duration_seconds',
        'duration_log', 'duration_sqrt', 'duration_squared',
        'is_long_duration', 'is_short_duration', 'is_micro_duration', 'is_medium_duration',
        # Time
        'hour_of_day', 'day_of_week', 'month', 'quarter', 'day_of_year', 'week_of_year',
        'is_weekend', 'is_peak_hours', 'is_night', 'season',
        # Cyclical
        'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos', 'month_sin', 'month_cos',
        # Turbine
        'turbine_id_num', 'status_type_num',
        'is_status_5', 'is_status_4', 'is_status_3',
        # Turbine stats
        'turbine_alarm_frequency', 'turbine_avg_duration',
        'turbine_max_duration', 'turbine_min_duration', 'turbine_std_duration',
        'duration_rank', 'duration_vs_avg', 'duration_vs_max',
        # Interactions
        'duration_x_hour', 'duration_x_dow', 'duration_x_status',
        'turbine_x_status', 'hour_x_season', 'status_x_season',
    ]

    X = df[feature_cols].fillna(0)
    y = df['Alarm_Type']
    return X, y, feature_cols


def resample_data(X, y):
    """SMOTEENN: oversample minorities + clean majority noise"""
    try:
        from imblearn.combine import SMOTEENN
        from imblearn.over_sampling import SMOTE
        min_samples = y.value_counts().min()
        k = min(5, min_samples - 1)
        if k >= 1:
            print("Applying SMOTEENN (SMOTE + Edited Nearest Neighbours)...")
            smote = SMOTE(random_state=42, k_neighbors=k)
            smoteenn = SMOTEENN(smote=smote, random_state=42)
            X_res, y_res = smoteenn.fit_resample(X, y)
            print(f"After SMOTEENN: {len(X_res)} samples")
        else:
            X_res, y_res = X, y
    except Exception as e:
        print(f"SMOTEENN failed ({e}), falling back to plain SMOTE")
        from imblearn.over_sampling import SMOTE
        min_samples = y.value_counts().min()
        k = min(5, min_samples - 1)
        sm = SMOTE(random_state=42, k_neighbors=k)
        X_res, y_res = sm.fit_resample(X, y)
        print(f"After SMOTE: {len(X_res)} samples")
    return X_res, y_res


def build_ensemble(X_train, y_train):
    """Voting ensemble: RF + ExtraTrees + XGBoost"""
    le = LabelEncoder()
    y_enc = le.fit_transform(y_train)

    # ── Random Forest (tuned) ─────────────────────────────────────────────────
    print("\nTuning Random Forest...")
    rf_params = {
        'n_estimators': [100, 200, 300],
        'max_depth': [15, 20, 25, None],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2],
        'max_features': ['sqrt', 'log2'],
    }
    rf_base = RandomForestClassifier(class_weight='balanced', random_state=42, n_jobs=-1)
    rf_search = RandomizedSearchCV(rf_base, rf_params, n_iter=15, cv=3,
                                   scoring='accuracy', random_state=42, n_jobs=-1, verbose=1)
    rf_search.fit(X_train, y_train)
    best_rf = rf_search.best_estimator_
    print(f"Best RF params: {rf_search.best_params_}")
    print(f"RF CV best: {rf_search.best_score_*100:.2f}%")

    # ── Extra Trees ───────────────────────────────────────────────────────────
    print("\nTraining Extra Trees...")
    et = ExtraTreesClassifier(
        n_estimators=200, max_depth=20,
        class_weight='balanced', random_state=42, n_jobs=-1
    )
    et.fit(X_train, y_train)

    # ── XGBoost ───────────────────────────────────────────────────────────────
    print("\nTuning XGBoost...")
    n_classes = len(np.unique(y_enc))
    xgb_params = {
        'n_estimators': [200, 300, 400],
        'max_depth': [4, 6, 8],
        'learning_rate': [0.05, 0.1, 0.15],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.7, 0.9],
        'min_child_weight': [1, 3],
    }
    xgb_base = xgb.XGBClassifier(
        objective='multi:softprob',
        num_class=n_classes,
        eval_metric='mlogloss',
        use_label_encoder=False,
        random_state=42,
        n_jobs=-1,
        verbosity=0
    )
    xgb_search = RandomizedSearchCV(xgb_base, xgb_params, n_iter=15, cv=3,
                                    scoring='accuracy', random_state=42, n_jobs=-1, verbose=1)
    xgb_search.fit(X_train, y_enc)
    print(f"Best XGB params: {xgb_search.best_params_}")
    print(f"XGB CV best: {xgb_search.best_score_*100:.2f}%")

    return best_rf, et, xgb_search.best_estimator_, le


def train_model(X, y):
    # Drop singletons
    class_counts = y.value_counts()
    valid_classes = class_counts[class_counts >= 2].index
    mask = y.isin(valid_classes)
    X, y = X[mask], y[mask]
    print(f"Classes after filtering singletons: {y.nunique()}")

    X_res, y_res = resample_data(X, y)

    X_train, X_test, y_train, y_test = train_test_split(
        X_res, y_res, test_size=0.2, random_state=42, stratify=y_res
    )
    print(f"Train: {len(X_train)} | Test: {len(X_test)}")

    best_rf, et, best_xgb, le = build_ensemble(X_train, y_train)

    # ── Evaluate each model ───────────────────────────────────────────────────
    print("\n── Per-model accuracy on test set ──")
    rf_acc = accuracy_score(y_test, best_rf.predict(X_test))
    et_acc = accuracy_score(y_test, et.predict(X_test))
    y_test_enc = le.transform(y_test)
    xgb_pred_enc = best_xgb.predict(X_test)
    xgb_pred = le.inverse_transform(xgb_pred_enc)
    xgb_acc = accuracy_score(y_test, xgb_pred)
    print(f"  Random Forest : {rf_acc*100:.2f}%")
    print(f"  Extra Trees   : {et_acc*100:.2f}%")
    print(f"  XGBoost       : {xgb_acc*100:.2f}%")

    # ── Voting Ensemble (soft voting where possible) ──────────────────────────
    # We use majority vote across the 3 predictions
    rf_preds  = best_rf.predict(X_test)
    et_preds  = et.predict(X_test)
    xgb_preds = xgb_pred

    # Majority vote
    from scipy import stats
    ensemble_preds = []
    for rf_p, et_p, xgb_p in zip(rf_preds, et_preds, xgb_preds):
        vote = stats.mode([rf_p, et_p, xgb_p], keepdims=True).mode[0]
        ensemble_preds.append(vote)

    ensemble_acc = accuracy_score(y_test, ensemble_preds)
    print(f"\n✅ ENSEMBLE accuracy: {ensemble_acc*100:.2f}%")
    print("\nClassification Report (Ensemble):")
    print(classification_report(y_test, ensemble_preds, zero_division=0))

    # CV on best single model (RF — XGB CV already done)
    print("\nCross-validating best RF...")
    cv_scores = cross_val_score(best_rf, X_res, y_res, cv=5, scoring='accuracy')
    print(f"CV scores: {cv_scores}")
    print(f"CV Mean: {cv_scores.mean()*100:.2f}% (+/- {cv_scores.std()*100:.2f}%)")

    return best_rf, et, best_xgb, le, ensemble_acc, cv_scores, y_res


def save_model(best_rf, et, best_xgb, le, feature_cols, accuracy, cv_scores, y):
    os.makedirs(MODEL_PATH, exist_ok=True)

    # Save all models
    with open(os.path.join(MODEL_PATH, 'windsense_rf_model.pkl'), 'wb') as f:
        pickle.dump(best_rf, f, protocol=4)
    with open(os.path.join(MODEL_PATH, 'windsense_et_model.pkl'), 'wb') as f:
        pickle.dump(et, f, protocol=4)
    with open(os.path.join(MODEL_PATH, 'windsense_xgb_model.pkl'), 'wb') as f:
        pickle.dump(best_xgb, f, protocol=4)
    with open(os.path.join(MODEL_PATH, 'windsense_label_encoder.pkl'), 'wb') as f:
        pickle.dump(le, f, protocol=4)
    with open(os.path.join(MODEL_PATH, 'feature_names.pkl'), 'wb') as f:
        pickle.dump(feature_cols, f)

    metadata = {
        "model_type": "VotingEnsemble (RF + ExtraTrees + XGBoost)",
        "accuracy": round(accuracy * 100, 2),
        "cv_mean_accuracy": round(cv_scores.mean() * 100, 2),
        "cv_std": round(cv_scores.std() * 100, 2),
        "n_features": len(feature_cols),
        "n_classes": y.nunique(),
        "classes": sorted(y.unique().tolist()),
        "training_date": str(pd.Timestamp.now()),
        "feature_names": feature_cols,
        "phase": "Phase 3 — Ensemble + SMOTEENN + Cyclical Features + Interactions"
    }
    with open(os.path.join(MODEL_PATH, 'model_metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\nAll models saved to {MODEL_PATH}")


def run_retraining():
    print("=" * 60)
    print("WINDSENSE AI — PHASE 3: ENSEMBLE UPGRADE")
    print("=" * 60)
    episodes = load_training_data()
    X, y, feature_cols = engineer_features(episodes)
    best_rf, et, best_xgb, le, acc, cv_scores, y_res = train_model(X, y)
    save_model(best_rf, et, best_xgb, le, feature_cols, acc, cv_scores, y_res)
    print("\n" + "=" * 60)
    print(f"DONE — Ensemble: {acc*100:.2f}% | CV Mean: {cv_scores.mean()*100:.2f}%")
    print("=" * 60)

if __name__ == "__main__":
    run_retraining()