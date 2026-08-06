#!/usr/bin/env bash
# Atualiza o PiCockpit no Raspberry Pi.
#
# Faz backup antes de qualquer coisa: atualizacao que roda migracao de banco
# sem copia de seguranca e aposta, nao procedimento.
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/picockpit}"
VENV_DIR="${VENV_DIR:-$HOME/picockpit-venv}"
SERVICE="picockpit.service"

cd "$REPO_DIR"

echo "==> Backup antes de atualizar"
"$REPO_DIR/scripts/backup.sh"

running=false
if systemctl --user is-active --quiet "$SERVICE"; then
  running=true
  echo "==> Parando o servico"
  systemctl --user stop "$SERVICE"
fi

echo "==> Atualizando o codigo"
git pull --ff-only

echo "==> Atualizando dependencias"
"$VENV_DIR/bin/python" -m pip install -q -e ".[ui]"

echo "==> Verificando a suite"
QT_QPA_PLATFORM=offscreen "$VENV_DIR/bin/python" -m pytest -q

if [[ "$running" == true ]]; then
  echo "==> Subindo o servico"
  systemctl --user start "$SERVICE"
fi

echo "==> Versao agora em $(git rev-parse --short HEAD)"
