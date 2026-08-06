// Trilha de navegacao lateral, dimensionada para toque (alvos de 72 px).
import QtQuick

Rectangle {
    id: rail

    property var model: []
    property int currentIndex: 0

    signal selected(int index)

    color: Theme.colors.surface

    Rectangle {
        anchors { top: parent.top; bottom: parent.bottom; right: parent.right }
        width: 1
        color: Theme.colors.surface_alt
    }

    Column {
        anchors { top: parent.top; topMargin: 16; horizontalCenter: parent.horizontalCenter }
        spacing: 8

        Repeater {
            model: rail.model

            delegate: Item {
                required property int index
                required property var modelData

                width: rail.width
                height: 72

                Rectangle {
                    anchors.centerIn: parent
                    width: 72
                    height: 60
                    radius: 12
                    color: index === rail.currentIndex ? Theme.colors.surface_alt : "transparent"
                    border.width: index === rail.currentIndex ? 1 : 0
                    border.color: Theme.colors.primary

                    Behavior on color {
                        ColorAnimation { duration: 120 }
                    }
                }

                Column {
                    anchors.centerIn: parent
                    spacing: 4

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: modelData.glyph
                        font.pixelSize: 22
                        color: index === rail.currentIndex
                            ? Theme.colors.primary
                            : Theme.colors.text_muted
                    }

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: modelData.label
                        font { pixelSize: 12; weight: Font.Medium }
                        color: index === rail.currentIndex
                            ? Theme.colors.text
                            : Theme.colors.text_muted
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: rail.selected(index)
                }
            }
        }
    }
}
