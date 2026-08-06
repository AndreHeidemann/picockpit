// Barra superior: titulo da pagina, relogio e contador de FPS.
import QtQuick
import PiCockpit 1.0

Rectangle {
    id: bar

    property string title: ""

    color: Theme.colors.surface

    Rectangle {
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: 1
        color: Theme.colors.surface_alt
    }

    Text {
        anchors { left: parent.left; leftMargin: 24; verticalCenter: parent.verticalCenter }
        text: bar.title
        color: Theme.colors.text
        font { pixelSize: 20; weight: Font.DemiBold; letterSpacing: 0.5 }
    }

    Row {
        anchors { right: parent.right; rightMargin: 24; verticalCenter: parent.verticalCenter }
        spacing: 20

        FpsCounter {
            anchors.verticalCenter: parent.verticalCenter
            target: AppInfo.targetFps
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: Qt.formatTime(clock.now, "HH:mm")
            color: Theme.colors.text
            font { pixelSize: 20; weight: Font.Medium }
        }
    }

    Item {
        id: clock
        property date now: new Date()
        Timer {
            interval: 1000
            running: true
            repeat: true
            onTriggered: clock.now = new Date()
        }
    }
}
