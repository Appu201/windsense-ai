# utils/sms_sender.py — Twilio WhatsApp Sandbox alerts
from twilio.rest import Client

ACCOUNT_SID = "ACebe3c710683e01ebfd414dde9aec3b98"   # paste from twilio.com/console
AUTH_TOKEN = "b1a7f277c4e926c05a1155b949dd5a3f"      # paste from twilio.com/console

client = Client(ACCOUNT_SID, AUTH_TOKEN)

TEAM_NUMBERS = [
    "9284743112",  # Aparajithaa
    "9123516325",  # Aarif
    "8778838055",  # Divya
]

def send_whatsapp(phone, message):
    """Send a WhatsApp message to one number via Twilio Sandbox."""
    try:
        msg = client.messages.create(
            body=message,
            from_='whatsapp:+14155238886',
            to='whatsapp:+91' + phone
        )
        return True, msg.sid
    except Exception as e:
        return False, str(e)

def send_alert_to_all(message):
    """Send alert to all team members. Returns list of (number, success, response)."""
    results = []
    for num in TEAM_NUMBERS:
        status, response = send_whatsapp(num, message)
        results.append((num, status, response))
    return results

def send_real_sms(to_number, message_body):
    """
    Drop-in replacement for the old send_real_sms function.
    Sends via WhatsApp instead of SMS.
    to_number format: +919284743112 or 9284743112
    """
    try:
        number = to_number.strip()
        if number.startswith('+91'):
            number = number[3:]
        elif number.startswith('91') and len(number) == 12:
            number = number[2:]

        success, response = send_whatsapp(number, message_body)
        return success, response
    except Exception as e:
        return False, str(e)
