import os
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Configuração do logging
logger = logging.getLogger(__name__)

# Leitura das credenciais e números a partir das variáveis de ambiente
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")
USER_WHATSAPP_TO = os.getenv("USER_WHATSAPP_TO")

# Validação da configuração
if not all([ACCOUNT_SID, AUTH_TOKEN, WHATSAPP_FROM, USER_WHATSAPP_TO]):
    logger.warning("Credenciais da Twilio não configuradas. A função de relatório estará desativada.")
    client = None
else:
    # Verificação para não inicializar o cliente com placeholders
    if "YOUR_TWILIO" in ACCOUNT_SID or "YOUR_TWILIO" in AUTH_TOKEN:
        logger.warning("As credenciais da Twilio parecem ser placeholders. A função de relatório estará desativada.")
        client = None
    else:
        client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_whatsapp_report(message_body: str):
    """
    Envia uma mensagem de relatório para o número de WhatsApp do usuário.

    Args:
        message_body (str): O conteúdo da mensagem a ser enviada.

    Returns:
        bool: True se a mensagem foi enviada com sucesso, False caso contrário.
    """
    if not client:
        logger.error("Cliente Twilio não inicializado. Não é possível enviar o relatório.")
        return False

    try:
        logger.info(f"Enviando relatório via WhatsApp para {USER_WHATSAPP_TO}...")
        message = client.messages.create(
            from_=WHATSAPP_FROM,
            body=message_body,
            to=USER_WHATSAPP_TO
        )
        logger.info(f"Mensagem enviada com sucesso. SID: {message.sid}")
        return True
    except TwilioRestException as e:
        logger.error(f"Falha ao enviar mensagem via Twilio: {e}")
        return False
    except Exception as e:
        logger.error(f"Ocorreu um erro inesperado ao enviar o relatório: {e}")
        return False