#!/usr/bin/env bash
# Instala o PiCockpit como servico de usuario do systemd.
# Executar no Raspberry Pi, com o usuario que roda a sessao grafica.
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/picockpit}"
UNIT_DIR="$HOME/.config/systemd/user"
UNIT_NAME="picockpit.service"

# Garante o bit de execucao: clone vindo de filesystem Windows chega sem
# ele, e os scripts de manutencao precisam rodar direto.
chmod +x "$REPO_DIR"/scripts/*.sh

mkdir -p "$UNIT_DIR"
install -m 644 "$REPO_DIR/deployment/$UNIT_NAME" "$UNIT_DIR/$UNIT_NAME"

systemctl --user daemon-reload
systemctl --user enable "$UNIT_NAME"

echo "Servico instalado. Comandos uteis:"
echo "  systemctl --user start picockpit     # inicia agora"
echo "  systemctl --user status picockpit    # estado e ultimas linhas"
echo "  systemctl --user stop picockpit      # para, gravando a viagem"
echo "  journalctl --user -u picockpit -f    # acompanha o log"
