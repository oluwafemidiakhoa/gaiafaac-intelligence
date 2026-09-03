"""Billing service for usage tracking, invoicing, and revenue management"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.subscription_models import (
    BillingEvent,
    Invoice,
    OrganizationSubscription,
    SubscriptionTier,
    UsageLog,
)


class BillingService:
    """Manage subscriptions, usage tracking, and revenue"""

    def __init__(self, session: Session):
        self.session = session

    def log_usage(
        self,
        organization_id: uuid.UUID,
        subscription_id: uuid.UUID,
        event_type: str,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        response_status: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> UsageLog:
        """Log API usage for billing purposes"""
        log = UsageLog(
            organization_id=organization_id,
            subscription_id=subscription_id,
            event_type=event_type,
            endpoint=endpoint,
            method=method,
            response_status=response_status,
            user_id=user_id,
        )
        self.session.add(log)
        self.session.commit()
        return log

    def create_billing_event(
        self,
        organization_id: uuid.UUID,
        subscription_id: uuid.UUID,
        event_type: str,
        amount_naira: Decimal,
        description: Optional[str] = None,
    ) -> BillingEvent:
        """Create a billing event (subscription charge, overage, etc.)"""
        event = BillingEvent(
            organization_id=organization_id,
            subscription_id=subscription_id,
            event_type=event_type,
            description=description,
            amount_naira=amount_naira,
        )
        self.session.add(event)
        self.session.commit()
        return event

    def generate_invoice(
        self,
        organization_id: uuid.UUID,
        subscription_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime,
        billing_events: list[BillingEvent],
    ) -> Invoice:
        """Generate an invoice from billing events"""
        # Calculate totals
        subtotal = sum(Decimal(str(event.amount_naira)) for event in billing_events)
        tax = subtotal * Decimal("0.075")  # 7.5% VAT in Nigeria
        total = subtotal + tax

        # Generate invoice number: INV-YYYYMMDD-ORGID
        invoice_number = f"INV-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(organization_id)[:8].upper()}"

        # Build line items
        line_items = [
            {
                "description": event.description or event.event_type,
                "amount": str(event.amount_naira),
            }
            for event in billing_events
        ]

        invoice = Invoice(
            organization_id=organization_id,
            subscription_id=subscription_id,
            invoice_number=invoice_number,
            subtotal_naira=subtotal,
            tax_naira=tax,
            total_naira=total,
            period_start=period_start,
            period_end=period_end,
            due_date=datetime.now(timezone.utc) + timedelta(days=30),
            status="draft",
            line_items=str(line_items),
        )

        self.session.add(invoice)

        # Mark events as invoiced
        for event in billing_events:
            event.is_invoiced = True
            event.invoice_id = invoice.id

        self.session.commit()
        return invoice

    def get_monthly_usage(
        self, organization_id: uuid.UUID, month: Optional[int] = None, year: Optional[int] = None
    ) -> dict:
        """Get usage metrics for a specific month"""
        now = datetime.now(timezone.utc)
        if month is None:
            month = now.month
        if year is None:
            year = now.year

        # Get logs for the month
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

        logs = (
            self.session.execute(
                select(UsageLog)
                .where(
                    UsageLog.organization_id == organization_id,
                    UsageLog.created_at >= start,
                    UsageLog.created_at < end,
                )
                .order_by(UsageLog.event_type)
            )
            .scalars()
            .all()
        )

        # Aggregate by event type
        usage_by_type = {}
        for log in logs:
            usage_by_type[log.event_type] = usage_by_type.get(log.event_type, 0) + 1

        return {
            "organization_id": organization_id,
            "period": f"{year}-{month:02d}",
            "total_events": len(logs),
            "by_type": usage_by_type,
            "logs": logs,
        }

    def check_usage_limits(
        self,
        organization_id: uuid.UUID,
        subscription: OrganizationSubscription,
        tier: SubscriptionTier,
    ) -> dict:
        """Check if organization has exceeded usage limits"""
        # Get this month's usage
        usage = self.get_monthly_usage(organization_id)

        api_calls = usage["by_type"].get("api_call", 0)
        exports = usage["by_type"].get("export", 0)

        return {
            "organization_id": organization_id,
            "api_calls": {
                "used": api_calls,
                "limit": tier.requests_per_month,
                "exceeded": api_calls > tier.requests_per_month,
                "overage": max(0, api_calls - tier.requests_per_month),
            },
            "exports": {
                "used": exports,
                "limit": tier.exports_per_month,
                "exceeded": exports > tier.exports_per_month,
                "overage": max(0, exports - tier.exports_per_month),
            },
        }

    def calculate_overage_charges(self, api_overage: int, export_overage: int) -> Decimal:
        """Calculate charges for usage overages"""
        # Pricing: ₦50 per extra API call, ₦5,000 per extra export
        api_cost = Decimal(str(api_overage)) * Decimal("50")
        export_cost = Decimal(str(export_overage)) * Decimal("5000")
        return api_cost + export_cost

    def send_invoice_email(self, invoice: Invoice, email: str) -> bool:
        """Send invoice to customer (integrates with Zoho Mail)"""
        from gaiafaac_api.services.zoho_email import get_email_service
        from gaiafaac_api.services.zoho_email import EmailMessage

        email_service = get_email_service()

        # Build invoice email
        body_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Invoice {invoice.invoice_number}</h2>
                <p>Invoice Date: {invoice.created_at.strftime("%Y-%m-%d")}</p>
                <p>Due Date: {invoice.due_date.strftime("%Y-%m-%d")}</p>

                <h3>Billing Period: {invoice.period_start.strftime("%Y-%m-%d")} to {invoice.period_end.strftime("%Y-%m-%d")}</h3>

                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="border-bottom: 1px solid #ccc;">
                        <th>Description</th>
                        <th style="text-align: right;">Amount (₦)</th>
                    </tr>
                    <tr>
                        <td>Subscription</td>
                        <td style="text-align: right;">₦{invoice.subtotal_naira:,.2f}</td>
                    </tr>
                    <tr style="border-bottom: 2px solid #ccc;">
                        <td>Tax (7.5%)</td>
                        <td style="text-align: right;">₦{invoice.tax_naira:,.2f}</td>
                    </tr>
                    <tr style="font-weight: bold; font-size: 16px;">
                        <td>Total</td>
                        <td style="text-align: right;">₦{invoice.total_naira:,.2f}</td>
                    </tr>
                </table>

                <p>
                    <a href="https://gaiafaac.app/dashboard/invoices/{invoice.id}" style="
                        background-color: #10b981;
                        color: white;
                        padding: 10px 20px;
                        text-decoration: none;
                        border-radius: 4px;
                        display: inline-block;
                    ">Pay Invoice</a>
                </p>
            </body>
        </html>
        """

        message = EmailMessage(
            to=email,
            subject=f"Invoice {invoice.invoice_number} - GaiaFAAC Intelligence",
            body_html=body_html,
        )

        success = email_service.send_email(message)
        if success:
            invoice.sent_at = datetime.now(timezone.utc)
            self.session.commit()

        return success
