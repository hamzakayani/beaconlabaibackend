import html
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from app.core.logging_config import setup_logging

logger = setup_logging()
def get_admin_notification_emails() -> list[str]:
    """
    Parse ADMIN_NOTIFICATION_EMAIL from .env and return a clean list of emails
    """
    if not settings.ADMIN_NOTIFICATION_EMAIL:
        return []

    return [
        email.strip()
        for email in settings.ADMIN_NOTIFICATION_EMAIL.split(",")
        if email.strip()
    ]

def send_email_notification(
    to_email: str | list[str],
    subject: str,
    body: str,
    is_html: bool = False
) -> bool:
    """
    Send email notification using SMTP

    Args:
        to_email: Recipient email address or list of addresses
        subject: Email subject
        body: Email body content
        is_html: Whether body is HTML format

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    recipients = [to_email] if isinstance(to_email, str) else to_email
    if not recipients:
        return False

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.SMTP_USERNAME
        msg['To'] = ", ".join(recipients)

        # Add body to email
        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        # Create SMTP session
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()  # Enable security
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USERNAME, recipients, msg.as_string())

        logger.info(f"Email sent successfully to {recipients}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {recipients}: {str(e)}")
        return False

# def send_contact_inquiry_notification(
#     first_name: str,
#     last_name: str,
#     email: str,
#     phone_number: str,
#     subject: str,
#     message: str
# ) -> bool:
#     """
#     Send notification email to admin when a new contact inquiry is submitted
    
#     Args:
#         first_name: Contact's first name
#         last_name: Contact's last name
#         email: Contact's email
#         phone_number: Contact's phone number
#         subject: Inquiry subject
#         message: Inquiry message
    
#     Returns:
#         bool: True if email sent successfully, False otherwise
#     """
#     admin_emails = get_admin_notification_emails()
#     # Check if admin notification email is configured
#     if not admin_emails:
#         logger.warning(
#             "ADMIN_NOTIFICATION_EMAIL not configured. Skipping email notification."
#         )
#         return False
    
#     email_subject = f"Beacon Lab AI Inquiry: {subject}"
    
#     email_body = f""" 
# CONTACT DETAILS:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Name: {first_name} {last_name}
# Email: {email}
# Phone: {phone_number}
# Subject: {subject}

# MESSAGE:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# {message}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# This is an automated notification from Beacon Lab AI Backend.
# Please log in to the admin panel to view and manage this inquiry.
# """
    
#     return send_email_notification(
#         to_email=admin_emails,
#         subject=email_subject,
#         body=email_body,
#         is_html=False
#     )

def send_contact_inquiry_notification(
    first_name: str,
    last_name: str,
    email: str,
    phone_number: str,
    subject: str,
    message: str
) -> bool:
    admin_emails = get_admin_notification_emails()
 
    if not admin_emails:
        logger.warning(
            "ADMIN_NOTIFICATION_EMAIL not configured. Skipping email notification."
        )
        return False
 
    email_subject = f"Beacon Lab AI Inquiry: {subject}"
 
    email_body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>New Contact Inquiry</title>
</head>
<body style="margin:0; padding:0; background-color:#f4f6f8; font-family:Arial, Helvetica, sans-serif;">
 
