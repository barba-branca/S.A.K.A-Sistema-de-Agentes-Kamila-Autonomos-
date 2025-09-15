import os
import logging
from twilio.rest import Client

logger = logging.getLogger(__name__)

def send_whatsapp_message(body: str, to: str = None):
    """
    Envia uma mensagem de WhatsApp usando o Twilio.
    Caso as credenciais não estejam configuradas, exibe a mensagem no log.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
    recipient_phone_number = to or os.getenv("RECIPIENT_PHONE_NUMBER")

    if not all([account_sid, auth_token, twilio_phone_number, recipient_phone_number]):
        logger.info("---- SIMULAÇÃO DE WHATSAPP ----")
        logger.info(f"Para: {recipient_phone_number or 'Não configurado'}")
        logger.info(f"Corpo: {body}")
        logger.info("-----------------------------")
        logger.warning("Variáveis de ambiente do Twilio não configuradas. Exibindo no console.")
        return

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=body,
            from_=f'whatsapp:{twilio_phone_number}',
            to=f'whatsapp:{recipient_phone_number}'
        )
        logger.info(f"Mensagem de WhatsApp enviada com sucesso para {recipient_phone_number}. SID: {message.sid}")
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem de WhatsApp: {e}")
