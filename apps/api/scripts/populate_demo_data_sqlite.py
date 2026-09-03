#!/usr/bin/env python3.12
"""Generate realistic fixture data using SQLite (for local testing without PostgreSQL)"""

import random
import sys
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from gaiafaac_api.database.base import Base
from gaiafaac_api.database.debt_models import DebtKind, StateDebtRecord
from gaiafaac_api.database.enums import ProcessingStatus, VerificationStatus
from gaiafaac_api.database.igr_models import IgrPeriodType, StateIgrRecord
from gaiafaac_api.database.models import State
from gaiafaac_api.database.subscription_models import (
    OrganizationSubscription,
    SubscriptionStatus,
    SubscriptionTier,
)


def main() -> None:
    """Main entry point"""
    print("\n" + "=" * 70)
    print("GaiaFAAC Intelligence - Demo Data Generator (SQLite)")
    print("=" * 70 + "\n")

    # Create SQLite database
    db_path = "/tmp/gaiafaac_demo.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", echo=False)

    # Create all tables
    Base.metadata.create_all(engine)
    print(f"✅ Created SQLite database at {db_path}\n")

    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as session:
        # Create subscription tiers
        print("💳 Creating subscription tiers...")
        tiers = [
            SubscriptionTier(
                id=uuid.uuid4(),
                name="Free",
                price_naira=0,
                requests_per_month=10000,
                exports_per_month=0,
                features="public_search,basic_export",
                description="For explorers & researchers",
            ),
            SubscriptionTier(
                id=uuid.uuid4(),
                name="Professional",
                price_naira=50000,
                requests_per_month=100000,
                exports_per_month=5,
                features="watchlists,alerts,api_access,csv_export",
                description="For institutions & analysts",
            ),
            SubscriptionTier(
                id=uuid.uuid4(),
                name="Enterprise",
                price_naira=500000,
                requests_per_month=999999,
                exports_per_month=999,
                features="all,custom_reports,webhooks,sla,dedicated_support",
                description="For banks, governments, APIs",
            ),
        ]
        session.add_all(tiers)
        session.commit()
        print(f"   ✅ Created {len(tiers)} subscription tiers\n")

        # Create dummy states (since we can't rely on existing data)
        print("🌍 Creating sample states...")
        state_names = [
            "Lagos",
            "Kano",
            "Katsina",
            "Oyo",
            "Rivers",
            "Bauchi",
            "Jigawa",
            "Delta",
            "Kebbi",
            "Borno",
            "Enugu",
            "Ebonyi",
            "Anambra",
            "Imo",
            "Abia",
            "Akwa Ibom",
            "Cross River",
            "Edo",
            "Ekiti",
            "Osun",
            "Ondo",
            "Ogun",
            "Kwara",
            "Niger",
            "Plateau",
            "Taraba",
            "Adamawa",
            "Gombe",
            "Yobe",
            "Zamfara",
            "Sokoto",
            "Nasarawa",
            "Kogi",
            "Kaduna",
            "Benue",
            "Abuja",
            "Bayelsa",
        ]

        states = []
        for state_name in state_names:
            state = State(
                state_id=uuid.uuid4(),
                name=state_name,
                slug=state_name.lower().replace(" ", "-"),
            )
            states.append(state)

        session.add_all(states)
        session.commit()
        print(f"   ✅ Created {len(states)} states\n")

        # Generate NBS IGR demo data
        print("📊 Generating NBS IGR demo data for 2024...")
        igr_count = 0
        for state in states:
            amount = Decimal(str(random.randint(500_000_000, 50_000_000_000)))
            record = StateIgrRecord(
                id=uuid.uuid4(),
                state_id=state.state_id,
                fiscal_year=2024,
                period_type=IgrPeriodType.FULL_YEAR,
                amount=amount,
                amount_original=f"₦{amount:,.0f}",
                source_organization="NBS (Demo - Not Verified)",
                source_url="https://www.nigerianstat.gov.ng (demo)",
                source_page=1,
                processing_status=ProcessingStatus.PUBLISHED,
                verification_status=VerificationStatus.DEMO,
                published_at=datetime.utcnow(),
            )
            session.add(record)
            igr_count += 1
        session.commit()
        print(f"   ✅ Created {igr_count} NBS IGR demo records\n")

        # Generate DMO debt demo data
        print("💳 Generating DMO domestic and external debt demo data...")
        debt_count = 0
        as_of_date = date(2024, 9, 1)
        for state in states:
            for kind in [DebtKind.DOMESTIC, DebtKind.EXTERNAL]:
                base_amount = random.randint(5_000_000_000, 100_000_000_000)
                if kind == DebtKind.EXTERNAL:
                    base_amount = int(base_amount * random.uniform(0.3, 0.5))
                amount = Decimal(str(base_amount))

                record = StateDebtRecord(
                    id=uuid.uuid4(),
                    state_id=state.state_id,
                    debt_kind=kind,
                    as_of_date=as_of_date,
                    amount=amount,
                    amount_original=f"₦{amount:,.0f}",
                    source_organization=f"DMO (Demo - Not Verified)",
                    source_url="https://www.dmo.gov.ng/debt-profile/sub-national-debts (demo)",
                    processing_status=ProcessingStatus.PUBLISHED,
                    verification_status=VerificationStatus.DEMO,
                    published_at=datetime.utcnow(),
                )
                session.add(record)
                debt_count += 1
        session.commit()
        print(f"   ✅ Created {debt_count} DMO debt demo records\n")

        total = igr_count + debt_count
        print("=" * 70)
        print(f"✅ Successfully generated {total} demo records in SQLite")
        print(f"   - NBS IGR 2024:        {igr_count} records")
        print(f"   - DMO Debt Sept 2024:  {debt_count} records")
        print(f"\n📂 Database location: {db_path}")
        print(f"⚠️  All records marked as (Demo) - NOT verified real data")
        print(f"\n💡 To use this database:")
        print(f"   export DATABASE_URL='sqlite+pysqlite:///{db_path}'")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)

        import traceback

        traceback.print_exc()
        sys.exit(1)
