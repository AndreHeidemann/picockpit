#!/usr/bin/env bash
# Forca as saidas HDMI a existirem mesmo sem monitor conectado.
#
# Sem isso, o Pi desabilita a saida quando nada esta plugado, a sessao grafica
# fica sem output e nao ha o que compartilhar pelo Raspberry Pi Connect - o
# desenvolvimento passa a exigir um monitor dedicado ao Pi.
#
# O sufixo `D` em `video=` liga a saida digital independentemente da deteccao
# de hotplug. Funciona porque o config.txt ja tem `disable_fw_kms_setup=1`, que
# entrega o controle de modo ao kernel em vez do firmware.
#
# Precisa de sudo e de reiniciar. Executar no Raspberry Pi.
set -euo pipefail

CMDLINE="${CMDLINE:-/boot/firmware/cmdline.txt}"

# Cluster do motorista: proporcao automotiva widescreen.
CLUSTER_MODE="${CLUSTER_MODE:-1280x480@60}"
# Multimidia: onde ficam navegacao, ajustes e, no futuro, a projecao.
CONSOLE_MODE="${CONSOLE_MODE:-1920x1080@60}"

FORCED="video=HDMI-A-1:${CLUSTER_MODE}D video=HDMI-A-2:${CONSOLE_MODE}D"

if [[ $EUID -ne 0 ]]; then
  echo "Precisa de sudo: sudo $0" >&2
  exit 1
fi

if grep -q "video=HDMI-A-1" "$CMDLINE"; then
  echo "As saidas ja estao forcadas em $CMDLINE:"
  grep -o 'video=[^ ]*' "$CMDLINE"
  echo
  echo "Para trocar de modo, rode primeiro: sudo $0 --remover"
  exit 0
fi

if [[ "${1:-}" == "--remover" ]]; then
  cp "$CMDLINE" "$CMDLINE.picockpit-bak"
  sed -i -E 's/ ?video=HDMI-A-[12]:[^ ]*//g' "$CMDLINE"
  echo "Saidas forcadas removidas. Reinicie para aplicar."
  exit 0
fi

cp "$CMDLINE" "$CMDLINE.picockpit-bak"
# cmdline.txt e uma linha unica: os parametros entram no fim dela, sem quebra.
sed -i "1s|\$| ${FORCED}|" "$CMDLINE"

echo "Backup em $CMDLINE.picockpit-bak"
echo "Linha resultante:"
cat "$CMDLINE"
echo
echo "Reinicie para aplicar:  sudo reboot"
echo "Depois confira com:     wlr-randr"
