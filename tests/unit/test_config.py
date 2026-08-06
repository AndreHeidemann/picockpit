"""Testes do carregamento de configuracao."""

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
