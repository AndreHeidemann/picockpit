#!/usr/bin/env bash
# Aplica os modos de video das telas automotivas na sessao grafica.
#
# Por que isto existe, se o `setup_displays.sh` ja escreve `video=` no
# cmdline.txt: no Raspberry Pi OS 13 (Trixie), com kernel 6.18, o parametro
# passou a ligar a saida sem fixar o modo. Medido na migracao: HDMI-A-1 subiu
# em 1024x768 mesmo com `video=HDMI-A-1:1280x480M@60D` na linha de comando.
# No Bookworm, com kernel 6.6, o mesmo parametro entregava o modo pedido.
#
# O `video=` continua necessario - e ele que faz a saida existir sem monitor,
# que e o que devolve o acesso remoto. O modo, agora, e aplicado aqui.
#
# Idempotente e tolerante: saida ausente nao e erro. Um cluster desconectado na
# bancada nao pode impedir o painel de subir.
set -uo pipefail

CLUSTER_OUTPUT="${CLUSTER_OUTPUT:-HDMI-A-1}"
CONSOLE_OUTPUT="${CONSOLE_OUTPUT:-HDMI-A-2}"
CLUSTER_MODE="${CLUSTER_MODE:-1280x480@60}"
CONSOLE_MODE="${CONSOLE_MODE:-1920x1080@60}"

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"

if ! command -v wlr-randr > /dev/null; then
  echo "wlr-randr nao encontrado; modos nao aplicados" >&2
  exit 0
fi

if [[ ! -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" ]]; then
  echo "sem sessao Wayland em $XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" >&2
  exit 0
fi

present="$(wlr-randr 2>/dev/null | grep -oE '^[A-Za-z0-9-]+' || true)"

apply() {
  local output="$1" mode="$2"
  if ! grep -qx "$output" <<< "$present"; then
    echo "$output ausente; ignorando"
    return
  fi
  # `--custom-mode` e nao `--mode`: 1280x480 nao esta na lista de modos padrao
  # e, sem EDID de um monitor real, nao ha de onde tira-lo.
  if wlr-randr --output "$output" --custom-mode "$mode" 2>/dev/null; then
    echo "$output -> $mode"
  else
    echo "$output: falhou ao aplicar $mode" >&2
  fi
}

apply "$CLUSTER_OUTPUT" "$CLUSTER_MODE"
apply "$CONSOLE_OUTPUT" "$CONSOLE_MODE"
