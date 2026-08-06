"""Carregamento de configuracao com precedencia arquivo < ambiente.

Um unico ponto de verdade evita que a trilha Docker e a trilha do Raspberry Pi
divirjam silenciosamente.
"""

from __future__ import annotations

import os

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - apenas em ambientes 3.10
    import tomli as tomllib  # type: ignore[no-redef]
from dataclasses import dataclass, field
from pathlib import Path

#: Prefixo das variaveis de ambiente que sobrescrevem o arquivo de config.
ENV_PREFIX = "PICOCKPIT_"

DEFAULT_CONFIG_PATH = Path("configs/default.toml")


def default_log_dir() -> Path:
    """Diretorio de log padrao, preferindo memoria a cartao SD.

    O Raspberry Pi roda em cartao SD, que tem numero limitado de escritas. Log
    de aplicacao e o tipo de dado que se escreve o tempo todo e se le quase
    nunca - manter no cartao troca vida util por conveniencia. Em
    ``XDG_RUNTIME_DIR``, que e tmpfs, a escrita nao toca o cartao; o preco e
    que o log se perde no reinicio.

    Diagnostico que precisa sobreviver a um reboot deve ir para o banco ou
    para um destino explicito via ``PICOCKPIT_LOG_DIR``.

    Returns:
        Caminho do diretorio de log.
    """
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if runtime and Path(runtime).is_dir():
        return Path(runtime) / "picockpit" / "logs"
    return Path("/tmp/picockpit-logs")


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Configuracao efetiva da aplicacao.

    Attributes:
        env: Ambiente logico (``development`` ou ``production``).
        log_level: Nivel de log raiz.
        log_dir: Diretorio dos arquivos de log rotacionados. Por padrao em
            tmpfs, para nao gastar o cartao SD.
        provider: Provider de telemetria ativo.
        target_fps: Taxa de atualizacao alvo da UI, validada apenas no Pi real.
        sample_interval_ms: Intervalo de amostragem dos providers.
        database_path: Caminho do banco SQLite.
        theme: Tema visual inicial.
        kiosk: Inicia em tela cheia, sem decoracao de janela. E o modo de uso
            no carro; em desenvolvimento atrapalha, por isso o padrao e
            desligado.
        cluster_screen: Indice do display do motorista, onde ficam os
            instrumentos. Sem toque: e a tela que o motorista olha, nao a que
            ele opera.
        console_screen: Indice do display da multimidia, onde ficam a barra de
            navegacao, os ajustes e a projecao.
        console_fraction: Fracao do display da multimidia ocupada pela nossa
            barra. O restante fica para a janela de projecao, posicionada pelo
            compositor.
    """

    env: str = "development"
    log_level: str = "INFO"
    log_dir: Path = field(default_factory=default_log_dir)
    provider: str = "simulation"
    target_fps: int = 60
    sample_interval_ms: int = 50
    database_path: Path = Path("data/picockpit.db")
    theme: str = "normal"
    kiosk: bool = False
    cluster_screen: int = 0
    console_screen: int = 1
    console_fraction: float = 0.3


def _coerce(current: object, raw: str) -> object:
    """Converte ``raw`` para o tipo do valor atual do campo."""
    if isinstance(current, bool):
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    if isinstance(current, int):
        return int(raw)
    if isinstance(current, float):
        return float(raw)
    if isinstance(current, Path):
        return Path(raw)
    return raw


def load_config(path: Path | None = None, env: dict[str, str] | None = None) -> AppConfig:
    """Monta a configuracao a partir de defaults, arquivo TOML e ambiente.

    Args:
        path: Arquivo TOML opcional. Ausencia do arquivo nao e erro.
        env: Mapa de ambiente; usa ``os.environ`` quando omitido.

    Returns:
        Configuracao imutavel resultante.
    """
    data: dict[str, object] = {}

    config_path = path or DEFAULT_CONFIG_PATH
    if config_path.is_file():
        with config_path.open("rb") as handle:
            data.update(tomllib.load(handle))

    environ = os.environ if env is None else env
    defaults = AppConfig()
    for field_name in AppConfig.__dataclass_fields__:
        raw = environ.get(f"{ENV_PREFIX}{field_name.upper()}")
        if raw is not None:
            data[field_name] = raw

    kwargs: dict[str, object] = {}
    for field_name in AppConfig.__dataclass_fields__:
        if field_name not in data:
            continue
        kwargs[field_name] = _coerce(getattr(defaults, field_name), str(data[field_name]))

    return AppConfig(**kwargs)  # type: ignore[arg-type]
