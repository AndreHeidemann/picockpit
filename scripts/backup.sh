#!/usr/bin/env bash
# Copia de seguranca do banco e das configuracoes.
#
# O banco e copiado com a API de backup do SQLite, nao com `cp`: em modo WAL,
# copiar o arquivo com a aplicacao rodando pode capturar um estado
# inconsistente, sem as transacoes que ainda vivem no journal.
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/picockpit}"
VENV_DIR="${VENV_DIR:-$HOME/picockpit-venv}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/picockpit-backups}"
DB_PATH="${DB_PATH:-$REPO_DIR/data/picockpit.db}"
KEEP="${KEEP:-10}"

stamp="$(date +%Y%m%d-%H%M%S)"
target="$BACKUP_DIR/picockpit-$stamp"
mkdir -p "$target"

if [[ -f "$DB_PATH" ]]; then
  "$VENV_DIR/bin/python" - "$DB_PATH" "$target/picockpit.db" <<'PY'
import sqlite3
import sys

source, destination = sys.argv[1], sys.argv[2]
with sqlite3.connect(source) as origin, sqlite3.connect(destination) as copy:
    origin.backup(copy)
print(f"banco copiado para {destination}")
PY
else
  echo "banco ainda nao existe, pulando"
fi

cp -r "$REPO_DIR/configs" "$target/configs"

# Os drop-ins de systemd nao estao no repositorio de proposito: descrevem esta
# maquina (quantas telas, quais indices), nao o projeto. Justamente por isso
# somem numa reinstalacao e ninguem percebe ate a interface subir na tela
# errada.
DROPIN_DIR="$HOME/.config/systemd/user/picockpit.service.d"
if compgen -G "$DROPIN_DIR/*.conf" > /dev/null; then
  mkdir -p "$target/systemd"
  cp "$DROPIN_DIR"/*.conf "$target/systemd/"
  echo "drop-ins de systemd incluidos"
fi

# Retrato do sistema. Nao e restauravel automaticamente - mexer em
# /boot/firmware exige sudo - mas sem ele a instalacao limpa perde os modos de
# video forcados, e o Pi volta a exigir monitor fisico para ser acessado.
{
  echo "# Gerado por scripts/backup.sh em $(date -Is)"
  echo "## sistema"
  grep PRETTY_NAME /etc/os-release 2>/dev/null || true
  echo "glibc $(getconf GNU_LIBC_VERSION 2>/dev/null | awk '{print $NF}')"
  echo "python $(python3 -V 2>&1)"
  echo "compositor ${XDG_CURRENT_DESKTOP:-desconhecido}"
  echo "## modos de video forcados em cmdline.txt"
  grep -o -E 'video=HDMI-A-[12]:[^ ]*' /boot/firmware/cmdline.txt 2>/dev/null || echo "nenhum"
} > "$target/sistema.txt"

tar -czf "$target.tar.gz" -C "$BACKUP_DIR" "picockpit-$stamp"
rm -rf "$target"
echo "backup em $target.tar.gz"

# Mantem apenas os mais recentes: cartao cheio derruba a aplicacao inteira.
#
# O corpo do laco nao pode ser uma cadeia com `&&`: sob `set -e`, a cadeia que
# termina em falso derruba o script. Era o que acontecia quando nao havia nada
# a apagar - o backup ficava pronto e correto, mas o script saia com codigo 1,
# e qualquer automacao encadeada depois dele parava sem motivo aparente.
mapfile -t old < <(ls -1t "$BACKUP_DIR"/picockpit-*.tar.gz 2>/dev/null | tail -n +$((KEEP + 1)))
for file in "${old[@]}"; do
  rm -f "$file"
  echo "removido backup antigo: $(basename "$file")"
done
