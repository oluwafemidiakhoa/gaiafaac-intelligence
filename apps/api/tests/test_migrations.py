from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from gaiafaac_api.config import get_settings

EXPECTED_TABLES = {
    "audit_logs",
    "evidence_manifests",
    "evidence_conflict_claims",
    "evidence_conflicts",
    "evidence_sources",
    "evidence_verifications",
    "extraction_runs",
    "forecasts",
    "fiscal_claims",
    "fiscal_proofs",
    "fiscal_states",
    "claim_revisions",
    "generated_insights",
    "national_distributions",
    "organizations",
    "reporting_periods",
    "source_documents",
    "state_allocation_components",
    "state_allocations",
    "state_indicators",
    "states",
    "subscriptions",
    "users",
    "validation_results",
}

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_alembic_upgrade_and_downgrade(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "migration.db"
    database_url = f"sqlite+pysqlite:///{database_path}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()
    config = Config(REPOSITORY_ROOT / "alembic.ini")

    command.upgrade(config, "head")
    engine = create_engine(database_url)
    assert set(inspect(engine).get_table_names()) >= EXPECTED_TABLES

    command.downgrade(config, "base")
    assert set(inspect(engine).get_table_names()) == {"alembic_version"}
    engine.dispose()
    get_settings.cache_clear()
