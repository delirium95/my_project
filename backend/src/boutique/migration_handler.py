"""One-off Lambda entry point for safe production Alembic upgrades."""

from pathlib import Path

from alembic.config import Config

from alembic import command


def handler(_event: dict[str, object], _context: object) -> dict[str, str]:
    """Upgrade the configured database to the current migration head.

    The function shares the API Lambda's VPC and environment variables, so migrations can run
    against a private RDS database without a bastion host or a NAT gateway.
    """
    task_root = Path(__file__).resolve().parent.parent
    config = Config(str(task_root / "alembic.ini"))
    config.set_main_option("script_location", str(task_root / "alembic"))
    command.upgrade(config, "head")
    return {"status": "upgraded"}