<table width="100%" cellpadding="0" cellspacing="0" style="padding:24px;">
  <tr>
    <td align="center">
 
      <!-- Card -->
      <table width="600" cellpadding="0" cellspacing="0"
        style="background:#ffffff; border-radius:14px; overflow:hidden;
               box-shadow:0 8px 24px rgba(0,0,0,0.12);">
 
        <!-- Header -->
        <tr>
          <td style="background:#0b0b0b; padding:28px;">
            <table width="100%">
              <tr>
                <td>
                  <span style="font-size:22px; font-weight:700; color:#ffffff;">BEACON</span>
                  <span style="color:#ffffff80; margin:0 6px;">|</span>
                  <span style="font-size:22px; font-weight:700; color:#ffffff;">RIAZ LAB</span>
                  <div style="margin-top:6px; font-size:11px; letter-spacing:2px; color:#ffffff99;">
                    EVIDENCE SYNTHESIS
                  </div>
                </td>
                <td align="right">
                  <div style="width:44px; height:44px; background:#2563eb; border-radius:50%;
                              color:#ffffff; text-align:center; line-height:44px;
                              font-size:18px;">
                    ✉
                  </div>
                </td>
              </tr>
            </table>
          </td>
        </tr>
 
        <!-- Accent Bar -->
        <tr>
          <td style="height:4px; background:#2563eb;"></td>
        </tr>
 
        <!-- Title -->
        <tr>
          <td style="padding:26px;">
            <h2 style="margin:0; font-size:20px; color:#111827;">
              New Contact Inquiry
            </h2>
            <p style="margin:6px 0 0; font-size:13px; color:#6b7280;">
              Received automatically from Beacon Lab AI
            </p>
          </td>
        </tr>
 
        <!-- Contact Info -->
        <tr>
          <td style="padding:0 26px 20px;">
            <h3 style="font-size:12px; letter-spacing:1px; color:#6b7280; margin-bottom:14px;">
              CONTACT INFORMATION
            </h3>
 
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="padding:10px 0; color:#6b7280; width:140px;">Full Name</td>
                <td style="font-weight:600;">{first_name} {last_name}</td>
              </tr>
              <tr>
                <td style="padding:10px 0; color:#6b7280;">Email</td>
                <td>
                  <a href="mailto:{email}" style="color:#2563eb; text-decoration:none;">
                    {email}
                  </a>
                </td>
              </tr>
              <tr>
                <td style="padding:10px 0; color:#6b7280;">Phone</td>
                <td>{phone_number}</td>
              </tr>
              <tr>
                <td style="padding:10px 0; color:#6b7280;">Subject</td>
                <td>{subject}</td>
              </tr>
            </table>
          </td>
        </tr>
 
        <!-- Message -->
        <tr>
          <td style="padding:0 26px 26px;">
            <h3 style="font-size:12px; letter-spacing:1px; color:#6b7280; margin-bottom:10px;">
              MESSAGE CONTENT
            </h3>
            <div style="background:#f3f4f6; border:1px solid #e5e7eb;
                        border-radius:10px; padding:18px; color:#111827;
                        white-space:pre-wrap; line-height:1.6;">
              {message}
            </div>
          </td>
        </tr>
 
        <!-- CTA -->
        <tr>
          <td style="padding:0 26px 26px;">
            <a href="https://www.beaconlab.ai/admin/dashboard"
               style="display:block; background:#2563eb; color:#ffffff;
                      text-align:center; text-decoration:none;
                      padding:14px; border-radius:10px;
                      font-weight:600;">
              View in Admin Panel →
            </a>
          </td>
        </tr>
 
        <!-- Footer -->
        <tr>
          <td style="background:#0b0b0b; padding:18px;">
            <table width="100%">
              <tr>
                <td style="font-size:11px; color:#ffffff80;">
                  Automated notification from Beacon Lab AI<br>
                  © 2026 Beacon | Riaz Lab
                </td>
                <td align="right" style="font-size:11px; color:#10b981;">
                  ● System Active
                </td>
              </tr>
            </table>
          </td>
        </tr>
 
      </table>
 
    </td>
  </tr>
</table>
 
