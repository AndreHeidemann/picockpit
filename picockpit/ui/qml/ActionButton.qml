// Botao de toque com alvo grande o bastante para uso com o carro em movimento.
import QtQuick
import PiCockpit 1.0

Rectangle {
    id: button

    property string text: ""
    property bool highlighted: false
    property bool enabled: true

    signal activated()

    implicitWidth: label.implicitWidth + 36
    implicitHeight: 44
    radius: 10

    color: highlighted ? Theme.colors.surface_alt : "transparent"
    border.width: 1
    border.color: highlighted ? Theme.colors.primary : Theme.colors.surface_alt
    opacity: enabled ? 1.0 : 0.35

    Text {
        id: label

        anchors.centerIn: parent
        text: button.text
        color: button.highlighted ? Theme.colors.primary : Theme.colors.text
        font { pixelSize: 14; weight: Font.DemiBold; letterSpacing: 1.0 }
    }

    MouseArea {
        anchors.fill: parent
        enabled: button.enabled
        onClicked: button.activated()
        onPressed: button.scale = 0.96
        onReleased: button.scale = 1.0
        onCanceled: button.scale = 1.0
    }

    Behavior on scale {
        NumberAnimation { duration: 90 }
    }
}
