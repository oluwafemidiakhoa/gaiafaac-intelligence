#!/usr/bin/env python3.12
"""Generate realistic fixture data for demo/testing: NBS IGR, DMO Debt, State Budgets"""

import random
import sys
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from gaiafaac_api.database.debt_models import DebtKind, StateDebtRecord
from gaiafaac_api.database.enums import ProcessingStatus, VerificationStatus
from gaiafaac_api.database.igr_models import IgrPeriodType, StateIgrRecord
from gaiafaac_api.database.models import State
from gaiafaac_api.database.session import create_database_engine, create_session_factory


def generate_nbs_igr_demo(session: Session, states: list[State]) -> int:
    """Generate demo NBS IGR records for all states (2024)"""
    print("📊 Generating NBS IGR demo data for 2024...")

    count = 0
    for state in states:
        # Realistic IGR: ₦500M - ₦50B depending on state size
        amount = Decimal(str(random.randint(500_000_000, 50_000_000_000)))

        record = StateIgrRecord(
            id=uuid.uuid4(),
            state_id=state.id,
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
        count += 1

    session.commit()
    print(f"   ✅ Created {count} NBS IGR demo records")
    return count


def generate_dmo_debt_demo(session: Session, states: list[State]) -> int:
    """Generate demo DMO debt records for all states (September 2024)"""
    print("💳 Generating DMO domestic and external debt demo data...")

    count = 0
    as_of_date = date(2024, 9, 1)

    for state in states:
        for kind in [DebtKind.DOMESTIC, DebtKind.EXTERNAL]:
            # Realistic debt: ₦5B - ₦100B depending on state and type
            base_amount = random.randint(5_000_000_000, 100_000_000_000)
            # External debt typically 30-50% of domestic
            if kind == DebtKind.EXTERNAL:
                base_amount = int(base_amount * random.uniform(0.3, 0.5))

            amount = Decimal(str(base_amount))

            record = StateDebtRecord(
                id=uuid.uuid4(),
                state_id=state.id,
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
            count += 1

    session.commit()
    print(f"   ✅ Created {count} DMO debt demo records (domestic + external)")
    return count


def main() -> None:
    """Main entry point"""
    print("\n" + "=" * 70)
    print("GaiaFAAC Intelligence - Demo Data Generator")
    print("=" * 70 + "\n")

    try:
        engine = create_database_engine()
        session_factory = create_session_factory(engine)

        with session_factory() as session:
            # Fetch all states
            states = session.query(State).all()
            if not states:
                print("❌ No states found in database. Run migrations first:")
                print("   alembic upgrade head")
                sys.exit(1)

            print(f"🌍 Found {len(states)} states in database\n")

            # Generate demo data
            igr_count = generate_nbs_igr_demo(session, states)
            debt_count = generate_dmo_debt_demo(session, states)

            total = igr_count + debt_count
            print(f"\n{'=' * 70}")
            print(f"✅ Successfully generated {total} demo records")
            print(f"   - NBS IGR 2024:        {igr_count} records")
            print(f"   - DMO Debt Sept 2024:  {debt_count} records")
            print(f"\n⚠️  All records marked as (Demo) - NOT verified real data")
            print(f"    These are for UI/API testing only")
            print(f"\n💡 Next steps:")
            print(f"   1. Visit https://gaiafaac-web.up.railway.app")
            print(f"   2. See demo records in Evidence Network")
            print(f"   3. Test watchlists and exports with demo data")
            print(f"   4. Pricing/signup ready at /pricing")
            print("=" * 70 + "\n")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
