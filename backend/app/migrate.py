"""Safe migration bootstrap for existing Sprint 2.1 and new databases."""
from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from .database import engine

BASELINE = "0001_sprint2_baseline"
CORE_TABLES = {
    "clinics", "doctors", "services", "patients", "doctor_schedules",
    "appointments", "appointment_events"
}


def alembic_config() -> Config:
    root = Path(__file__).resolve().parents[2]
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "backend" / "migrations"))
    return cfg


def migrate() -> None:
    cfg = alembic_config()
    tables = set(inspect(engine).get_table_names())
    if "alembic_version" in tables:
        print("Database already managed by Alembic; upgrading to head...")
        command.upgrade(cfg, "head")
        return

    existing_core = CORE_TABLES.intersection(tables)
    if existing_core:
        missing = CORE_TABLES - tables
        if missing:
            raise RuntimeError(
                "Existing database looks incomplete. Missing baseline tables: "
                + ", ".join(sorted(missing))
                + ". Migration stopped to protect your data."
            )
        print("Existing Sprint 2.x schema detected; stamping Alembic baseline without deleting data...")
        command.stamp(cfg, BASELINE)
        command.upgrade(cfg, "head")
    else:
        print("New database detected; creating schema through Alembic...")
        command.upgrade(cfg, "head")


if __name__ == "__main__":
    migrate()
