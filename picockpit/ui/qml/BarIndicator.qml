// Barra horizontal fina para grandezas de variacao lenta: combustivel e
// temperatura. Ocupa pouco espaco e nao compete com os arcos principais.
import QtQuick
import PiCockpit 1.0

Item {
    id: bar

    property real value: 0
    property real minimum: 0
    property real maximum: 100
    property string label: ""
    property string glyph: ""
    property bool alert: false
    property color accent: Theme.colors.primary

    readonly property real fraction: maximum > minimum
        ? Math.max(0, Math.min(1, (value - minimum) / (maximum - minimum)))
        : 0

    implicitHeight: 42

    Behavior on value {
        NumberAnimation { duration: 250; easing.type: Easing.OutQuad }
    }

    Row {
        anchors { left: parent.left; right: parent.right; top: parent.top }
        spacing: 8

        Text {
            text: bar.glyph
            color: bar.alert ? Theme.colors.danger : Theme.colors.text_muted
            font.pixelSize: 14
        }

        Text {
            text: bar.label
            color: bar.alert ? Theme.colors.danger : Theme.colors.text_muted
            font { pixelSize: 12; weight: Font.Medium; letterSpacing: 1.0 }
        }
    }

    Rectangle {
        id: track

        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: 6
        radius: 3
        color: Theme.colors.surface_alt

        Rectangle {
            width: track.width * bar.fraction
            height: parent.height
            radius: parent.radius
            color: bar.alert ? Theme.colors.danger : bar.accent

            Behavior on color {
                ColorAnimation { duration: 200 }
            }
        }
    }
}
