import logging
import os
from pathlib import Path

logger = logging.getLogger("metricmind.migrations")


def run_migrations_upgrade(revision: str = "head") -> bool:
    try:
        from alembic.config import Config

        from alembic import command
    except ImportError:
        logger.exception("alembic is not installed; cannot run migrations")
        return False

    try:
        backend_root = Path(__file__).resolve().parents[2]
        ini_path = backend_root / "alembic.ini"
        if not ini_path.exists():
            logger.error("alembic.ini not found at %s", ini_path)
            return False

        config = Config(str(ini_path))
        config.set_main_option("script_location", str(backend_root / "alembic"))

        database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql://metricmind:metricmind@localhost:5433/metricmind",
        )
        config.set_main_option("sqlalchemy.url", database_url)

        command.upgrade(config, revision)
        logger.info("Migrations upgraded successfully to %s", revision)
        return True
    except Exception as exc:
        logger.exception("Failed to run migrations upgrade: %s", exc)
        return False
