// Historico de viagens.
//
// Uma linha por trecho rodado. O que fica gravado e o resumo, nao a serie de
// amostras: registrar amostra a amostra encheria o cartao de escrita continua
// sem produzir nada que se va consultar.
import QtQuick
import ".."
import PiCockpit 1.0

Item {
    id: page

    // Mesma regra do painel: numa coluna estreita, o que sai sao as leituras
    // secundarias, e nao o tamanho de todo mundo.
    readonly property bool narrow: width < 720
    readonly property bool veryNarrow: width < 520

    // Totais
    Rectangle {
        id: summary

        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
        height: page.narrow ? 86 : 62
        radius: 12
        color: Theme.colors.surface
        border.width: 1
        border.color: Theme.colors.surface_alt

        Flow {
            anchors {
                left: parent.left
                right: clearButton.left
                verticalCenter: parent.verticalCenter
                leftMargin: 20
                rightMargin: 12
            }
            spacing: page.narrow ? 16 : 34

            InfoCell {
                label: qsTr("TOTAL RODADO")
                value: Trips.totals.distance || "0,0 km"
            }

            InfoCell {
                label: qsTr("COMBUSTIVEL")
                value: Trips.totals.fuel || "0,0 L"
            }

            InfoCell {
                label: qsTr("MEDIA GERAL")
                value: Trips.totals.consumption || "0,0 km/L"
            }

            InfoCell {
                visible: !page.veryNarrow
                label: qsTr("TEMPO")
                value: Trips.totals.duration || "0 min"
            }

            InfoCell {
                visible: !page.narrow
                label: qsTr("VIAGENS")
                value: Trips.count.toString()
            }
        }

        ActionButton {
            id: clearButton

            anchors {
                right: parent.right
                rightMargin: 14
                verticalCenter: parent.verticalCenter
            }
            text: qsTr("APAGAR")
            enabled: Trips.count > 0
            onActivated: Trips.clearHistory()
        }
    }

    ListView {
        anchors {
            left: parent.left
            right: parent.right
            top: summary.bottom
            bottom: parent.bottom
            margins: 20
            topMargin: 10
        }
        clip: true
        spacing: 8
        model: Trips.trips

        delegate: Rectangle {
            required property var modelData

            width: ListView.view.width
            height: page.narrow ? 74 : 52
            radius: 10
            color: Theme.colors.surface
            border.width: 1
            border.color: Theme.colors.surface_alt

            Flow {
                // Termina onde os codigos de falha comecam: sem isso a ultima
                // coluna passa por baixo deles.
                anchors {
                    left: parent.left
                    right: faultCodes.left
                    leftMargin: 18
                    rightMargin: 12
                    verticalCenter: parent.verticalCenter
                }
                clip: true
                spacing: page.narrow ? 14 : 30

                InfoCell {
                    label: qsTr("QUANDO")
                    value: modelData.date
                }

                InfoCell {
                    label: qsTr("DISTANCIA")
                    value: modelData.distance
                }

                InfoCell {
                    label: qsTr("CONSUMO")
                    value: modelData.consumption
                }

                InfoCell {
                    visible: !page.veryNarrow
                    label: qsTr("DURACAO")
                    value: modelData.duration
                }

                InfoCell {
                    visible: !page.narrow
                    label: qsTr("MEDIA")
                    value: modelData.averageSpeed
                }

                InfoCell {
                    visible: !page.narrow
                    label: qsTr("MAXIMA")
                    value: modelData.maxSpeed
                }

                InfoCell {
                    visible: !page.veryNarrow
                    label: qsTr("GASTO")
                    value: modelData.fuelUsed
                }
            }

            Text {
                id: faultCodes

                anchors {
                    right: parent.right
                    rightMargin: 18
                    verticalCenter: parent.verticalCenter
                }
                visible: modelData.faults.length > 0
                text: modelData.faults.join("  ")
                color: Theme.colors.warning
                font { pixelSize: 12; weight: Font.DemiBold }
            }
        }
    }

    Text {
        anchors.centerIn: parent
        visible: Trips.count === 0
        text: qsTr("Nenhuma viagem registrada ainda")
        color: Theme.colors.text_muted
        font.pixelSize: 14
    }
}
