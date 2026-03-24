import os

TWILIO_SID = "ACebe3c710683e01ebfd414dde9aec3b98"
TWILIO_AUTH = "b1a7f277c4e926c05a1155b949dd5a3f"
FROM_WA = "whatsapp:+14155238886"


def send_real_sms(to_number: str, message_body: str):
    """
    Send WhatsApp message via Twilio sandbox.
    Normalises the number, strips any accidental 'whatsapp:' prefix
    the caller may have already added, then sends.
    Returns (success: bool, message: str)
    """
    try:
        from twilio.rest import Client

        # --- normalise destination number ---
        clean_number = to_number.strip()
        if clean_number.lower().startswith("whatsapp:"):
            clean_number = clean_number[len("whatsapp:"):]
        to_wa = f"whatsapp:{clean_number}"

        client = Client(TWILIO_SID, TWILIO_AUTH)
        message = client.messages.create(
            body=message_body,
            from_=FROM_WA,
            to=to_wa,
        )
        return True, f"Sent: {message.sid}"

    except Exception as e:
        error_msg = str(e)

        if "63016" in error_msg:
            return (
                False,
                "Sandbox session expired — recipient must send "
                "'join fruit-salt' to +14155238886 on WhatsApp first.",
            )
        elif "21608" in error_msg:
            return False, "Number not verified for Twilio sandbox."
        elif "Trial account" in error_msg or "20003" in error_msg:
            return False, "Trial account limit — check Twilio console balance."
        elif "21211" in error_msg or "21614" in error_msg:
            return False, f"Invalid 'To' number format: {to_number}"
        else:
            return False, f"Twilio error: {error_msg}"