import os
import logging
from twilio.rest import Client

logger = logging.getLogger(__name__)

def send_whatsapp_message(body: str, to: str = None):
    """
    Sends a WhatsApp message using Twilio.
    Falls back to logging the message if credentials are not configured.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
    recipient_phone_number = to or os.getenv("RECIPIENT_PHONE_NUMBER")

    if not all([account_sid, auth_token, twilio_phone_number, recipient_phone_number]):
        logger.info("---- WHATSAPP SIMULATION ----")
        logger.info(f"To: {recipient_phone_number or 'Not configured'}")
        logger.info(f"Body: {body}")
        logger.info("-----------------------------")
        logger.warning("Twilio environment variables not fully configured. Logging to console instead.")
        return

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=body,
            from_=f'whatsapp:{twilio_phone_number}',
            to=f'whatsapp:{recipient_phone_number}'
        )
        logger.info(f"WhatsApp message sent successfully to {recipient_phone_number}. SID: {message.sid}")
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