</body>
</html>
"""
 
    return send_email_notification(
        to_email=admin_emails,
        subject=email_subject,
        body=email_body,
        is_html=True
    )


def send_job_application_notification(
    job_title: str,
    full_name: str,
    email: str,
    phone: str | None,
    cover_letter: str | None,
    cv_filename: str,
) -> bool:
    """
    Send notification email to admin when someone applies for a job.
    """
    admin_emails = get_admin_notification_emails()
    if not admin_emails:
        logger.warning(
            "ADMIN_NOTIFICATION_EMAIL not configured. Skipping job application email notification."
        )
        return False

    phone_display = phone or "Not provided"
    cover_display = (cover_letter or "Not provided").strip()
    cover_display = html.escape(cover_display).replace("\n", "<br>")

    email_subject = f"New Job Application: {job_title} – {full_name}"

    email_body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>New Job Application</title>
</head>
<body style="margin:0; padding:0; background-color:#f4f6f8; font-family:Arial, Helvetica, sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="padding:24px;">
  <tr>
    <td align="center">

      <!-- Card -->
      <table width="600" cellpadding="0" cellspacing="0"
        style="background:#ffffff; border-radius:14px; overflow:hidden;
               box-shadow:0 8px 24px rgba(0,0,0,0.12);">

        <!-- Header -->
        <tr>
          <td style="background:#0b0b0b; padding:28px;">
            <table width="100%">
              <tr>
                <td>
                  <span style="font-size:22px; font-weight:700; color:#ffffff;">BEACON</span>
                  <span style="color:#ffffff80; margin:0 6px;">|</span>
                  <span style="font-size:22px; font-weight:700; color:#ffffff;">RIAZ LAB</span>
                  <div style="margin-top:6px; font-size:11px; letter-spacing:2px; color:#ffffff99;">
                    EVIDENCE SYNTHESIS
                  </div>
                </td>
                <td align="right">
                  <div style="width:44px; height:44px; background:#2563eb; border-radius:50%;
                              color:#ffffff; text-align:center; line-height:44px;
                              font-size:18px;">
                    ✉
                  </div>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Accent Bar -->
        <tr>
          <td style="height:4px; background:#2563eb;"></td>
        </tr>

        <!-- Title -->
        <tr>
          <td style="padding:26px;">
            <h2 style="margin:0; font-size:20px; color:#111827;">
              New Job Application
            </h2>
            <p style="margin:6px 0 0; font-size:13px; color:#6b7280;">
              {html.escape(job_title)} – received from Beacon Lab AI
            </p>
          </td>
        </tr>

        <!-- Applicant Info -->
        <tr>
          <td style="padding:0 26px 20px;">
            <h3 style="font-size:12px; letter-spacing:1px; color:#6b7280; margin-bottom:14px;">
              APPLICANT INFORMATION
            </h3>

            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="padding:10px 0; color:#6b7280; width:140px;">Full Name</td>
                <td style="font-weight:600;">{html.escape(full_name)}</td>
              </tr>
              <tr>
                <td style="padding:10px 0; color:#6b7280;">Email</td>
                <td>
                  <a href="mailto:{html.escape(email)}" style="color:#2563eb; text-decoration:none;">
                    {html.escape(email)}
                  </a>
                </td>
              </tr>
              <tr>
                <td style="padding:10px 0; color:#6b7280;">Phone</td>
                <td>{html.escape(phone_display)}</td>
              </tr>
              <tr>
                <td style="padding:10px 0; color:#6b7280;">CV file</td>
                <td>{html.escape(cv_filename)}</td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Cover Letter -->
        <tr>
          <td style="padding:0 26px 26px;">
            <h3 style="font-size:12px; letter-spacing:1px; color:#6b7280; margin-bottom:10px;">
              COVER LETTER
            </h3>
            <div style="background:#f3f4f6; border:1px solid #e5e7eb;
                        border-radius:10px; padding:18px; color:#111827;
                        line-height:1.6;">
              {cover_display}
            </div>
          </td>
        </tr>

        <!-- CTA -->
        <tr>
          <td style="padding:0 26px 26px;">
            <a href="https://www.beaconlab.ai/admin/dashboard"
               style="display:block; background:#2563eb; color:#ffffff;
                      text-align:center; text-decoration:none;
                      padding:14px; border-radius:10px;
                      font-weight:600;">
              View in Admin Panel →
            </a>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#0b0b0b; padding:18px;">
            <table width="100%">
              <tr>
                <td style="font-size:11px; color:#ffffff80;">
                  Automated notification from Beacon Lab AI<br>
                  © 2026 Beacon | Riaz Lab
                </td>
                <td align="right" style="font-size:11px; color:#10b981;">
                  ● System Active
                </td>
              </tr>
            </table>
          </td>
        </tr>

      </table>

    </td>
  </tr>
</table>

</body>
</html>
"""

    return send_email_notification(
        to_email=admin_emails,
        subject=email_subject,
        body=email_body,
        is_html=True
    )

