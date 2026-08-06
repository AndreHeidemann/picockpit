// Moldura comum dos widgets: rotulo pequeno, valor grande, unidade discreta.
//
// Todo widget desenha dentro desta moldura para que ligar e desligar qualquer
// combinacao continue produzindo uma grade coerente.
import QtQuick
import PiCockpit 1.0

Rectangle {
    id: card

    property string label: ""
    property string value: "--"
    property string unit: ""
    property color accent: Theme.colors.primary
    property bool alert: false

    radius: 12
    color: Theme.colors.surface
    border.width: 1
    border.color: alert ? Theme.colors.danger : Theme.colors.surface_alt

    Behavior on border.color {
        ColorAnimation { duration: 160 }
    }

    Text {
        anchors { left: parent.left; top: parent.top; margins: 12 }
        text: card.label
        color: Theme.colors.text_muted
        font { pixelSize: 11; weight: Font.DemiBold; letterSpacing: 1.2 }
    }

    Row {
        anchors.centerIn: parent
        spacing: 6

        Text {
            anchors.baseline: unitLabel.baseline
            text: card.value
            color: card.alert ? Theme.colors.danger : card.accent
            font { pixelSize: Math.round(card.height * 0.34); weight: Font.Light }
        }

        Text {
            id: unitLabel

            anchors.bottom: parent.bottom
            text: card.unit
            color: Theme.colors.text_muted
            font { pixelSize: 12; weight: Font.Medium }
        }
    }
}
