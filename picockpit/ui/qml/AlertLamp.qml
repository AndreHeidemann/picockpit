// Luz de alerta. Apagada fica discreta; acesa ganha cor e leve pulsacao,
// como as luzes espia de um painel real.
import QtQuick
import PiCockpit 1.0

Item {
    id: lamp

    property bool active: false
    property string glyph: ""
    property string text: ""
    property color activeColor: Theme.colors.danger

    implicitWidth: content.implicitWidth + 20
    implicitHeight: 28

    Rectangle {
        anchors.fill: parent
        radius: 6
        color: lamp.active ? Qt.rgba(1, 1, 1, 0.06) : "transparent"
        border.width: lamp.active ? 1 : 0
        border.color: lamp.activeColor
        opacity: lamp.active ? 1 : 0

        Behavior on opacity {
            NumberAnimation { duration: 180 }
        }
    }

    Row {
        id: content

        anchors.centerIn: parent
        spacing: 6
        opacity: lamp.active ? 1 : 0.18

        Behavior on opacity {
            NumberAnimation { duration: 180 }
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: lamp.glyph
            color: lamp.active ? lamp.activeColor : Theme.colors.text_muted
            font.pixelSize: 15
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: lamp.text
            color: lamp.active ? lamp.activeColor : Theme.colors.text_muted
            font { pixelSize: 12; weight: Font.DemiBold; letterSpacing: 0.8 }
        }
    }

    SequentialAnimation {
        running: lamp.active
        loops: Animation.Infinite

        NumberAnimation { target: content; property: "opacity"; to: 0.45; duration: 700 }
        NumberAnimation { target: content; property: "opacity"; to: 1.0; duration: 700 }
    }
}
