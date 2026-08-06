// Medidor de FPS baseado em frames efetivamente renderizados.
// So tem significado quando medido no hardware real do Pi 5.
import QtQuick
import PiCockpit 1.0

Row {
    id: counter

    property int target: 60
    property int fps: 0

    readonly property color statusColor: fps >= target * 0.9
        ? Theme.colors.success
        : (fps >= target * 0.6 ? Theme.colors.warning : Theme.colors.danger)

    spacing: 6

    FrameAnimation {
        id: frames
        running: true
        property int count: 0
        onTriggered: count += 1
    }

    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: {
            counter.fps = frames.count
            frames.count = 0
            AppInfo.reportFps(counter.fps)
        }
    }

    Rectangle {
        anchors.verticalCenter: parent.verticalCenter
        width: 8
        height: 8
        radius: 4
        color: counter.statusColor
    }

    Text {
        anchors.verticalCenter: parent.verticalCenter
        text: counter.fps + " fps"
        color: Theme.colors.text_muted
        font { pixelSize: 14; weight: Font.Medium }
    }
}
