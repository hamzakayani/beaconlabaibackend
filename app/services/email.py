import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from app.core.logging_config import setup_logging

logger = setup_logging()

def send_email_notification(
    to_email: str,
    subject: str,
    body: str,
    is_html: bool = False
) -> bool:
    """
    Send email notification using SMTP
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        is_html: Whether body is HTML format
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.SMTP_USERNAME
        msg['To'] = to_email

        # Add body to email
        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        # Create SMTP session
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()  # Enable security
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

def send_contact_inquiry_notification(
    first_name: str,
    last_name: str,
    email: str,
    phone_number: str,
    subject: str,
    message: str
) -> bool:
    """
    Send notification email to admin when a new contact inquiry is submitted
    
    Args:
        first_name: Contact's first name
        last_name: Contact's last name
        email: Contact's email
        phone_number: Contact's phone number
        subject: Inquiry subject
        message: Inquiry message
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Check if admin notification email is configured
    if not settings.ADMIN_NOTIFICATION_EMAIL or settings.ADMIN_NOTIFICATION_EMAIL.strip() == "":
        logger.warning("ADMIN_NOTIFICATION_EMAIL not configured. Skipping email notification.")
        return False
    
    email_subject = f"New Contact Inquiry: {subject}"
    
    email_body = f"""New Contact Inquiry Received

A new contact inquiry has been submitted through the website contact form.

CONTACT DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name: {first_name} {last_name}
Email: {email}
Phone: {phone_number}
Subject: {subject}

MESSAGE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{message}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated notification from Beacon Lab AI Backend.
Please log in to the admin panel to view and manage this inquiry.
"""
    
    return send_email_notification(
        to_email=settings.ADMIN_NOTIFICATION_EMAIL,
        subject=email_subject,
        body=email_body,
        is_html=False
    )

