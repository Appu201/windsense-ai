# utils/database.py — SQLite persistent storage for WindSense AI
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'windsense.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS acknowledgments (
            alarm_id TEXT PRIMARY KEY,
            technician TEXT,
            ack_time TEXT,
            action_taken TEXT,
            notes TEXT,
            response_time_min REAL,
            alarm_type TEXT,
            turbine_id TEXT,
            priority TEXT,
            method TEXT DEFAULT 'dashboard'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alarm_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alarm_id TEXT,
            alarm_type TEXT,
            turbine_id TEXT,
            priority TEXT,
            confidence REAL,
            detected_at TEXT,
            status TEXT DEFAULT 'ACTIVE'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alarm_id TEXT,
            alarm_type TEXT,
            recipient_name TEXT,
            recipient_email TEXT,
            notification_type TEXT,
            sent_at TEXT,
            status TEXT
        )
    ''')

    conn.commit()
    conn.close()

def save_acknowledgment(alarm_id, ack_data):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        alarm_data = ack_data.get('alarm_data', {})
        cursor.execute('''
            INSERT OR REPLACE INTO acknowledgments
            (alarm_id, technician, ack_time, action_taken, notes,
             response_time_min, alarm_type, turbine_id, priority, method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            alarm_id,
            ack_data.get('technician', 'Email'),
            ack_data.get('ack_time', ack_data.get('time', datetime.now().isoformat())),
            ack_data.get('action_taken', 'Acknowledged'),
            ack_data.get('notes', ''),
            ack_data.get('response_time', 0),
            alarm_data.get('predicted_type', ack_data.get('alarm_type', 'Unknown')),
            str(alarm_data.get('asset_id', 'Unknown')),
            alarm_data.get('priority', 'CRITICAL'),
            ack_data.get('method', 'dashboard')
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB save error: {e}")
        return False

def load_acknowledgments():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM acknowledgments')
        rows = cursor.fetchall()
        conn.close()
        acks = {}
        for row in rows:
            acks[row[0]] = {
                'technician': row[1],
                'ack_time': row[2],
                'action_taken': row[3],
                'notes': row[4],
                'response_time': row[5],
                'alarm_type': row[6],
                'turbine_id': row[7],
                'priority': row[8],
                'method': row[9]
            }
        return acks
    except Exception as e:
        print(f"DB load error: {e}")
        return {}

def log_alarm(alarm_data):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO alarm_log
            (alarm_id, alarm_type, turbine_id, priority, confidence, detected_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            alarm_data.get('alarm_id'),
            alarm_data.get('predicted_type'),
            str(alarm_data.get('asset_id')),
            alarm_data.get('priority'),
            alarm_data.get('confidence'),
            alarm_data.get('timestamp', datetime.now().isoformat())
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB log error: {e}")
        return False

def log_notification(alarm_id, alarm_type, recipient_name, recipient_email, notif_type, status):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO notification_log
            (alarm_id, alarm_type, recipient_name, recipient_email,
             notification_type, sent_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            alarm_id, alarm_type, recipient_name, recipient_email,
            notif_type, datetime.now().isoformat(), status
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB notification log error: {e}")
        return False

def get_alarm_stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        stats = {}
        cursor.execute('SELECT COUNT(*) FROM alarm_log')
        stats['total_alarms'] = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM acknowledgments')
        stats['total_acknowledged'] = cursor.fetchone()[0]
        cursor.execute('SELECT AVG(response_time_min) FROM acknowledgments WHERE method = "dashboard"')
        result = cursor.fetchone()[0]
        stats['avg_response_time'] = round(result, 1) if result else 0
        cursor.execute('SELECT priority, COUNT(*) FROM alarm_log GROUP BY priority')
        stats['by_priority'] = dict(cursor.fetchall())
        conn.close()
        return stats
    except Exception as e:
        print(f"DB stats error: {e}")
        return {}

# Auto-initialize on import
init_db()