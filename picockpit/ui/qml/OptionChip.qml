// Opcao selecionavel em linha, com alvo de toque generoso.
import QtQuick
import PiCockpit 1.0

Rectangle {
    id: chip

    property string text: ""
    property bool selected: false
    property color accent: Theme.colors.primary

    signal activated()

    implicitWidth: label.implicitWidth + 32
    implicitHeight: 48
    radius: 10

    color: selected ? Theme.colors.surface_alt : Theme.colors.surface
    border.width: selected ? 2 : 1
    border.color: selected ? chip.accent : Theme.colors.surface_alt

    Behavior on color {
        ColorAnimation { duration: 120 }
    }

    Text {
        id: label

        anchors.centerIn: parent
        text: chip.text
        color: chip.selected ? Theme.colors.text : Theme.colors.text_muted
        font { pixelSize: 14; weight: Font.Medium }
    }

    MouseArea {
        anchors.fill: parent
        onClicked: chip.activated()
    }
}
