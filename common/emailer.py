from concurrent.futures import ThreadPoolExecutor
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from django.conf import settings

from common.decorators import log_time, safe
from common.progress_socket import send_progress_update

logger = logging.getLogger('contactmailer')

@safe
def send_single_email(recipient: str, subject: str, template: str, context: dict = None) -> bool:
    """
    Sends a single email using Python's smtplib.
    """
    if context is None:
        context = {}
    
    body = template.format(**context)
    
    msg = MIMEMultipart()
    msg['From'] = settings.DEFAULT_FROM_EMAIL
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        if settings.EMAIL_USE_TLS:
            server.starttls()
        if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            
        server.send_message(msg)
        server.quit()
        logger.info(f"Email successfully sent to {recipient}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {e}", exc_info=True)
        return False

@log_time
def send_bulk_emails(campaign_id: str, subject: str, body_template: str, recipients: list):
    """
    Sends emails concurrently using ThreadPoolExecutor.
    Updates the local progress socket server.
    recipients is a list of dictionaries, e.g. [{"email": "x@x.com", "name": "X"}]
    """
    total = len(recipients)
    sent = 0
    failed = 0
    
    send_progress_update(campaign_id, sent, failed, total)
    
    def process_recipient(recipient_data):
        nonlocal sent, failed
        email = recipient_data.get('email')
        success = send_single_email(email, subject, body_template, context=recipient_data)
        if success:
            sent += 1
        else:
            failed += 1
        send_progress_update(campaign_id, sent, failed, total)

    with ThreadPoolExecutor(max_workers=5) as executor:
        # submit all tasks
        futures = [executor.submit(process_recipient, r) for r in recipients]
        
    logger.info(f"Campaign {campaign_id} finished. Sent: {sent}, Failed: {failed}, Total: {total}")
