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

    // Em tela dividida o painel recebe uma fracao da largura. Sem regra de
    // adaptacao, a faixa de leituras secundarias passa por cima das barras
    // laterais - foi o que aconteceu na primeira montagem com 70/30.
    readonly property bool compact: width < 860
    readonly property bool veryCompact: width < 640

    readonly property real sideGaugeSize: Math.min(
        height * (compact ? 0.62 : 0.74), compact ? 220 : 290)

    // Escala de mostrador tambem e unidade: converter so o valor faz o
    // ponteiro saturar contra uma regua que ficou em outra medida.
    // 20 a 120 C equivalem a 68 a 248 F; 30 km/L equivalem a ~70 mpg;
    // 12 L/h equivalem a ~3,2 gal/h.
    readonly property bool fahrenheit: Telemetry.temperatureUnit === "F"
    readonly property real temperatureFloor: fahrenheit ? 68 : 20
    readonly property real temperatureCeiling: fahrenheit ? 248 : 120

    readonly property bool milesPerGallon: Telemetry.consumptionUnit === "mpg"
    readonly property real consumptionCeiling: milesPerGallon ? 70 : 30
    readonly property real fuelRateCeiling: milesPerGallon ? 3.5 : 12

    // Conta-giros a esquerda.
    Gauge {
        id: tachometer

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
        label: qsTr("RPM")
        units: "rpm"
        scaleSteps: 8
        scaleFactor: 0.001
        scaleDecimals: 0
    }

    // Consumo a direita. Parado, km/L nao tem significado - a conta seria
    // distancia zero sobre combustivel queimado - entao o mostrador troca para
    // consumo horario, que e o que um carro real faz.
    Gauge {
        id: consumptionGauge

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
        maximum: Telemetry.moving ? dashboard.consumptionCeiling : dashboard.fuelRateCeiling
        label: qsTr("CONSUMO")
        units: Telemetry.moving ? Telemetry.consumptionUnit : Telemetry.fuelRateUnit
        valueText: (Telemetry.moving ? Telemetry.consumption : Telemetry.fuelRate).toFixed(1)
        // Espelhado para abrir na direcao do centro, como no conjunto
        // simetrico de um cluster real.
        mirrored: true
        scaleSteps: 6
        accent: Theme.colors.success
        // O gradiente precisa ser da mesma familia da cor de acento; usar a
        // ponta escura do tema aqui misturaria verde com azul.
        accentDim: Qt.darker(Theme.colors.success, 2.4)
    }

    // Bloco central: velocidade e marcha.
    //
    // Ancorado entre os dois mostradores, e nao no centro da pagina. Numeral
    // grande com posicao centralizada invadia o mostrador da direita assim que
    // a regiao encolhia: o tamanho da fonte tambem precisa caber na largura
    // disponivel, nao so na altura.
    Item {
        id: centerArea

        anchors {
            left: tachometer.right
            right: consumptionGauge.left
            top: parent.top
            bottom: parent.bottom
            leftMargin: 6
            rightMargin: 6
        }
    }

    Column {
        anchors {
            horizontalCenter: centerArea.horizontalCenter
            verticalCenter: parent.verticalCenter
            verticalCenterOffset: -30
        }
        spacing: -6

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Math.round(Telemetry.speed)
            color: Theme.colors.text
            font {
                pixelSize: Math.round(Math.min(
                    dashboard.height * (dashboard.compact ? 0.26 : 0.32),
                    centerArea.width * 0.44))
                weight: Font.Light
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Telemetry.speedUnit
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
        spacing: dashboard.compact ? 4 : 8

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

    // Rodape. As barras acompanham o arco de cima: temperatura do motor sob o
    // conta-giros, combustivel sob o consumo. Agrupar por assunto vale mais do
    // que simetria - o olho procura combustivel perto de km/L.
    BarIndicator {
        id: engineBar

        anchors {
            left: parent.left
            leftMargin: dashboard.compact ? 16 : 28
            bottom: parent.bottom
            bottomMargin: 14
        }
        width: Math.min(dashboard.compact ? 150 : 230, dashboard.width * 0.22)

        value: Telemetry.coolantTemp
        minimum: dashboard.temperatureFloor
        maximum: dashboard.temperatureCeiling
        label: qsTr("MOTOR")
        glyph: "♨"
        // Mostra o maximo junto: sem a escala, "92" nao diz se o motor esta
        // no ponto de operacao ou prestes a ferver.
        readout: Math.round(Telemetry.coolantTemp) + " / "
            + Math.round(dashboard.temperatureCeiling) + " °" + Telemetry.temperatureUnit
        alert: Telemetry.overheating
        accent: Theme.colors.warning
    }

    BarIndicator {
        id: fuelBar

        anchors {
            right: parent.right
            rightMargin: dashboard.compact ? 16 : 28
            bottom: parent.bottom
            bottomMargin: 14
        }
        width: Math.min(dashboard.compact ? 150 : 230, dashboard.width * 0.22)

        value: Telemetry.fuelLevel
        label: qsTr("COMBUSTIVEL")
        glyph: "⛽"
        readout: Math.round(Telemetry.fuelLevel) + " %"
        alert: Telemetry.lowFuel
        accent: Theme.colors.success
    }

    // Faixa de leituras secundarias.
    //
    // Ancorada entre as duas barras, e nao centralizada na pagina: limiar fixo
    // de largura errou feio quando a escala da interface entrou na conta - a
    // regiao tinha 969 px logicos, acima do limiar, e mesmo assim nao cabia.
    // O espaco disponivel e o que existe entre as barras, e e ele que decide
    // quantas leituras aparecem.
    Item {
        id: infoStrip

        anchors {
            left: engineBar.right
            right: fuelBar.left
            bottom: parent.bottom
            leftMargin: 14
            rightMargin: 14
            bottomMargin: 46
        }
        height: 40
        clip: true

        Row {
            anchors.centerIn: parent
            spacing: infoStrip.width < 560 ? 12 : 22

            InfoCell {
                label: qsTr("AUTONOMIA")
                value: Math.round(Telemetry.range) + " " + Telemetry.distanceUnit
                alert: Telemetry.lowFuel
            }

            InfoCell {
                visible: infoStrip.width > 760
                label: qsTr("AR ADMITIDO")
                value: Telemetry.intakeTemp.toFixed(0) + " °" + Telemetry.temperatureUnit
            }

            InfoCell {
                visible: infoStrip.width > 380
                label: qsTr("BATERIA")
                value: Telemetry.voltage.toFixed(1) + " V"
                alert: Telemetry.lowVoltage
            }

            InfoCell {
                visible: infoStrip.width > 560
                label: qsTr("CARGA")
                value: Math.round(Telemetry.engineLoad) + " %"
            }

            InfoCell {
                visible: infoStrip.width > 760
                label: qsTr("COLETOR")
                value: Math.round(Telemetry.map) + " kPa"
            }

            InfoCell {
                visible: infoStrip.width > 560
                label: qsTr("ACELERADOR")
                value: Math.round(Telemetry.throttle) + " %"
            }

            InfoCell {
                label: qsTr("HODOMETRO")
                value: Telemetry.odometer.toFixed(1) + " " + Telemetry.distanceUnit
            }
        }
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
