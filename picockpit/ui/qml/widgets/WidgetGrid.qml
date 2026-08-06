// Grade de widgets ativos.
//
// Cada widget le apenas dos singletons expostos pelo Python; nenhum conhece o
// outro. E o que permite ligar, desligar e reordenar sem tocar em codigo.
import QtQuick
import PiCockpit 1.0

Item {
    id: grid

    readonly property var active: Layout.widgets
    readonly property int columns: Math.max(1, Math.min(4, Math.floor(width / 210)))
    readonly property int rows: Math.max(1, Math.ceil(active.length / columns))
    readonly property real cellWidth: (width - 24 - (columns - 1) * 10) / columns
    readonly property real cellHeight: Math.min(
        120, (height - 24 - (rows - 1) * 10) / rows)

    Flow {
        anchors { fill: parent; margins: 12 }
        spacing: 10

        Repeater {
            model: grid.active

            delegate: Loader {
                required property string modelData

                width: grid.cellWidth
                height: grid.cellHeight

                sourceComponent: {
                    switch (modelData) {
                    case "speed":       return speedWidget
                    case "rpm":         return rpmWidget
                    case "consumption": return consumptionWidget
                    case "range":       return rangeWidget
                    case "fuel":        return fuelWidget
                    case "temperature": return temperatureWidget
                    case "voltage":     return voltageWidget
                    case "odometer":    return odometerWidget
                    case "clock":       return clockWidget
                    case "gps":         return gpsWidget
                    default:            return null
                    }
                }
            }
        }
    }

    Text {
        anchors.centerIn: parent
        visible: grid.active.length === 0
        text: qsTr("Nenhum widget ativo. Escolha em Ajustes.")
        color: Theme.colors.text_muted
        font.pixelSize: 14
    }

    Component {
        id: speedWidget
        WidgetCard {
            label: qsTr("VELOCIDADE")
            value: Math.round(Telemetry.speed).toString()
            unit: Telemetry.speedUnit
        }
    }

    Component {
        id: rpmWidget
        WidgetCard {
            label: qsTr("ROTACAO")
            value: Math.round(Telemetry.rpm).toString()
            unit: "rpm"
            accent: Theme.colors.danger
            alert: Telemetry.rpm >= 5500
        }
    }

    Component {
        id: consumptionWidget
        WidgetCard {
            label: qsTr("CONSUMO")
            value: (Telemetry.moving ? Telemetry.consumption : Telemetry.fuelRate).toFixed(1)
            unit: Telemetry.moving ? Telemetry.consumptionUnit : Telemetry.fuelRateUnit
            accent: Theme.colors.success
        }
    }

    Component {
        id: rangeWidget
        WidgetCard {
            label: qsTr("AUTONOMIA")
            value: Math.round(Telemetry.range).toString()
            unit: Telemetry.distanceUnit
            alert: Telemetry.lowFuel
        }
    }

    Component {
        id: fuelWidget
        WidgetCard {
            label: qsTr("COMBUSTIVEL")
            value: Math.round(Telemetry.fuelLevel).toString()
            unit: "%"
            accent: Theme.colors.success
            alert: Telemetry.lowFuel
        }
    }

    Component {
        id: temperatureWidget
        WidgetCard {
            label: qsTr("MOTOR")
            value: Math.round(Telemetry.coolantTemp).toString()
            unit: "°" + Telemetry.temperatureUnit
            accent: Theme.colors.warning
            alert: Telemetry.overheating
        }
    }

    Component {
        id: voltageWidget
        WidgetCard {
            label: qsTr("BATERIA")
            value: Telemetry.voltage.toFixed(1)
            unit: "V"
            alert: Telemetry.lowVoltage
        }
    }

    Component {
        id: odometerWidget
        WidgetCard {
            label: qsTr("HODOMETRO")
            value: Telemetry.odometer.toFixed(1)
            unit: Telemetry.distanceUnit
        }
    }

    Component {
        id: clockWidget
        WidgetCard {
            label: qsTr("RELOGIO")
            value: Qt.formatTime(clock.now, "HH:mm")
            unit: Qt.formatDateTime(clock.now, "dd/MM")

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
    }

    Component {
        id: gpsWidget
        WidgetCard {
            // Placeholder honesto: o receptor GPS e expansao futura, e o
            // widget existe para a grade ja prever o espaco dele.
            label: qsTr("GPS")
            value: "--"
            unit: qsTr("sem receptor")
            accent: Theme.colors.secondary
        }
    }
}
