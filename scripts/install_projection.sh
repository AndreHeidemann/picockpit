#!/usr/bin/env bash
# Instala a unidade de servico da projecao e mostra o que ainda depende de voce.
#
# NAO instala o LIVI. O LIVI e software de terceiros sob GPL-3.0-or-later, com
# instalador proprio; baixa-lo daqui misturaria as duas distribuicoes sem
# necessidade. Este script cuida do nosso lado: a unidade que tira a projecao do
# autostart e a regra de janela do compositor.
#
# Executar no Raspberry Pi, depois da migracao para o Trixie.
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/picockpit}"
UNIT_DIR="$HOME/.config/systemd/user"
# Caminho real do instalador oficial (scripts/install/desktop/install.sh):
# $USER_HOME/LIVI/LIVI.AppImage, nao ~/Applications/.
APPIMAGE="${APPIMAGE:-$HOME/LIVI/LIVI.AppImage}"
LABWC_DIR="$HOME/.config/labwc"

echo "==> Unidade de servico"
mkdir -p "$UNIT_DIR"
install -m 644 "$REPO_DIR/deployment/livi.service" "$UNIT_DIR/livi.service"
systemctl --user daemon-reload
echo "    $UNIT_DIR/livi.service"

if [[ ! -x "$APPIMAGE" ]]; then
  echo "    AVISO: $APPIMAGE nao existe ou nao e executavel."
  echo "    A unidade fica instalada e a interface mostra 'pronta', mas subir"
  echo "    vai falhar. Instale o LIVI antes - ver docs/projecao.md."
fi

echo
echo "==> Autostart do LIVI"
# O instalador do LIVI cria uma entrada de autostart. Com ela a projecao sobe
# sozinha no boot, por fora do nosso controle, e cobre o painel do motorista.
shopt -s nullglob
autostart=("$HOME/.config/autostart/"*[Ll][Ii][Vv][Ii]*.desktop)
shopt -u nullglob
if (( ${#autostart[@]} )); then
  for entry in "${autostart[@]}"; do
    echo "    ENCONTRADO: $entry"
  done
  echo "    Remova ou renomeie: com autostart a projecao sobe no boot por fora"
  echo "    da interface. Nao removo por voce - e arquivo de outro programa."
else
  echo "    Nenhuma entrada de autostart do LIVI encontrada."
fi

echo
echo "==> Regra de janela do compositor"
echo "    Duas regras: uma prende o LIVI na faixa esquerda, outra prende a"
echo "    nossa propria janela de multimidia na faixa direita - sem a segunda"
echo "    o Wayland deixa a nossa janela flutuante onde o labwc quiser."
if [[ -f "$LABWC_DIR/rc.xml" ]]; then
  echo "    Ja existe $LABWC_DIR/rc.xml."
  echo "    Funda a mao os dois blocos <windowRule> de:"
  echo "      $REPO_DIR/deployment/labwc-rc.xml"
  echo "    Sobrescrever apagaria a sua configuracao do compositor."
else
  mkdir -p "$LABWC_DIR"
  install -m 644 "$REPO_DIR/deployment/labwc-rc.xml" "$LABWC_DIR/rc.xml"
  echo "    Instalado em $LABWC_DIR/rc.xml"
fi

echo
echo "==> Conferir a geometria: os numeros precisam concordar"
fraction="$(systemctl --user show picockpit -p Environment 2>/dev/null \
  | tr ' ' '\n' | sed -n 's/^PICOCKPIT_CONSOLE_FRACTION=//p')"
livi_width="$(sed -n 's/.*ResizeTo" width="\([0-9]*\)".*/\1/p' \
  "$REPO_DIR/deployment/labwc-rc.xml" | sed -n 1p)"
console_width="$(sed -n 's/.*ResizeTo" width="\([0-9]*\)".*/\1/p' \
  "$REPO_DIR/deployment/labwc-rc.xml" | sed -n 2p)"
echo "    PICOCKPIT_CONSOLE_FRACTION      = ${fraction:-0.3 (padrao)}"
echo "    largura da regra do livi        = ${livi_width:-?} px"
echo "    largura da regra da multimidia  = ${console_width:-?} px"
echo "    Num display de 1920 px, os dois devem somar 1920 e a fracao decidir"
echo "    o corte: multimidia = 1920*fracao, projecao = 1920 - isso."

echo
echo "==> Falta conferir o app_id da janela do LIVI"
echo "    Com o LIVI aberto:  lswt -v   ou   labwc com a opcao de depuracao"
echo "    A regra assume 'dev.f-io.livi' (o StartupWMClass que o instalador"
echo "    oficial grava nos atalhos). Se nao for isso, ajuste o identifier na"
echo "    regra do LIVI. App_id errado nao da erro: a regra so nunca casa, e a"
echo "    janela aparece em qualquer lugar. A regra da nossa multimidia casa"
echo "    por titulo, nao depende dessa conferencia."
