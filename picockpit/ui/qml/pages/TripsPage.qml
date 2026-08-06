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

    // Totais
    Rectangle {
        id: summary

        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
        height: 62
        radius: 12
        color: Theme.colors.surface
        border.width: 1
        border.color: Theme.colors.surface_alt

        Row {
            anchors { left: parent.left; leftMargin: 20; verticalCenter: parent.verticalCenter }
            spacing: 34

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
                label: qsTr("TEMPO")
                value: Trips.totals.duration || "0 min"
            }

            InfoCell {
                label: qsTr("VIAGENS")
                value: Trips.count.toString()
            }
        }

        ActionButton {
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
            height: 52
            radius: 10
            color: Theme.colors.surface
            border.width: 1
            border.color: Theme.colors.surface_alt

            Row {
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
                spacing: 30

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
                    label: qsTr("DURACAO")
                    value: modelData.duration
                }

                InfoCell {
                    label: qsTr("MEDIA")
                    value: modelData.averageSpeed
                }

                InfoCell {
                    label: qsTr("MAXIMA")
                    value: modelData.maxSpeed
                }

                InfoCell {
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
