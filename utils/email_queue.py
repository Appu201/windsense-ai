import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

QUEUE_FILE = os.path.join(os.path.dirname(os.path.abspath('app.py')), 'data', 'email_queue.json')

def load_queue():
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_queue(queue):
    try:
        with open(QUEUE_FILE, 'w') as f:
            json.dump(queue, f, indent=2)
    except Exception as e:
        print(f"[QUEUE] Failed to save queue: {e}")

def add_to_queue(recipient_email, recipient_name, subject, body_html, alarm_id):
    """Add a failed email to the retry queue"""
    queue = load_queue()
    queue.append({
        'recipient_email': recipient_email,
        'recipient_name': recipient_name,
        'subject': subject,
        'body_html': body_html,
        'alarm_id': alarm_id,
        'queued_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'attempts': 0
    })
    save_queue(queue)
    print(f"[QUEUE] Email to {recipient_name} queued for retry")

def flush_queue():
    """
    Try to send all queued emails.
    Call this on every page load — it's fast if queue is empty.
    Returns (sent_count, failed_count).
    """
    queue = load_queue()
    if not queue:
        return 0, 0

    remaining = []
    sent_count = 0
    failed_count = 0

    for item in queue:
        try:
            msg = MIMEMultipart()
            msg['From'] = 'windsenseada@gmail.com'
            msg['To'] = item['recipient_email']
            msg['Subject'] = item['subject']
            msg.attach(MIMEText(item['body_html'], 'html'))

            _smtp = smtplib.SMTP('smtp.gmail.com', 587, timeout=5)
            _smtp.ehlo()
            _smtp.starttls()
            _smtp.login('windsenseada@gmail.com', 'oaru xyta qlwi hpmw')
            _smtp.sendmail('windsenseada@gmail.com', item['recipient_email'], msg.as_string())
            _smtp.quit()

            print(f"[QUEUE] Flushed queued email to {item['recipient_name']}")
            sent_count += 1

        except Exception as e:
            item['attempts'] = item.get('attempts', 0) + 1
            # Drop after 10 failed attempts to avoid infinite queue
            if item['attempts'] < 10:
                remaining.append(item)
            else:
                print(f"[QUEUE] Dropped email to {item['recipient_name']} after 10 attempts")
            failed_count += 1

    save_queue(remaining)
    return sent_count, failed_count