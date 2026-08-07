// Linha de explicacao sob um titulo de secao.
//
// Existe por um defeito real: os textos de apoio dos Ajustes eram `Text` sem
// largura, e `Text` sem largura nao quebra linha - ele cresce ate onde
// precisar e some por baixo da borda. Na multimidia dividida, que e onde os
// Ajustes vivem, a coluna e estreita e metade das frases estava cortada.
//
// A largura vem do pai, entao toda secao que usa isto precisa ter largura
// propria. Uma `Column` sem largura explicita assume a do maior filho, o que
// tornaria a conta circular.
import QtQuick
import PiCockpit 1.0

Text {
    width: parent ? parent.width : implicitWidth
    color: Theme.colors.text_muted
    font.pixelSize: 12
    wrapMode: Text.WordWrap
}
