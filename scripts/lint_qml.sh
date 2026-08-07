#!/usr/bin/env bash
# Analise estatica dos arquivos QML.
#
# Existe por causa de um bug real da Etapa 3: `opacity` atribuido a um
# ShapePath, que nao e um Item. O QML so reclamou em tempo de execucao, e com
# uma mensagem que apontava para o lugar errado ("Cannot assign object to list
# property data"). O qmllint pega esse tipo de erro antes de rodar.
#
# Executar no Raspberry Pi: o qmllint vem junto do PySide6.
set -uo pipefail

REPO_DIR="${REPO_DIR:-$HOME/picockpit}"
QMLLINT="${QMLLINT:-$HOME/picockpit-venv/bin/pyside6-qmllint}"

if [[ ! -x "$QMLLINT" ]]; then
  echo "pyside6-qmllint nao encontrado em $QMLLINT" >&2
  exit 127
fi

mapfile -t FILES < <(find "$REPO_DIR/picockpit/ui/qml" -name '*.qml' | sort)

# `--import` e `--unqualified` desligados de proposito: os singletons do modulo
# PiCockpit sao registrados em tempo de execucao pelo Python, entao nao existem
# em disco para o qmllint resolver. As categorias que importam - propriedade
# inexistente, tipo errado, sintaxe - continuam ativas.
output="$("$QMLLINT" --import disable --unqualified disable "${FILES[@]}" 2>&1)"
status=$?

[[ -n "$output" ]] && printf '%s\n' "$output"

# O qmllint devolve zero mesmo tendo impresso avisos, e a versao anterior deste
# script confiava so no codigo de saida: ele anunciava "sem problemas" logo
# abaixo de uma tela de avisos. Um aviso novo passaria despercebido no meio dos
# antigos - que e exatamente o modo de falha que um linter deveria impedir.
warnings=$(printf '%s\n' "$output" | grep -c '^\(Warning\|Error\|Critical\):')
notes=$(printf '%s\n' "$output" | grep -c '^Info:')

if [[ $status -ne 0 || $warnings -gt 0 ]]; then
  echo "qmllint: $warnings aviso(s) em ${#FILES[@]} arquivos" >&2
  exit 1
fi

if [[ $notes -gt 0 ]]; then
  echo "qmllint: ${#FILES[@]} arquivos sem avisos, $notes observacao(oes)"
  exit 0
fi

echo "qmllint: ${#FILES[@]} arquivos sem problemas"
