
import logging

# Configure a dedicated logger for this service
logger = logging.getLogger(__name__)

def send_email(recipient: str, subject: str, body: str):
    """
    Simulates sending an email notification.
    In a real system, this would integrate with a service like SendGrid, AWS SES, etc.
    """
    message = f"\n--- SIMULATING EMAIL NOTIFICATION ---\
Recipient: {recipient}\nSubject: {subject}\nBody: {body}\n--- END OF EMAIL SIMULATION ---"
    logger.info(message)
    print(message) # Also print for immediate visibility during development

def send_sms(phone_number: str, message: str):
    """
    Simulates sending an SMS notification.
    In a real system, this would integrate with a service like Twilio.
    """
    sms_message = f"\n--- SIMULATING SMS NOTIFICATION ---\
To: {phone_number}\nMessage: {message}\n--- END OF SMS SIMULATION ---"
    logger.info(sms_message)
    print(sms_message)

def send_whatsapp(user_id: str, message: str):
    """
    Simulates sending a WhatsApp notification.
    In a real system, this would integrate with the WhatsApp Business API (e.g., via Twilio).
    """
    wa_message = f"\n--- SIMULATING WHATSAPP NOTIFICATION ---\
To User ID: {user_id}\nMessage: {message}\n--- END OF WHATSAPP SIMULATION ---"
    logger.info(wa_message)
    print(wa_message)
