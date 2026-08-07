// Graficos em tempo real dos sinais que mais mudam.
//
// Janela de 60 segundos, redesenho a 10 Hz. A telemetria chega a 20 Hz, mas
// dobrar a taxa de desenho nao acrescenta informacao visivel e gasta GPU que o
// painel precisa manter livre.
import QtQuick
import ".."
import PiCockpit 1.0

Item {
    id: page

    // Coluna unica quando estreita: dois graficos lado a lado numa faixa de
    // 30% da tela nao mostram forma nenhuma, so ruido.
    readonly property int columns: width < 620 ? 1 : 2
    readonly property int rows: 4 / columns
    readonly property real cellWidth: (width - 48 - (columns - 1) * 12) / columns
    readonly property real cellHeight: (height - 48 - (rows - 1) * 12) / rows

    Grid {
        anchors { fill: parent; margins: 24 }
        columns: page.columns
        spacing: 12

        LineChart {
            width: page.cellWidth
            height: page.cellHeight
            signalName: "speed"
            label: qsTr("VELOCIDADE")
            accent: Theme.colors.primary
        }

        LineChart {
            width: page.cellWidth
            height: page.cellHeight
            signalName: "rpm"
            label: qsTr("ROTACAO")
            accent: Theme.colors.danger
        }

        LineChart {
            width: page.cellWidth
            height: page.cellHeight
            signalName: "consumption"
            label: qsTr("CONSUMO")
            accent: Theme.colors.success
            decimals: 1
        }

        LineChart {
            width: page.cellWidth
            height: page.cellHeight
            signalName: "engine_load"
            label: qsTr("CARGA DO MOTOR")
            accent: Theme.colors.warning
        }
    }
}
