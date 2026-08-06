#!/usr/bin/env bash
# Sobe o PiCockpit OS na sessao grafica ativa do Raspberry Pi.
# Executar SEMPRE no Pi (via SSH ou shell remoto do Raspberry Pi Connect).
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/picockpit}"
VENV_DIR="${VENV_DIR:-$HOME/picockpit-venv}"

cd "$REPO_DIR"

# A sessao do usuario grafico nao e herdada por uma conexao SSH; apontamos
# explicitamente para o socket Wayland e para o barramento da sessao.
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export DISPLAY="${DISPLAY:-:0}"

if [[ -z "${QT_QPA_PLATFORM:-}" ]]; then
  if [[ -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" ]]; then
    # Wayland nativo evita a camada extra do Xwayland e entrega o melhor FPS.
    export QT_QPA_PLATFORM="wayland;xcb"
  else
    export QT_QPA_PLATFORM="xcb"
  fi
fi

export PYTHONPATH="$REPO_DIR"
exec "$VENV_DIR/bin/python" -m picockpit.app.main "$@"
