#!/usr/bin/env bash
# Prepara o ambiente Python do Raspberry Pi: venv e dependencias de UI.
# Idempotente: pode ser reexecutado com seguranca.
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/picockpit}"
VENV_DIR="${VENV_DIR:-$HOME/picockpit-venv}"

if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip
# PySide6 fixado em 6.8.0.2: ultima wheel aarch64 manylinux_2_31, compativel
# com a glibc 2.36 do Raspberry Pi OS 12. Ver README.
"$VENV_DIR/bin/python" -m pip install -e "$REPO_DIR[ui]"

"$VENV_DIR/bin/python" - <<'PY'
import PySide6
from PySide6.QtCore import qVersion
print(f"PySide6 {PySide6.__version__} sobre Qt {qVersion()}")
PY
