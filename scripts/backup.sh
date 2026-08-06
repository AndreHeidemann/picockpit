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

tar -czf "$target.tar.gz" -C "$BACKUP_DIR" "picockpit-$stamp"
rm -rf "$target"
echo "backup em $target.tar.gz"

# Mantem apenas os mais recentes: cartao cheio derruba a aplicacao inteira.
mapfile -t old < <(ls -1t "$BACKUP_DIR"/picockpit-*.tar.gz 2>/dev/null | tail -n +$((KEEP + 1)))
for file in "${old[@]:-}"; do
  [[ -n "$file" ]] && rm -f "$file" && echo "removido backup antigo: $(basename "$file")"
done
