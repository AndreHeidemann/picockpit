// Cartao de conteudo reutilizado pelas paginas ainda nao implementadas.
// Existe para que a navegacao e o tema possam ser validados na Etapa 1 sem
// antecipar funcionalidade das etapas seguintes.
import QtQuick

Item {
    id: page

    property string heading: ""
    property string subtitle: ""
    property string stage: ""

    Rectangle {
        anchors { fill: parent; margins: 24 }
        radius: 16
        color: Theme.colors.surface
        border.width: 1
        border.color: Theme.colors.surface_alt

        Column {
            anchors.centerIn: parent
            spacing: 10

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: page.heading
                color: Theme.colors.text
                font { pixelSize: 32; weight: Font.DemiBold }
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: page.subtitle
                color: Theme.colors.text_muted
                font.pixelSize: 16
            }

            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                width: stageLabel.implicitWidth + 24
                height: stageLabel.implicitHeight + 12
                radius: 6
                color: Theme.colors.surface_alt

                Text {
                    id: stageLabel
                    anchors.centerIn: parent
                    text: page.stage
                    color: Theme.colors.primary
                    font { pixelSize: 13; weight: Font.Medium; letterSpacing: 0.8 }
                }
            }
        }
    }
}
