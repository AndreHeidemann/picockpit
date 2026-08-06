"""Testes do carregamento de configuracao."""

import os
from pathlib import Path

from picockpit.core.config import AppConfig, load_config


def test_defaults_when_no_file_and_no_env() -> None:
    config = load_config(path=Path("nao-existe.toml"), env={})
    assert config == AppConfig()


def test_file_values_override_defaults(tmp_path: Path) -> None:
    config_file = tmp_path / "app.toml"
    config_file.write_text('log_level = "DEBUG"\ntarget_fps = 30\n', encoding="utf-8")

    config = load_config(path=config_file, env={})

    assert config.log_level == "DEBUG"
    assert config.target_fps == 30


def test_env_overrides_file(tmp_path: Path) -> None:
    config_file = tmp_path / "app.toml"
    config_file.write_text('log_level = "DEBUG"\n', encoding="utf-8")

    config = load_config(path=config_file, env={"PICOCKPIT_LOG_LEVEL": "ERROR"})

    assert config.log_level == "ERROR"


def test_env_values_are_coerced_to_field_types() -> None:
    config = load_config(
        path=Path("nao-existe.toml"),
        env={"PICOCKPIT_TARGET_FPS": "30", "PICOCKPIT_DATABASE_PATH": "/tmp/x.db"},
    )

    assert config.target_fps == 30
    assert config.database_path == Path("/tmp/x.db")


def test_unknown_env_keys_are_ignored() -> None:
    config = load_config(path=Path("nao-existe.toml"), env={"PICOCKPIT_NAO_EXISTE": "1"})
    assert config == AppConfig()


def test_kiosk_is_off_by_default() -> None:
    assert load_config(path=Path("nao-existe.toml"), env={}).kiosk is False


def test_kiosk_reads_boolean_words_from_the_environment() -> None:
    """O servico systemd liga o modo kiosk por variavel de ambiente."""
    for value in ("true", "1", "yes", "on"):
        config = load_config(path=Path("nao-existe.toml"), env={"PICOCKPIT_KIOSK": value})
        assert config.kiosk is True, value

    for value in ("false", "0", "no", ""):
        config = load_config(path=Path("nao-existe.toml"), env={"PICOCKPIT_KIOSK": value})
        assert config.kiosk is False, value


def test_log_dir_defaults_to_tmpfs_when_available(tmp_path: Path) -> None:
    """Sem SSD, log nao pode morar no cartao SD por padrao."""
    from picockpit.core.config import default_log_dir

    runtime = tmp_path / "run"
    runtime.mkdir()
    original = os.environ.get("XDG_RUNTIME_DIR")
    os.environ["XDG_RUNTIME_DIR"] = str(runtime)
    try:
        assert default_log_dir() == runtime / "picockpit" / "logs"
    finally:
        if original is None:
            del os.environ["XDG_RUNTIME_DIR"]
        else:
            os.environ["XDG_RUNTIME_DIR"] = original


def test_log_dir_falls_back_without_runtime_dir() -> None:
    from picockpit.core.config import default_log_dir

    original = os.environ.pop("XDG_RUNTIME_DIR", None)
    try:
        assert default_log_dir() == Path("/tmp/picockpit-logs")
    finally:
        if original is not None:
            os.environ["XDG_RUNTIME_DIR"] = original


def test_log_dir_can_still_be_forced_by_environment(tmp_path: Path) -> None:
    config = load_config(
        path=Path("nao-existe.toml"),
        env={"PICOCKPIT_LOG_DIR": str(tmp_path / "diagnostico")},
    )

    assert config.log_dir == tmp_path / "diagnostico"
