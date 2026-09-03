"""Zoho Mail integration for customer communication"""

from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from gaiafaac_api.config import get_settings


@dataclass
class EmailMessage:
    """Email message structure"""

    to: str
    subject: str
    body_html: str
    body_text: str | None = None
    from_email: str = "gaiaassist@gailabai.com"
    reply_to: str | None = None
    cc: list[str] | None = None
    bcc: list[str] | None = None


class ZohoEmailService:
    """Send emails via Zoho Mail"""

    # Zoho Mail SMTP configuration
    SMTP_HOST = "smtp.zoho.com"
    SMTP_PORT = 587

    def __init__(
        self,
        sender_email: str = "",
        sender_password: str = "",
    ):
        settings = get_settings()
        self.sender_email = sender_email or settings.zoho_sender_email or "gaiaassist@gailabai.com"
        self.sender_password = sender_password or settings.zoho_sender_password

        if not self.sender_password:
            print("⚠️  Warning: ZOHO_SENDER_PASSWORD not configured")
            print("   Set it in environment or .env file")

    def send_email(self, message: EmailMessage) -> bool:
        """Send email via Zoho SMTP"""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject
            msg["From"] = message.from_email
            msg["To"] = message.to

            if message.cc:
                msg["Cc"] = ", ".join(message.cc)
            if message.reply_to:
                msg["Reply-To"] = message.reply_to

            # Attach text version
            if message.body_text:
                msg.attach(MIMEText(message.body_text, "plain"))

            # Attach HTML version (preferred)
            msg.attach(MIMEText(message.body_html, "html"))

            # Send via Zoho SMTP
            with smtplib.SMTP(self.SMTP_HOST, self.SMTP_PORT) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)

                recipients = [message.to]
                if message.cc:
                    recipients.extend(message.cc)
                if message.bcc:
                    recipients.extend(message.bcc)

                server.sendmail(self.sender_email, recipients, msg.as_string())

            print(f"✅ Email sent to {message.to}")
            return True

        except smtplib.SMTPException as e:
            print(f"❌ SMTP Error: {e}")
            return False
        except Exception as e:
            print(f"❌ Email Error: {e}")
            return False


# Email template builders
def build_subscription_confirmation_email(
    customer_name: str,
    tier_name: str,
    amount_naira: int,
    start_date: str,
) -> EmailMessage:
    """Build subscription confirmation email"""
    body_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: #10b981;">Welcome to GaiaFAAC Intelligence, {customer_name}!</h2>

                <p>Your <strong>{tier_name}</strong> subscription is now active.</p>

                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>Subscription Details</h3>
                    <p><strong>Tier:</strong> {tier_name}</p>
                    <p><strong>Amount:</strong> ₦{amount_naira:,}/month</p>
                    <p><strong>Start Date:</strong> {start_date}</p>
                </div>

                <h3>Next Steps</h3>
                <ol>
                    <li>Visit your <a href="https://gaiafaac.app/dashboard">dashboard</a></li>
                    <li>Create your first watchlist</li>
                    <li>Configure alerts for fiscal changes</li>
                    <li>Generate Decision Packets</li>
                </ol>

                <p>Questions? Contact us at <a href="mailto:gaiaassist@gailabai.com">gaiaassist@gailabai.com</a></p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                <p style="color: #6b7280; font-size: 12px;">
                    GaiaFAAC Intelligence | Verified fiscal intelligence for Nigeria<br>
                    <a href="https://gaiafaac.app">gaiafaac.app</a>
                </p>
            </div>
        </body>
    </html>
    """

    body_text = f"""
Welcome to GaiaFAAC Intelligence, {customer_name}!

Your {tier_name} subscription is now active.

SUBSCRIPTION DETAILS
Tier: {tier_name}
Amount: ₦{amount_naira:,}/month
Start Date: {start_date}

NEXT STEPS
1. Visit your dashboard: https://gaiafaac.app/dashboard
2. Create your first watchlist
3. Configure alerts for fiscal changes
4. Generate Decision Packets

Questions? Contact us at gaiaassist@gailabai.com

---
GaiaFAAC Intelligence | Verified fiscal intelligence for Nigeria
https://gaiafaac.app
    """

    return EmailMessage(
        to="",  # Will be set by caller
        subject=f"Welcome! Your {tier_name} subscription is active",
        body_html=body_html,
        body_text=body_text,
        from_email="gaiaassist@gailabai.com",
    )


def build_payment_receipt_email(
    customer_name: str,
    amount_naira: int,
    invoice_number: str,
    transaction_date: str,
) -> EmailMessage:
    """Build payment receipt email"""
    body_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: #10b981;">Payment Receipt</h2>

                <p>Hi {customer_name},</p>
                <p>Thank you for your payment. Here's your receipt:</p>

                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Invoice Number:</strong> {invoice_number}</p>
                    <p><strong>Amount:</strong> ₦{amount_naira:,}</p>
                    <p><strong>Date:</strong> {transaction_date}</p>
                    <p><strong>Status:</strong> ✅ Paid</p>
                </div>

                <p>Your subscription is active and you can access all features immediately.</p>

                <p>Questions? Contact us at <a href="mailto:gaiaassist@gailabai.com">gaiaassist@gailabai.com</a></p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                <p style="color: #6b7280; font-size: 12px;">
                    GaiaFAAC Intelligence | Verified fiscal intelligence for Nigeria
                </p>
            </div>
        </body>
    </html>
    """

    return EmailMessage(
        to="",  # Will be set by caller
        subject=f"Payment Receipt - Invoice {invoice_number}",
        body_html=body_html,
        from_email="gaiaassist@gailabai.com",
    )


def build_review_notification_email(
    reviewer_name: str,
    source_type: str,
    source_id: str,
    jurisdiction: str,
) -> EmailMessage:
    """Build review queue notification (for review@ailabai.com)"""
    body_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: #3b82f6;">New {source_type} Source Waiting for Review</h2>

                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Source Type:</strong> {source_type}</p>
                    <p><strong>Jurisdiction:</strong> {jurisdiction}</p>
                    <p><strong>Source ID:</strong> {source_id}</p>
                </div>

                <p>
                    <a href="https://gaiafaac.app/review/{source_type.lower()}/{source_id}"
                       style="background-color: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">
                        Review Now
                    </a>
                </p>

                <p style="color: #6b7280; font-size: 12px; margin-top: 20px;">
                    This is an automated notification for the GaiaFAAC review queue.
                </p>
            </div>
        </body>
    </html>
    """

    return EmailMessage(
        to="review@ailabai.com",
        subject=f"Review Required: {source_type} - {jurisdiction}",
        body_html=body_html,
        from_email="gaiaassist@gailabai.com",
        reply_to="gaiaassist@gailabai.com",
    )


# Singleton instance
_email_service: ZohoEmailService | None = None


def get_email_service() -> ZohoEmailService:
    """Get or create email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = ZohoEmailService()
    return _email_service
