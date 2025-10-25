import logging
import json
import requests
from dpath import get as dpath_get
from app.utils.playbook_utils import render_template

logger = logging.getLogger(__name__)

def _send_email(config, context):
    """Placeholder for sending an email."""
    to = render_template(config.get('to'), context)
    cc = render_template(config.get('cc'), context)
    subject = render_template(config.get('subject'), context)
    body = render_template(config.get('body_template'), context)
    
    logger.info("--- EMAIL NOTIFICATION (SIMULATED) ---")
    logger.info(f"To: {to}")
    logger.info(f"Cc: {cc}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Body: {body}")
    logger.info("--- END SIMULATION ---")
    # In a real implementation, you would use smtplib or a service like SendGrid here.
    # This would require SMTP configuration (host, port, user, pass) in your app's config.

def _send_sms_whatsapp(config, context, channel):
    """Placeholder for sending SMS or WhatsApp messages."""
    to_number = render_template(config.get('to_number'), context)
    message = render_template(config.get('message_template'), context)

    logger.info(f"--- {channel.upper()} NOTIFICATION (SIMULATED) ---")
    logger.info(f"To Number: {to_number}")
    logger.info(f"Message: {message}")
    logger.info("--- END SIMULATION ---")
    # In a real implementation, you would use a service like Twilio here.
    # This would require API keys and service IDs in your app's config.

def _call_api(config, context):
    """Makes a REST API call based on the playbook configuration."""
    url = render_template(config.get('url'), context)
    method = config.get('method', 'POST').upper()
    headers = render_template(config.get('headers', {}), context)
    body = render_template(config.get('body_template', {}), context)

    logger.info(f"--- API NOTIFICATION ---")
    logger.info(f"Method: {method}")
    logger.info(f"URL: {url}")
    logger.info(f"Headers: {headers}")
    logger.info(f"Body: {json.dumps(body)}")

    try:
        response = requests.request(
            method,
            url,
            headers=headers,
            json=body,
            timeout=15 # 15-second timeout
        )
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
        logger.info(f"API call successful. Status: {response.status_code}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API call failed: {e}", exc_info=True)
        # Re-raise the exception so the playbook worker can handle it based on the step's failure policy.
        raise


def dispatch_notification(channel, config, context):
    """Dispatches the notification to the correct handler."""
    if channel == 'email':
        _send_email(config, context)
    elif channel in ['sms', 'whatsapp']:
        _send_sms_whatsapp(config, context, channel)
    elif channel == 'api':
        return _call_api(config, context) # Return the response for potential use in later steps
    else:
        logger.warning(f"Unknown notification channel '{channel}'.")