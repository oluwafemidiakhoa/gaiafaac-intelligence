from __future__ import annotations

import csv
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import (
    ComponentType,
    ProcessingStatus,
    ReportedUnit,
    SourceStatus,
    VerificationStatus,
)
from gaiafaac_api.database.models import (
    ReportingPeriod,
    State,
    StateAllocation,
    StateAllocationComponent,
)
from gaiafaac_api.services.source_documents import register_source_document

STATE_NAMESPACE = uuid.UUID("6b89a201-17fe-45f4-aeb2-f50654fe64af")
DEMO_PERIOD_ID = uuid.UUID("de000000-0000-4000-8000-000000000001")

NIGERIAN_STATES = (
    ("Abia", "AB", "abia", "South East", "Umuahia", False),
    ("Adamawa", "AD", "adamawa", "North East", "Yola", False),
    ("Akwa Ibom", "AK", "akwa-ibom", "South South", "Uyo", False),
    ("Anambra", "AN", "anambra", "South East", "Awka", False),
    ("Bauchi", "BA", "bauchi", "North East", "Bauchi", False),
    ("Bayelsa", "BY", "bayelsa", "South South", "Yenagoa", False),
    ("Benue", "BE", "benue", "North Central", "Makurdi", False),
    ("Borno", "BO", "borno", "North East", "Maiduguri", False),
    ("Cross River", "CR", "cross-river", "South South", "Calabar", False),
    ("Delta", "DE", "delta", "South South", "Asaba", False),
    ("Ebonyi", "EB", "ebonyi", "South East", "Abakaliki", False),
    ("Edo", "ED", "edo", "South South", "Benin City", False),
    ("Ekiti", "EK", "ekiti", "South West", "Ado-Ekiti", False),
    ("Enugu", "EN", "enugu", "South East", "Enugu", False),
    (
        "Federal Capital Territory",
        "FC",
        "federal-capital-territory",
        "North Central",
        "Abuja",
        True,
    ),
    ("Gombe", "GO", "gombe", "North East", "Gombe", False),
    ("Imo", "IM", "imo", "South East", "Owerri", False),
    ("Jigawa", "JI", "jigawa", "North West", "Dutse", False),
    ("Kaduna", "KD", "kaduna", "North West", "Kaduna", False),
    ("Kano", "KN", "kano", "North West", "Kano", False),
    ("Katsina", "KT", "katsina", "North West", "Katsina", False),
    ("Kebbi", "KE", "kebbi", "North West", "Birnin Kebbi", False),
    ("Kogi", "KO", "kogi", "North Central", "Lokoja", False),
    ("Kwara", "KW", "kwara", "North Central", "Ilorin", False),
    ("Lagos", "LA", "lagos", "South West", "Ikeja", False),
    ("Nasarawa", "NA", "nasarawa", "North Central", "Lafia", False),
    ("Niger", "NI", "niger", "North Central", "Minna", False),
    ("Ogun", "OG", "ogun", "South West", "Abeokuta", False),
    ("Ondo", "ON", "ondo", "South West", "Akure", False),
    ("Osun", "OS", "osun", "South West", "Osogbo", False),
    ("Oyo", "OY", "oyo", "South West", "Ibadan", False),
    ("Plateau", "PL", "plateau", "North Central", "Jos", False),
    ("Rivers", "RI", "rivers", "South South", "Port Harcourt", False),
    ("Sokoto", "SO", "sokoto", "North West", "Sokoto", False),
    ("Taraba", "TA", "taraba", "North East", "Jalingo", False),
    ("Yobe", "YO", "yobe", "North East", "Damaturu", False),
    ("Zamfara", "ZA", "zamfara", "North West", "Gusau", False),
)


def state_id(code: str) -> uuid.UUID:
    return uuid.uuid5(STATE_NAMESPACE, code)


def seed_states(session: Session) -> int:
    """Insert or correct the canonical 36 states plus FCT, idempotently."""
    changed = 0
    existing = {state.code: state for state in session.scalars(select(State)).all()}
    for name, code, slug, zone, capital, is_fct in NIGERIAN_STATES:
        values = {
            "name": name,
            "slug": slug,
            "geopolitical_zone": zone,
            "capital": capital,
            "is_fct": is_fct,
        }
        state = existing.get(code)
        if state is None:
            session.add(State(id=state_id(code), code=code, **values))
            changed += 1
            continue
        if any(getattr(state, field) != value for field, value in values.items()):
            for field, value in values.items():
                setattr(state, field, value)
            changed += 1
    session.commit()
    return changed


def seed_demo_allocations(session: Session, csv_path: Path) -> int:
    """Load unmistakably synthetic, pending, unpublished demonstration records."""
    seed_states(session)
    source = register_source_document(
        session,
        path=csv_path,
        source_organization="GaiaFAAC Intelligence (DEMO DATA)",
        mime_type="text/csv",
        publication_date=date(2099, 2, 2),
        document_version="demo-v1",
        source_status=SourceStatus.DEMO,
        processing_status=ProcessingStatus.REGISTERED,
        is_demo=True,
    )
    period = session.get(ReportingPeriod, DEMO_PERIOD_ID)
    if period is None:
        period = ReportingPeriod(
            id=DEMO_PERIOD_ID,
            revenue_month=date(2099, 1, 1),
            faac_meeting_date=date(2099, 2, 1),
            publication_date=date(2099, 2, 2),
            reporting_label="DEMO DATA — January 2099 synthetic period",
            source_status=SourceStatus.DEMO,
            verification_status=VerificationStatus.PENDING,
            is_demo=True,
            is_published=False,
        )
        session.add(period)
        session.flush()
    if source.reporting_period_id is None:
        source.reporting_period_id = period.id

    states = {state.code: state for state in session.scalars(select(State)).all()}
    existing_codes = set(
        session.scalars(
            select(State.code)
            .join(StateAllocation, StateAllocation.state_id == State.id)
            .where(StateAllocation.reporting_period_id == period.id)
        ).all()
    )
    inserted = 0
    with csv_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["data_label"] != "DEMO DATA - NOT REAL FAAC DATA":
                raise ValueError("Demo seed row is missing the required DEMO DATA label")
            code = row["state_code"]
            if code in existing_codes:
                continue
            allocation = StateAllocation(
                reporting_period_id=period.id,
                state_id=states[code].id,
                source_document_id=source.id,
                gross_total=Decimal(row["gross_amount"]),
                total_deductions=Decimal(row["deductions_amount"]),
                net_allocation=Decimal(row["net_amount"]),
                gross_total_original=row["gross_amount"],
                total_deductions_original=row["deductions_amount"],
                net_allocation_original=row["net_amount"],
                reported_unit=ReportedUnit(row["reported_unit"]),
                verification_status=VerificationStatus.PENDING,
                is_demo=True,
                is_published=False,
            )
            session.add(allocation)
            session.flush()
            session.add(
                StateAllocationComponent(
                    state_allocation_id=allocation.id,
                    component_type=ComponentType.STATUTORY_ALLOCATION,
                    component_name="DEMO DATA — synthetic statutory component",
                    gross_amount=allocation.gross_total,
                    deduction_amount=allocation.total_deductions,
                    net_amount=allocation.net_allocation,
                    gross_amount_original=row["gross_amount"],
                    deduction_amount_original=row["deductions_amount"],
                    net_amount_original=row["net_amount"],
                    reported_unit=allocation.reported_unit,
                )
            )
            inserted += 1
    session.commit()
    return inserted
