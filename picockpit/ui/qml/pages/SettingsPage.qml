// Ajustes.
//
// A tela completa e escopo da Etapa 12. Por ora reune o que ja existe no
// dominio e ainda nao tinha caminho pela interface: tema, combustivel e
// injecao de falhas.
import QtQuick
import ".."
import PiCockpit 1.0

Flickable {
    id: page

    contentHeight: content.implicitHeight + 48
    clip: true

    Column {
        id: content

        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
        spacing: 22

        // ------------------------------------------------------------- tema
        Column {
            spacing: 10

            Text {
                text: qsTr("Tema")
                color: Theme.colors.text
                font { pixelSize: 20; weight: Font.DemiBold }
            }

            Row {
                spacing: 10

                Repeater {
                    model: Theme.available

                    delegate: OptionChip {
                        required property string modelData

                        text: Theme.labelOf(modelData)
                        selected: modelData === Theme.name
                        onActivated: Theme.activate(modelData)
                    }
                }
            }
        }

        Rectangle {
            width: page.width - 48
            height: 1
            color: Theme.colors.surface_alt
        }

        // ------------------------------------------------------ combustivel
        Column {
            spacing: 10
            visible: Settings.simulationControls

            Text {
                text: qsTr("Combustivel")
                color: Theme.colors.text
                font { pixelSize: 20; weight: Font.DemiBold }
            }

            Text {
                text: qsTr("Etanol rende menos por litro e entrega mais torque")
                color: Theme.colors.text_muted
                font.pixelSize: 12
            }

            Row {
                spacing: 10

                Repeater {
                    model: Settings.fuels

                    delegate: OptionChip {
                        required property string modelData

                        text: Settings.fuelLabel(modelData)
                        selected: modelData === Settings.fuel
                        onActivated: Settings.setFuel(modelData)
                    }
                }
            }
        }

        Rectangle {
            width: page.width - 48
            height: 1
            color: Theme.colors.surface_alt
            visible: Settings.simulationControls
        }

        // ---------------------------------------------------------- falhas
        Column {
            spacing: 10
            visible: Settings.simulationControls

            Text {
                text: qsTr("Falhas simuladas")
                color: Theme.colors.text
                font { pixelSize: 20; weight: Font.DemiBold }
            }

            Text {
                text: qsTr("Provoca codigos de diagnostico para testar os alertas do painel")
                color: Theme.colors.text_muted
                font.pixelSize: 12
            }

            Flow {
                width: page.width - 48
                spacing: 8

                Repeater {
                    model: Settings.knownCodes

                    delegate: OptionChip {
                        required property string modelData

                        text: modelData
                        selected: Settings.faultCodes.indexOf(modelData) >= 0
                        accent: Theme.colors.warning
                        onActivated: Settings.injectFault(modelData)
                    }
                }
            }

            Text {
                visible: Settings.faultCodes.length > 0
                width: page.width - 48
                wrapMode: Text.WordWrap
                text: Settings.codeDescription(Settings.faultCodes[Settings.faultCodes.length - 1])
                color: Theme.colors.warning
                font.pixelSize: 12
            }

            ActionButton {
                text: qsTr("APAGAR CODIGOS")
                enabled: Settings.faultCodes.length > 0
                onActivated: Settings.clearFaults()
            }
        }

        Rectangle {
            width: page.width - 48
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
