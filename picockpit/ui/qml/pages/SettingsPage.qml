// Ajustes. A tela completa e escopo da Etapa 12; aqui apenas a troca de tema,
// que ja valida a ponte Python -> QML de ponta a ponta.
import QtQuick
import PiCockpit 1.0

Item {
    id: page

    Column {
        anchors { fill: parent; margins: 24 }
        spacing: 20

        Text {
            text: qsTr("Tema")
            color: Theme.colors.text
            font { pixelSize: 22; weight: Font.DemiBold }
        }

        Row {
            spacing: 12

            Repeater {
                model: Theme.available

                delegate: Rectangle {
                    required property string modelData

                    width: 124
                    height: 56
                    radius: 12
                    color: modelData === Theme.name ? Theme.colors.surface_alt : Theme.colors.surface
                    border.width: modelData === Theme.name ? 2 : 1
                    border.color: modelData === Theme.name
                        ? Theme.colors.primary
                        : Theme.colors.surface_alt

                    Behavior on color {
                        ColorAnimation { duration: 120 }
                    }

                    Text {
                        anchors.centerIn: parent
                        text: Theme.labelOf(modelData)
                        color: modelData === Theme.name ? Theme.colors.text : Theme.colors.text_muted
                        font { pixelSize: 15; weight: Font.Medium }
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: Theme.activate(modelData)
                    }
                }
            }
        }

        Rectangle {
            width: parent.width
            height: 1
            color: Theme.colors.surface_alt
        }

        Column {
            spacing: 6

            Text {
                text: qsTr("Versao %1 - ambiente %2").arg(AppInfo.version).arg(AppInfo.env)
                color: Theme.colors.text_muted
                font.pixelSize: 14
            }

            Text {
                text: qsTr("F11 alterna tela cheia - Ctrl+Q encerra")
                color: Theme.colors.text_muted
                font.pixelSize: 14
            }
        }
    }
}
