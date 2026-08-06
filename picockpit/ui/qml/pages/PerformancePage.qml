// Desempenho: cronometro de arrancada e cronometro de volta.
//
// O 0-100 dispara sozinho, a partir do proprio fluxo de velocidade. A volta e
// marcada a mao porque sem GPS nao existe linha de chegada - quando houver GPS,
// so o disparo muda, o resto continua igual.
import QtQuick
import ".."
import PiCockpit 1.0

Item {
    id: page

    Row {
        anchors {
            fill: parent
            margins: 24
        }
        spacing: 24

        // Arrancada
        Rectangle {
            width: (page.width - 72) / 2
            height: parent.height
            radius: 16
            color: Theme.colors.surface
            border.width: 1
            border.color: Theme.colors.surface_alt

            Column {
                anchors {
                    left: parent.left
                    right: parent.right
                    top: parent.top
                    margins: 20
                }
                spacing: 4

                Text {
                    text: qsTr("ARRANCADA 0-100 km/h")
                    color: Theme.colors.text_muted
                    font { pixelSize: 12; weight: Font.DemiBold; letterSpacing: 1.4 }
                }

                Text {
                    text: Chrono.accelRunning ? Chrono.accelElapsed : Chrono.accelLast
                    color: Chrono.accelRunning ? Theme.colors.primary : Theme.colors.text
                    font { pixelSize: Math.round(page.height * 0.30); weight: Font.Light }
                }

                Text {
                    text: Chrono.accelRunning
                        ? qsTr("medindo...")
                        : qsTr("ultima medicao")
                    color: Theme.colors.text_muted
                    font.pixelSize: 12
                }

                Item {
                    width: 1
                    height: 10
                }

                Row {
                    spacing: 8

                    Text {
                        text: qsTr("MELHOR")
                        color: Theme.colors.text_muted
                        font { pixelSize: 12; weight: Font.Medium; letterSpacing: 1.0 }
                    }

                    Text {
                        text: Chrono.accelBest
                        color: Theme.colors.success
                        font { pixelSize: 16; weight: Font.DemiBold }
                    }
                }
            }
        }

        // Voltas
        Rectangle {
            width: (page.width - 72) / 2
            height: parent.height
            radius: 16
            color: Theme.colors.surface
            border.width: 1
            border.color: Theme.colors.surface_alt

            Column {
                anchors {
                    left: parent.left
                    right: parent.right
                    top: parent.top
                    margins: 20
                }
                spacing: 4

                Text {
                    text: qsTr("VOLTA") + (Chrono.lapCount > 0 ? "  ·  " + Chrono.lapCount : "")
                    color: Theme.colors.text_muted
                    font { pixelSize: 12; weight: Font.DemiBold; letterSpacing: 1.4 }
                }

                Text {
                    text: Chrono.lapRunning ? Chrono.lapCurrent : Chrono.lapLast
                    color: Chrono.lapRunning ? Theme.colors.primary : Theme.colors.text
                    font { pixelSize: Math.round(page.height * 0.30); weight: Font.Light }
                }

                Row {
                    spacing: 16

                    Row {
                        spacing: 6

                        Text {
                            text: qsTr("ULTIMA")
                            color: Theme.colors.text_muted
                            font { pixelSize: 11; weight: Font.Medium; letterSpacing: 1.0 }
                        }

                        Text {
                            text: Chrono.lapLast
                            color: Theme.colors.text
                            font { pixelSize: 14; weight: Font.DemiBold }
                        }
                    }

                    Row {
                        spacing: 6

                        Text {
                            text: qsTr("MELHOR")
                            color: Theme.colors.text_muted
                            font { pixelSize: 11; weight: Font.Medium; letterSpacing: 1.0 }
                        }

                        Text {
                            text: Chrono.lapBest
                            color: Theme.colors.success
                            font { pixelSize: 14; weight: Font.DemiBold }
                        }
                    }
                }

                Item {
                    width: 1
                    height: 12
                }

                Row {
                    spacing: 10

                    ActionButton {
                        text: Chrono.lapRunning ? qsTr("VOLTA") : qsTr("INICIAR")
                        highlighted: true
                        onActivated: Chrono.toggleLap()
                    }

                    ActionButton {
                        text: qsTr("PARAR")
                        enabled: Chrono.lapRunning
                        onActivated: Chrono.stopLap()
                    }

                    ActionButton {
                        text: qsTr("ZERAR")
                        onActivated: Chrono.resetAll()
                    }
                }
            }
        }
    }
}
