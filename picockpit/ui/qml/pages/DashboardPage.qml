// Painel digital.
//
// Composicao inspirada nos clusters da familia BMW IDCevo: fundo quase preto,
// dois arcos abertos na base flanqueando uma leitura numerica central de peso
// leve, informacao secundaria em barras finas na borda inferior. Nenhum
// elemento grafico e copiado - a linguagem visual e a referencia, o desenho
// e nosso.
import QtQuick
import ".."
import PiCockpit 1.0

Item {
    id: dashboard

    readonly property real sideGaugeSize: Math.min(height * 0.72, 280)

    // Conta-giros a esquerda.
    ArcGauge {
        id: tachometer

        anchors {
            left: parent.left
            leftMargin: 32
            verticalCenter: parent.verticalCenter
            verticalCenterOffset: -14
        }
        width: dashboard.sideGaugeSize
        height: dashboard.sideGaugeSize

        value: Telemetry.rpm
        minimum: 0
        maximum: 7000
        warningFrom: 5500
        thickness: 12
        label: qsTr("RPM")
        units: "rpm"
    }

    // Carga do motor a direita: e o sinal que melhor traduz esforco
    // instantaneo, e existe tanto no simulador quanto no OBD-II real.
    ArcGauge {
        id: loadGauge

        anchors {
            right: parent.right
            rightMargin: 32
            verticalCenter: parent.verticalCenter
            verticalCenterOffset: -14
        }
        width: dashboard.sideGaugeSize
        height: dashboard.sideGaugeSize

        value: Telemetry.engineLoad
        minimum: 0
        maximum: 100
        thickness: 12
        label: qsTr("CARGA")
        units: "%"
        accent: Theme.colors.secondary
    }

    // Bloco central: velocidade e marcha.
    Column {
        id: center

        anchors {
            horizontalCenter: parent.horizontalCenter
            verticalCenter: parent.verticalCenter
            verticalCenterOffset: -24
        }
        spacing: -6

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Math.round(Telemetry.speed)
            color: Theme.colors.text
            font { pixelSize: Math.round(dashboard.height * 0.34); weight: Font.Light }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "km/h"
            color: Theme.colors.text_muted
            font { pixelSize: 15; weight: Font.Medium; letterSpacing: 2.0 }
        }

        Item {
            width: 1
            height: 12
        }

        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 54
            height: 40
            radius: 10
            color: Theme.colors.surface
            border.width: 1
            border.color: Theme.colors.surface_alt

            Text {
                anchors.centerIn: parent
                text: Telemetry.gearLabel
                color: Theme.colors.primary
                font { pixelSize: 22; weight: Font.DemiBold }
            }
        }
    }

    // Luzes de alerta.
    Row {
        anchors {
            horizontalCenter: parent.horizontalCenter
            top: parent.top
            topMargin: 10
        }
        spacing: 10

        AlertLamp {
            active: Telemetry.lowFuel
            glyph: "⛽"
            text: qsTr("RESERVA")
            activeColor: Theme.colors.warning
        }

        AlertLamp {
            active: Telemetry.overheating
            glyph: "♨"
            text: qsTr("TEMPERATURA")
        }

        AlertLamp {
            active: Telemetry.lowVoltage
            glyph: "⚡"
            text: qsTr("TENSAO")
        }

        AlertLamp {
            active: Telemetry.rpm >= 5500
            glyph: "▲"
            text: qsTr("TROCAR")
            activeColor: Theme.colors.warning
        }
    }

    // Rodape: combustivel, hodometro e temperatura.
    BarIndicator {
        id: fuelBar

        anchors { left: parent.left; leftMargin: 32; bottom: parent.bottom; bottomMargin: 18 }
        width: Math.min(220, dashboard.width * 0.22)

        value: Telemetry.fuelLevel
        label: qsTr("COMBUSTIVEL")
        glyph: "⛽"
        alert: Telemetry.lowFuel
        accent: Theme.colors.success
    }

    BarIndicator {
        id: tempBar

        anchors { right: parent.right; rightMargin: 32; bottom: parent.bottom; bottomMargin: 18 }
        width: Math.min(220, dashboard.width * 0.22)

        value: Telemetry.coolantTemp
        minimum: 20
        maximum: 120
        label: qsTr("TEMPERATURA")
        glyph: "♨"
        alert: Telemetry.overheating
        accent: Theme.colors.warning
    }

    Column {
        anchors {
            horizontalCenter: parent.horizontalCenter
            bottom: parent.bottom
            bottomMargin: 14
        }
        spacing: 2

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Telemetry.odometer.toFixed(1) + " km"
            color: Theme.colors.text
            font { pixelSize: 15; weight: Font.Medium }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: qsTr("HODOMETRO") + "  ·  " + Telemetry.voltage.toFixed(1) + " V"
            color: Theme.colors.text_muted
            font { pixelSize: 11; weight: Font.Medium; letterSpacing: 1.0 }
        }
    }
}
