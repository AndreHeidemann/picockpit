#!/usr/bin/env bash
# Instala o PiCockpit como servico de usuario do systemd.
# Executar no Raspberry Pi, com o usuario que roda a sessao grafica.
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/picockpit}"
UNIT_DIR="$HOME/.config/systemd/user"

# A unidade de modos de video vem antes do painel: no Trixie o `video=` do
# kernel liga a saida mas nao fixa o modo, entao alguem precisa aplica-lo na
# sessao grafica antes de a interface medir o tamanho da tela.
UNITS=(picockpit-displays.service picockpit.service)

# Garante o bit de execucao: clone vindo de filesystem Windows chega sem
# ele, e os scripts de manutencao precisam rodar direto.
chmod +x "$REPO_DIR"/scripts/*.sh

mkdir -p "$UNIT_DIR"
for unit in "${UNITS[@]}"; do
  install -m 644 "$REPO_DIR/deployment/$unit" "$UNIT_DIR/$unit"
done

systemctl --user daemon-reload
for unit in "${UNITS[@]}"; do
  systemctl --user enable "$unit"
done

echo "Servicos instalados: ${UNITS[*]}"
echo "Comandos uteis:"
echo "  systemctl --user start picockpit     # inicia agora"
echo "  systemctl --user status picockpit    # estado e ultimas linhas"
echo "  systemctl --user stop picockpit      # para, gravando a viagem"
echo "  journalctl --user -u picockpit -f    # acompanha o log"
