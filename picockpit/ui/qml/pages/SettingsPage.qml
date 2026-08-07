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
            width: page.width - 48
            spacing: 10

            Text {
                text: qsTr("Tema")
                color: Theme.colors.text
                font { pixelSize: 20; weight: Font.DemiBold }
            }

            SectionNote {
                text: qsTr("Cada modo desenha o proprio instrumento: abertura, espessura e segmentacao mudam junto com a cor")
            }

            // Flow e nao Row: na coluna estreita da multimidia dividida cinco
            // previas de 132 px nao cabem lado a lado, e uma Row as empurraria
            // para fora da tela em silencio.
            Flow {
                width: parent.width
                spacing: 10

                Repeater {
                    model: Theme.available

                    delegate: ThemeSwatch {
                        required property string modelData

                        themeName: modelData
                        selected: modelData === Theme.name
                        onActivated: Settings.setTheme(modelData)
                    }
                }
            }
        }

        Rectangle {
            width: page.width - 48
            height: 1
            color: Theme.colors.surface_alt
        }

        // -------------------------------------------------------- unidades
        Column {
            width: page.width - 48
            spacing: 10

            Text {
                text: qsTr("Unidades")
                color: Theme.colors.text
                font { pixelSize: 20; weight: Font.DemiBold }
            }

            SectionNote {
                text: qsTr("Os dados sao sempre guardados em unidade metrica; a troca afeta so a exibicao")
            }

            Row {
                spacing: 10

                Repeater {
                    model: Settings.unitOptions

                    delegate: OptionChip {
                        required property string modelData

                        text: modelData === "metric" ? qsTr("Metrico") : qsTr("Imperial")
                        selected: modelData === Settings.units
                        onActivated: Settings.setUnits(modelData)
                    }
                }
            }
        }

        Rectangle {
            width: page.width - 48
            height: 1
            color: Theme.colors.surface_alt
        }

        // ---------------------------------------------------------- tela
        Column {
            width: page.width - 48
            spacing: 10

            Text {
                text: qsTr("Tela")
                color: Theme.colors.text
                font { pixelSize: 20; weight: Font.DemiBold }
            }

            SectionNote {
                text: qsTr("Escala da interface")
            }

            Row {
                spacing: 10

                Repeater {
                    model: Settings.scaleOptions

                    delegate: OptionChip {
                        required property real modelData

                        text: Math.round(modelData * 100) + "%"
                        selected: Math.abs(modelData - Settings.uiScale) < 0.01
                        onActivated: Settings.setUiScale(modelData)
                    }
                }
            }

            SectionNote {
                text: qsTr("Quadros por segundo alvo")
            }

            Row {
                spacing: 10

                Repeater {
                    model: Settings.fpsOptions

                    delegate: OptionChip {
                        required property int modelData

                        text: modelData + " fps"
                        selected: modelData === Settings.targetFps
                        onActivated: Settings.setTargetFps(modelData)
                    }
                }
            }

            SectionNote {
                text: qsTr("O alvo de quadros passa a valer na proxima inicializacao")
                font.pixelSize: 11
            }
        }

        Rectangle {
            width: page.width - 48
            height: 1
            color: Theme.colors.surface_alt
        }

        // ---------------------------------------------------- tela dividida
        Column {
            width: page.width - 48
            spacing: 10

            Text {
                text: qsTr("Tela dividida")
                color: Theme.colors.text
                font { pixelSize: 20; weight: Font.DemiBold }
            }

            SectionNote {
                text: qsTr("A pagina escolhida na trilha ocupa a regiao principal")
            }

            Row {
                spacing: 10

                OptionChip {
                    text: qsTr("Desligada")
                    selected: !Layout.split
                    onActivated: Layout.setSplit(false)
                }

                Repeater {
                    model: Layout.ratioOptions

                    delegate: OptionChip {
                        required property var modelData

                        text: modelData.label
                        selected: Layout.split && Math.abs(modelData.value - Layout.ratio) < 0.01
                        onActivated: {
                            Layout.setRatio(modelData.value)
                            Layout.setSplit(true)
                        }
                    }
                }
            }

            SectionNote {
                text: qsTr("Pagina da regiao secundaria")
                visible: Layout.split
            }

            Flow {
                width: page.width - 48
                spacing: 8
                visible: Layout.split

                Repeater {
                    model: Layout.splittablePages

                    delegate: OptionChip {
                        required property string modelData

                        text: Layout.labelOf(modelData)
                        selected: modelData === Layout.secondary
                        onActivated: Layout.setSecondary(modelData)
                    }
                }
            }
        }

        Rectangle {
            width: page.width - 48
            height: 1
            color: Theme.colors.surface_alt
        }

        // --------------------------------------------------------- widgets
        Column {
            width: page.width - 48
            spacing: 10

            Text {
                text: qsTr("Widgets")
                color: Theme.colors.text
                font { pixelSize: 20; weight: Font.DemiBold }
            }

            SectionNote {
                text: qsTr("Cada widget e independente; ligue e desligue a vontade")
            }

            Flow {
                width: page.width - 48
                spacing: 8

                Repeater {
                    model: Layout.availableWidgets

                    delegate: OptionChip {
                        required property var modelData

                        text: modelData.label
                        selected: Layout.widgets.indexOf(modelData.key) >= 0
                        onActivated: Layout.toggleWidget(modelData.key)
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
            width: page.width - 48
            spacing: 10
            visible: Settings.simulationControls

            Text {
                text: qsTr("Combustivel")
                color: Theme.colors.text
                font { pixelSize: 20; weight: Font.DemiBold }
            }

            SectionNote {
                text: qsTr("Etanol rende menos por litro e entrega mais torque")
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
            width: page.width - 48
            spacing: 10
            visible: Settings.simulationControls

            Text {
                text: qsTr("Falhas simuladas")
                color: Theme.colors.text
                font { pixelSize: 20; weight: Font.DemiBold }
            }

            SectionNote {
                text: qsTr("Provoca codigos de diagnostico para testar os alertas do painel")
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

        ActionButton {
            text: qsTr("RESTAURAR PADROES")
            onActivated: Settings.restoreDefaults()
        }

        // Largura explicita tambem aqui: uma Column sem largura assume a do
        // maior filho, e um filho que le `parent.width` para se dimensionar
        // fecharia um laco de binding.
        Column {
            width: page.width - 48
            spacing: 6

            SectionNote {
                text: qsTr("Versao %1 - ambiente %2").arg(AppInfo.version).arg(AppInfo.env)
                font.pixelSize: 14
            }

            SectionNote {
                text: qsTr("F11 alterna tela cheia - Ctrl+Q encerra")
                font.pixelSize: 14
            }
        }
    }
}
