from utils.database import init_db, save_acknowledgment, load_acknowledgments

init_db()

save_acknowledgment('ALM-TEST-001', {
    'technician': 'Test Person',
    'ack_time': '2026-03-19 12:00:00',
    'action_taken': 'Testing',
    'notes': 'Database test',
    'response_time': 5.0,
    'alarm_data': {
        'predicted_type': 'Grid Fault',
        'asset_id': 10,
        'priority': 'CRITICAL'
    },
    'method': 'dashboard'
})

acks = load_acknowledgments()
print(f"Loaded {len(acks)} acknowledgments")
print(f"Test record found: {'ALM-TEST-001' in acks}")