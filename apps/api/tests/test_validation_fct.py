import uuid
from decimal import Decimal

from gaiafaac_api.database.enums import ReportedUnit
from gaiafaac_api.database.models import StateAllocation
from gaiafaac_api.pipeline.validation import _allocation_findings


def _fct_like_allocation() -> StateAllocation:
    return StateAllocation(
        id=uuid.uuid4(),
        gross_total=None,
        total_deductions=None,
        net_allocation=Decimal("10597800986.41"),
        reported_unit=ReportedUnit.NAIRA,
    )


def test_fct_may_be_published_net_only():
    findings = _allocation_findings(
        _fct_like_allocation(), [], tolerance=Decimal("0.01"), is_fct=True
    )
    codes = {f.rule_code for f in findings}
    # FCT's blank gross/deductions must NOT block.
    assert "MISSING_MONETARY_VALUE" not in codes


def test_a_normal_state_with_blank_gross_still_blocks():
    findings = _allocation_findings(
        _fct_like_allocation(), [], tolerance=Decimal("0.01"), is_fct=False
    )
    codes = {f.rule_code for f in findings}
    # A regular state with a blank gross/deductions IS flagged — the FCT allowance is narrow.
    assert "MISSING_MONETARY_VALUE" in codes
