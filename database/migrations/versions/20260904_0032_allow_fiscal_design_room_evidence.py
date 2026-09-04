"""Allow immutable Fiscal Design scenario evidence in Decision Rooms.

Revision ID: 20260904_0032
Revises: 20260904_0031
"""

from alembic import op

revision = "20260904_0032"
down_revision = "20260904_0031"
branch_labels = None
depends_on = None

_OLD = (
    "reference_kind IN ('organization_alert', 'fiscal_proof', 'decision_packet', "
    "'source', 'fiscal_event')"
)
_NEW = (
    "reference_kind IN ('organization_alert', 'fiscal_proof', 'decision_packet', "
    "'fiscal_design_scenario', 'source', 'fiscal_event')"
)


def _replace(expression: str) -> None:
    with op.batch_alter_table("evidence_room_evidence") as batch:
        batch.drop_constraint("ck_evidence_room_reference_kind", type_="check")
        batch.create_check_constraint("ck_evidence_room_reference_kind", expression)


def upgrade() -> None:
    _replace(_NEW)


def downgrade() -> None:
    _replace(_OLD)
