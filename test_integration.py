# test_integration.py — Day 1 full integration test
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

results = []

print("=" * 55)
print("  WINDSENSE AI — DAY 1 INTEGRATION TEST")
print("=" * 55)

# Test 1: paths
print("\n[1] Testing utils/paths...")
try:
    from utils.paths import DATA_PATH, MODEL_PATH
    assert isinstance(DATA_PATH, str), "DATA_PATH not a string"
    assert isinstance(MODEL_PATH, str), "MODEL_PATH not a string"
    print(f"    DATA_PATH  = {DATA_PATH}")
    print(f"    MODEL_PATH = {MODEL_PATH}")
    print("    ✅ PASS")
    results.append(("utils/paths", True))
except Exception as e:
    print(f"    ❌ FAIL: {e}")
    results.append(("utils/paths", False))

# Test 2: database
print("\n[2] Testing utils/database...")
try:
    from utils.database import init_db, save_acknowledgment, load_acknowledgments, log_alarm
    init_db()
    saved = save_acknowledgment('INT-001', {
        'technician': 'IntegrationTest',
        'ack_time': '2026-03-19 18:00:00',
        'action_taken': 'Testing',
        'notes': 'Auto test',
        'response_time': 2.5,
        'alarm_data': {'predicted_type': 'Grid Fault', 'asset_id': 10, 'priority': 'CRITICAL'},
        'method': 'dashboard'
    })
    assert saved, "save_acknowledgment returned False"
    acks = load_acknowledgments()
    assert 'INT-001' in acks, "Saved record not found on load"
    print(f"    Saved and loaded 1 acknowledgment successfully")
    print("    ✅ PASS")
    results.append(("utils/database", True))
except Exception as e:
    print(f"    ❌ FAIL: {e}")
    results.append(("utils/database", False))

# Test 3: theme
print("\n[3] Testing utils/theme...")
try:
    from utils.theme import WINDSENSE_CSS, apply_theme, main_header
    assert len(WINDSENSE_CSS) > 500, "CSS is too short"
    print(f"    CSS length: {len(WINDSENSE_CSS)} characters")
    print("    ✅ PASS")
    results.append(("utils/theme", True))
except Exception as e:
    print(f"    ❌ FAIL: {e}")
    results.append(("utils/theme", False))

# Test 4: sidebar
print("\n[4] Testing utils/sidebar...")
try:
    from utils.sidebar import render_sidebar
    print("    Import successful")
    print("    ✅ PASS")
    results.append(("utils/sidebar", True))
except Exception as e:
    print(f"    ❌ FAIL: {e}")
    results.append(("utils/sidebar", False))

# Test 5: data_validator
print("\n[5] Testing utils/data_validator...")
try:
    from utils.data_validator import validate_all_files, validate_file_exists
    report = validate_all_files('data/')
    print(f"    Passed: {len(report['passed'])}")
    print(f"    Failed: {len(report['failed'])}")
    print(f"    Warnings: {len(report['warnings'])}")
    print(f"    Overall: {report['overall_status']}")
    print("    ✅ PASS")
    results.append(("utils/data_validator", True))
except Exception as e:
    print(f"    ❌ FAIL: {e}")
    results.append(("utils/data_validator", False))

# Test 6: CSV files in data/
print("\n[6] Testing data files...")
try:
    import pandas as pd
    files = [
        'dashboard_alarm_stream.csv',
        'top_50_unique_detailed_alarms.csv',
        'detailed_classified_alarm_episodes.csv'
    ]
    for f in files:
        path = os.path.join('data', f)
        if os.path.exists(path):
            df = pd.read_csv(path)
            print(f"    ✅ {f}: {len(df)} rows")
        else:
            print(f"    ⚠️  {f}: NOT FOUND (expected if not copied yet)")
    results.append(("data files", True))
except Exception as e:
    print(f"    ❌ FAIL: {e}")
    results.append(("data files", False))

# Summary
print("\n" + "=" * 55)
passed = sum(1 for _, ok in results if ok)
total = len(results)
print(f"  RESULT: {passed}/{total} tests passed")
for name, ok in results:
    status = "✅" if ok else "❌"
    print(f"  {status} {name}")
print("=" * 55)