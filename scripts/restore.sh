#!/usr/bin/env bash
# Restaura um backup gerado por scripts/backup.sh.
#
# Uso: scripts/restore.sh ~/picockpit-backups/picockpit-20260806-120000.tar.gz
set -euo pipefail

ARCHIVE="${1:?informe o arquivo .tar.gz do backup}"
REPO_DIR="${REPO_DIR:-$HOME/picockpit}"
SERVICE="picockpit.service"

if systemctl --user is-active --quiet "$SERVICE"; then
  echo "==> Parando o servico"
  systemctl --user stop "$SERVICE"
fi

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT
tar -xzf "$ARCHIVE" -C "$workdir"
extracted="$(find "$workdir" -maxdepth 1 -type d -name 'picockpit-*' | head -1)"

if [[ -f "$extracted/picockpit.db" ]]; then
  mkdir -p "$REPO_DIR/data"
  # Os arquivos irmaos do WAL precisam sair junto, senao o SQLite tenta
  # reaplicar um journal que nao pertence mais a este banco.
  rm -f "$REPO_DIR/data/picockpit.db-wal" "$REPO_DIR/data/picockpit.db-shm"
  cp "$extracted/picockpit.db" "$REPO_DIR/data/picockpit.db"
  echo "banco restaurado"
fi

if [[ -d "$extracted/configs" ]]; then
  cp -r "$extracted/configs/." "$REPO_DIR/configs/"
  echo "configuracoes restauradas"
fi

if [[ -d "$extracted/systemd" ]]; then
  dropin_dir="$HOME/.config/systemd/user/picockpit.service.d"
  mkdir -p "$dropin_dir"
  cp "$extracted/systemd/." "$dropin_dir/" -r
  systemctl --user daemon-reload
  echo "drop-ins de systemd restaurados"
fi

# O que exige sudo fica como instrucao, nao como acao: um script de restauracao
# que mexe sozinho no boot e uma forma barata de deixar o Pi sem subir.
if [[ -f "$extracted/sistema.txt" ]]; then
  echo
  echo "==> Retrato do sistema de origem (conferir manualmente):"
  sed 's/^/    /' "$extracted/sistema.txt"
  if grep -q '^video=' "$extracted/sistema.txt"; then
    echo
    echo "    Havia modos de video forcados. Para reproduzi-los:"
    echo "    sudo bash $REPO_DIR/scripts/setup_displays.sh"
  fi
fi

echo
echo "Pronto. Suba com: systemctl --user start picockpit"
