#!/usr/bin/env bash
# Forca as saidas HDMI a existirem mesmo sem monitor conectado.
#
# Sem isso, o Pi desabilita a saida quando nada esta plugado, a sessao grafica
# fica sem output e nao ha o que compartilhar pelo Raspberry Pi Connect - o
# desenvolvimento passa a exigir um monitor dedicado ao Pi.
#
# Dois sufixos importam em `video=`:
#
#   D  liga a saida digital independentemente da deteccao de hotplug
#   M  manda o kernel calcular a temporizacao pela norma VESA CVT
#
# O `M` nao e opcional para modos automotivos. Sem monitor nao ha EDID, e o
# driver so conhece a lista de modos padrao - 1280x480 nao esta nela, e a saida
# cai para 1024x768 silenciosamente. Com `M`, o kernel gera a temporizacao.
#
# Tudo isso depende de `disable_fw_kms_setup=1` no config.txt, que entrega o
# controle de modo ao kernel em vez do firmware.
#
# Precisa de sudo e de reiniciar. Executar no Raspberry Pi.
set -euo pipefail

CMDLINE="${CMDLINE:-/boot/firmware/cmdline.txt}"
CONFIG="${CONFIG:-/boot/firmware/config.txt}"

# Cluster do motorista: proporcao automotiva widescreen.
CLUSTER_MODE="${CLUSTER_MODE:-1280x480@60}"
# Multimidia: onde ficam navegacao, ajustes e, no futuro, a projecao.
CONSOLE_MODE="${CONSOLE_MODE:-1920x1080@60}"

# Formato: <largura>x<altura>M@<taxa>D
FORCED="video=HDMI-A-1:${CLUSTER_MODE%@*}M@${CLUSTER_MODE#*@}D"
FORCED="$FORCED video=HDMI-A-2:${CONSOLE_MODE%@*}M@${CONSOLE_MODE#*@}D"

if [[ $EUID -ne 0 ]]; then
  echo "Precisa de sudo: sudo $0" >&2
  exit 1
fi

if [[ "${1:-}" == "--remover" ]]; then
  cp "$CMDLINE" "$CMDLINE.picockpit-bak"
  sed -i -E 's/ ?video=HDMI-A-[12]:[^ ]*//g' "$CMDLINE"
  echo "Saidas forcadas removidas. Reinicie para aplicar."
  exit 0
fi

# O `video=` do cmdline so vale se o kernel estiver no comando do modo. Sem
# isso o firmware configura o display antes e o parametro vira decoracao. Numa
# instalacao limpa a linha pode nao existir, e a falha e silenciosa: o Pi sobe,
# so nao tem saida nenhuma para compartilhar.
if ! grep -qE '^\s*disable_fw_kms_setup=1' "$CONFIG"; then
  cp "$CONFIG" "$CONFIG.picockpit-bak"
  printf '\n# PiCockpit: entrega o controle de modo ao kernel\ndisable_fw_kms_setup=1\n' >> "$CONFIG"
  echo "disable_fw_kms_setup=1 adicionado a $CONFIG"
fi

cp "$CMDLINE" "$CMDLINE.picockpit-bak"

# Remove qualquer forcamento anterior antes de escrever o novo, para o script
# poder ser rodado de novo com outros modos sem duplicar parametros.
sed -i -E 's/ ?video=HDMI-A-[12]:[^ ]*//g' "$CMDLINE"

# cmdline.txt e uma linha unica: os parametros entram no fim dela, sem quebra.
sed -i "1s|\$| ${FORCED}|" "$CMDLINE"

echo "Backup em $CMDLINE.picockpit-bak"
echo "Linha resultante:"
cat "$CMDLINE"
echo
echo "Reinicie para aplicar:  sudo reboot"
echo "Depois confira com:     wlr-randr"
