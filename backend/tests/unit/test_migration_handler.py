from pathlib import Path

from boutique import migration_handler


def test_migration_handler_upgrades_packaged_alembic_head(monkeypatch) -> None:
    configured: dict[str, str] = {}
    upgraded: list[tuple[object, str]] = []

    class FakeConfig:
        def __init__(self, config_path: str) -> None:
            configured["config_path"] = config_path

        def set_main_option(self, key: str, value: str) -> None:
            configured[key] = value

    monkeypatch.setattr(migration_handler, "Config", FakeConfig)
    monkeypatch.setattr(
        migration_handler.command,
        "upgrade",
        lambda config, revision: upgraded.append((config, revision)),
    )

    assert migration_handler.handler({}, object()) == {"status": "upgraded"}
    task_root = Path(migration_handler.__file__).resolve().parent.parent
    assert configured["config_path"] == str(task_root / "alembic.ini")
    assert configured["script_location"] == str(task_root / "alembic")
    assert upgraded[0][1] == "head"
