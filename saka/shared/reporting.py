import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# --- Configuração do Cliente Twilio ---
# As credenciais são carregadas a partir das variáveis de ambiente no .env
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
RECIPIENT_PHONE_NUMBER = os.getenv("RECIPIENT_PHONE_NUMBER")

# Validação das credenciais
if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, RECIPIENT_PHONE_NUMBER]):
    print("AVISO: Credenciais da Twilio não estão totalmente configuradas. A funcionalidade de relatório estará desativada.")
    twilio_client = None
else:
    try:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    except Exception as e:
        print(f"AVISO: Falha ao inicializar o cliente da Twilio: {e}")
        twilio_client = None


async def send_whatsapp_report(body: str):
    """
    Envia um relatório de texto via WhatsApp usando a API da Twilio.
    Esta função é `async` para ser compatível com as BackgroundTasks.

    Args:
        body (str): O corpo da mensagem a ser enviada.
    """
    if not twilio_client:
        print("Relatório não enviado: Cliente da Twilio não está disponível.")
        return

    try:
        message = twilio_client.messages.create(
            from_=TWILIO_PHONE_NUMBER,
            body=body,
            to=RECIPIENT_PHONE_NUMBER
        )
        print(f"Mensagem de relatório enviada com sucesso. SID: {message.sid}")
    except TwilioRestException as e:
        # Erros comuns incluem número de destino não verificado no sandbox da Twilio
        print(f"Erro ao enviar mensagem via Twilio: {e}")
    except Exception as e:
        print(f"Erro inesperado ao enviar relatório: {e}")