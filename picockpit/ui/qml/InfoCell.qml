// Leitura secundaria compacta: rotulo pequeno em cima, valor embaixo.
// Usada na faixa de informacoes do painel, onde cabe muita grandeza e sobra
// pouco espaco.
import QtQuick
import PiCockpit 1.0

Column {
    id: cell

    property string label: ""
    property string value: ""
    property bool alert: false

    spacing: 1

    Text {
        text: cell.label
        color: Theme.colors.text_muted
        font { pixelSize: 10; weight: Font.Medium; letterSpacing: 0.8 }
    }

    Text {
        text: cell.value
        color: cell.alert ? Theme.colors.danger : Theme.colors.text
        font { pixelSize: 15; weight: Font.Medium }
    }
}
