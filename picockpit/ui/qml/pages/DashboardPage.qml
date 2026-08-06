// Painel digital do Ford Ka 1.0 Ti-VCT.
//
// Composicao inspirada nos clusters da familia BMW IDCevo: fundo quase preto,
// dois arcos abertos na base flanqueando uma leitura numerica central de peso
// leve, informacao secundaria em barras e celulas finas nas bordas. Nenhum
// elemento grafico e copiado - a linguagem visual e a referencia.
//
// A escolha das grandezas e do carro, nao do estilo: num carro a combustao o
// que o motorista acompanha e consumo e autonomia. Tensao de bateria e
// diagnostico, e por isso vive na faixa secundaria.
import QtQuick
import ".."
import PiCockpit 1.0

Item {
    id: dashboard

    readonly property real sideGaugeSize: Math.min(height * 0.66, 260)

    // Conta-giros a esquerda.
    ArcGauge {
        anchors {
            left: parent.left
            leftMargin: 28
            verticalCenter: parent.verticalCenter
            verticalCenterOffset: -18
        }
        width: dashboard.sideGaugeSize
        height: dashboard.sideGaugeSize

        value: Telemetry.rpm
        minimum: 0
        maximum: 7000
        warningFrom: 5500
        thickness: 11
        label: qsTr("RPM")
        units: "rpm"
    }

    // Consumo a direita. Parado, km/L nao tem significado - a conta seria
    // distancia zero sobre combustivel queimado - entao o mostrador troca para
    // consumo horario, que e o que um carro real faz.
    ArcGauge {
        anchors {
            right: parent.right
            rightMargin: 28
            verticalCenter: parent.verticalCenter
            verticalCenterOffset: -18
        }
        width: dashboard.sideGaugeSize
        height: dashboard.sideGaugeSize

        value: Telemetry.moving ? Telemetry.consumption : Telemetry.fuelRate
        minimum: 0
        maximum: Telemetry.moving ? 25 : 12
        thickness: 11
        label: qsTr("CONSUMO")
        units: Telemetry.moving ? "km/L" : "L/h"
        valueText: (Telemetry.moving ? Telemetry.consumption : Telemetry.fuelRate).toFixed(1)
        accent: Theme.colors.success
    }

    // Bloco central: velocidade e marcha.
    Column {
        anchors {
            horizontalCenter: parent.horizontalCenter
            verticalCenter: parent.verticalCenter
            verticalCenterOffset: -30
        }
        spacing: -6

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Math.round(Telemetry.speed)
            color: Theme.colors.text
            font { pixelSize: Math.round(dashboard.height * 0.32); weight: Font.Light }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "km/h"
            color: Theme.colors.text_muted
            font { pixelSize: 14; weight: Font.Medium; letterSpacing: 2.0 }
        }

        Item {
            width: 1
            height: 10
        }

        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 50
            height: 36
            radius: 9
            color: Theme.colors.surface
            border.width: 1
            border.color: Theme.colors.surface_alt

            Text {
                anchors.centerIn: parent
                text: Telemetry.gearLabel
                color: Theme.colors.primary
                font { pixelSize: 20; weight: Font.DemiBold }
            }
        }
    }

    // Luzes de alerta.
    Row {
        anchors {
            horizontalCenter: parent.horizontalCenter
            top: parent.top
            topMargin: 8
        }
        spacing: 8

        AlertLamp {
            active: Telemetry.milOn
            glyph: "⬤"
            text: qsTr("INJECAO")
            activeColor: Theme.colors.warning
        }

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

    // Faixa de leituras secundarias.
    Row {
        anchors {
            horizontalCenter: parent.horizontalCenter
            bottom: parent.bottom
            bottomMargin: 46
        }
        spacing: 22

        InfoCell {
            label: qsTr("AUTONOMIA")
            value: Math.round(Telemetry.range) + " km"
            alert: Telemetry.lowFuel
        }

        InfoCell {
            label: qsTr("AR ADMITIDO")
            value: Telemetry.intakeTemp.toFixed(0) + " °C"
        }

        InfoCell {
            label: qsTr("BATERIA")
            value: Telemetry.voltage.toFixed(1) + " V"
            alert: Telemetry.lowVoltage
        }

        InfoCell {
            label: qsTr("CARGA")
            value: Math.round(Telemetry.engineLoad) + " %"
        }

        InfoCell {
            label: qsTr("COLETOR")
            value: Math.round(Telemetry.map) + " kPa"
        }

        InfoCell {
            label: qsTr("ACELERADOR")
            value: Math.round(Telemetry.throttle) + " %"
        }

        InfoCell {
            label: qsTr("HODOMETRO")
            value: Telemetry.odometer.toFixed(1) + " km"
        }
    }

    // Rodape. As barras acompanham o arco de cima: temperatura do motor sob o
    // conta-giros, combustivel sob o consumo. Agrupar por assunto vale mais do
    // que simetria - o olho procura combustivel perto de km/L.
    BarIndicator {
        anchors { left: parent.left; leftMargin: 28; bottom: parent.bottom; bottomMargin: 14 }
        width: Math.min(230, dashboard.width * 0.23)

        value: Telemetry.coolantTemp
        minimum: 20
        maximum: 120
        label: qsTr("MOTOR")
        glyph: "♨"
        // Mostra o maximo junto: sem a escala, "92" nao diz se o motor esta
        // no ponto de operacao ou prestes a ferver.
        readout: Math.round(Telemetry.coolantTemp) + " / 120 °C"
        alert: Telemetry.overheating
        accent: Theme.colors.warning
    }

    BarIndicator {
        anchors { right: parent.right; rightMargin: 28; bottom: parent.bottom; bottomMargin: 14 }
        width: Math.min(230, dashboard.width * 0.23)

        value: Telemetry.fuelLevel
        label: qsTr("COMBUSTIVEL")
        glyph: "⛽"
        readout: Math.round(Telemetry.fuelLevel) + " %"
        alert: Telemetry.lowFuel
        accent: Theme.colors.success
    }

    // Codigos de falha, quando houver.
    Text {
        anchors {
            horizontalCenter: parent.horizontalCenter
            bottom: parent.bottom
            bottomMargin: 20
        }
        visible: Telemetry.faultCodes.length > 0
        text: qsTr("FALHAS: ") + Telemetry.faultCodes.join("  ")
        color: Theme.colors.warning
        font { pixelSize: 11; weight: Font.DemiBold; letterSpacing: 1.0 }
    }
}
