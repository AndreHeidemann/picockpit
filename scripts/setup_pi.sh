#!/usr/bin/env bash
# Prepara o ambiente Python do Raspberry Pi: venv e dependencias de UI.
# Idempotente: pode ser reexecutado com seguranca.
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/picockpit}"
VENV_DIR="${VENV_DIR:-$HOME/picockpit-venv}"

# A versao do PySide6 nao e uma preferencia, e uma consequencia da glibc do
# sistema: as wheels aarch64 a partir de 6.8.1 sao `manylinux_2_39`. Deixar o
# pip descobrir isso sozinho funciona, mas quando falha o erro nao diz que o
# problema e a glibc. Escolhendo o constraint aqui, a decisao fica visivel e o
# mesmo repositorio serve Bookworm e Trixie sem edicao manual.
glibc_minor() {
  local raw
  raw="$(getconf GNU_LIBC_VERSION 2>/dev/null || ldd --version 2>/dev/null | head -1)"
  raw="${raw##* }"          # "glibc 2.36" -> "2.36"
  local major="${raw%%.*}"
  local minor="${raw#*.}"
  minor="${minor%%.*}"
  # Fora da serie 2.x estamos em algo mais novo do que tudo que conhecemos.
  [[ "$major" == "2" ]] || { echo 99; return; }
  echo "${minor:-0}"
}

MINOR="$(glibc_minor)"
if (( MINOR >= 39 )); then
  CONSTRAINTS="$REPO_DIR/constraints/trixie.txt"
else
  CONSTRAINTS="$REPO_DIR/constraints/bookworm.txt"
fi
echo "glibc 2.$MINOR -> $(basename "$CONSTRAINTS")"

if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -e "$REPO_DIR[ui]" -c "$CONSTRAINTS"

"$VENV_DIR/bin/python" - <<'PY'
import PySide6
from PySide6.QtCore import qVersion
print(f"PySide6 {PySide6.__version__} sobre Qt {qVersion()}")
PY

if (( MINOR >= 39 )); then
  echo
  echo "Primeira instalacao no Trixie: copie a versao impressa acima para"
  echo "constraints/trixie.txt como pin exato e faca commit."
fi
