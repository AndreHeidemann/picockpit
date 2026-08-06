// Mostrador principal do painel, em duas geometrias.
//
// `segment`: setores preenchidos com gradiente, separados por vaos angulares,
// escala numerica ao redor. `arc`: traco fino de contorno, discreto.
//
// A geometria vem do tema, nao de quem usa o componente: modo esportivo de
// painel automotivo nao e o modo conforto pintado de outra cor - muda o
// desenho do instrumento.
//
// Detalhe tecnico que dita a implementacao: ShapePath aceita gradiente no
// preenchimento, nao no traco. Por isso o estilo com gradiente e desenhado
// como setor fechado - arco externo, linha, arco interno de volta - e nao como
// linha grossa.
import QtQuick
import QtQuick.Shapes
import PiCockpit 1.0

Item {
    id: gauge

    property real value: 0
    property real minimum: 0
    property real maximum: 100
    // Zona de atencao, em unidades de valor. NaN desliga.
    property real warningFrom: NaN

    property real thickness: 22
    property string label: ""
    property string units: ""
    property string valueText: Math.round(value).toString()
    property color accent: Theme.colors.primary
    property color accentDim: Theme.colors.primary_dim
    // Espelha o mostrador para que ele abra na direcao do centro do painel.
    property bool mirrored: false
    property int scaleSteps: 7
    property real scaleFactor: 1.0
    property int scaleDecimals: 0
    property int separatorCount: 24

    readonly property string style: Theme.gaugeStyle
    readonly property bool segmented: style === "segment"

    readonly property real startAngle: mirrored ? 30 : 150
    readonly property real sweepAngle: mirrored ? -240 : 240

    readonly property real fraction: maximum > minimum
        ? Math.max(0, Math.min(1, (value - minimum) / (maximum - minimum)))
        : 0
    readonly property real outerRadius: Math.min(width, height) / 2 - 2
    readonly property real innerRadius: outerRadius - thickness
    readonly property real centerX: width / 2
    readonly property real centerY: height / 2

    readonly property bool inWarning: !isNaN(warningFrom) && value >= warningFrom
    readonly property real warningFraction: isNaN(warningFrom)
        ? 1
        : Math.max(0, Math.min(1, (warningFrom - minimum) / (maximum - minimum)))

    // Suaviza a chegada das amostras: o provider entrega a 20 Hz, a tela
    // desenha a 60. Sem isto o ponteiro andaria aos saltos.
    Behavior on value {
        NumberAnimation { duration: 130; easing.type: Easing.OutQuad }
    }

    function pointX(angle, radius) {
        return gauge.centerX + radius * Math.cos(angle * Math.PI / 180)
    }

    function pointY(angle, radius) {
        return gauge.centerY + radius * Math.sin(angle * Math.PI / 180)
    }

    // ------------------------------------------------------------- segmento

    Shape {
        anchors.fill: parent
        visible: gauge.segmented
        preferredRendererType: Shape.CurveRenderer

        // Trilho
        ShapePath {
            fillColor: Theme.colors.surface_alt
            strokeColor: "transparent"

            startX: gauge.pointX(gauge.startAngle, gauge.outerRadius)
            startY: gauge.pointY(gauge.startAngle, gauge.outerRadius)

            PathAngleArc {
                centerX: gauge.centerX
                centerY: gauge.centerY
                radiusX: gauge.outerRadius
                radiusY: gauge.outerRadius
                startAngle: gauge.startAngle
                sweepAngle: gauge.sweepAngle
                moveToStart: false
            }

            PathLine {
                x: gauge.pointX(gauge.startAngle + gauge.sweepAngle, gauge.innerRadius)
                y: gauge.pointY(gauge.startAngle + gauge.sweepAngle, gauge.innerRadius)
            }

            PathAngleArc {
                centerX: gauge.centerX
                centerY: gauge.centerY
                radiusX: gauge.innerRadius
                radiusY: gauge.innerRadius
                startAngle: gauge.startAngle + gauge.sweepAngle
                sweepAngle: -gauge.sweepAngle
                moveToStart: false
            }

            PathLine {
                x: gauge.pointX(gauge.startAngle, gauge.outerRadius)
                y: gauge.pointY(gauge.startAngle, gauge.outerRadius)
            }
        }

        // Progresso, com gradiente do tom escuro ao claro no sentido do
        // crescimento.
        ShapePath {
            id: progressPath

            // Referencia por id, e nao por `parent`: elementos de caminho nao
            // sao Items e nao tem pai navegavel. `parent.sweep` resolveria
            // como undefined e o setor sumiria.
            readonly property real sweep: gauge.sweepAngle * gauge.fraction

            strokeColor: "transparent"

            fillGradient: LinearGradient {
                x1: gauge.pointX(gauge.startAngle, gauge.outerRadius)
                y1: gauge.pointY(gauge.startAngle, gauge.outerRadius)
                x2: gauge.pointX(gauge.startAngle + gauge.sweepAngle, gauge.outerRadius)
                y2: gauge.pointY(gauge.startAngle + gauge.sweepAngle, gauge.outerRadius)

                GradientStop { position: 0.0; color: gauge.accentDim }
                GradientStop {
                    position: 1.0
                    color: gauge.inWarning ? Theme.colors.danger : gauge.accent
                }
            }

            startX: gauge.pointX(gauge.startAngle, gauge.outerRadius)
            startY: gauge.pointY(gauge.startAngle, gauge.outerRadius)

            PathAngleArc {
                centerX: gauge.centerX
                centerY: gauge.centerY
                radiusX: gauge.outerRadius
                radiusY: gauge.outerRadius
                startAngle: gauge.startAngle
                sweepAngle: progressPath.sweep
                moveToStart: false
            }

            PathLine {
                x: gauge.pointX(gauge.startAngle + progressPath.sweep, gauge.innerRadius)
                y: gauge.pointY(gauge.startAngle + progressPath.sweep, gauge.innerRadius)
            }

            PathAngleArc {
                centerX: gauge.centerX
                centerY: gauge.centerY
                radiusX: gauge.innerRadius
                radiusY: gauge.innerRadius
                startAngle: gauge.startAngle + progressPath.sweep
                sweepAngle: -progressPath.sweep
                moveToStart: false
            }

            PathLine {
                x: gauge.pointX(gauge.startAngle, gauge.outerRadius)
                y: gauge.pointY(gauge.startAngle, gauge.outerRadius)
            }
        }
    }

    // Separadores angulares. Retangulos finos sobre o setor saem bem mais
    // barato do que desenhar dezenas de setores independentes, e o resultado
    // visual e o mesmo.
    Repeater {
        model: gauge.segmented ? gauge.separatorCount : 0

        delegate: Rectangle {
            required property int index

            readonly property real angle: gauge.startAngle
                + gauge.sweepAngle * (index / gauge.separatorCount)

            width: 2
            height: gauge.thickness
            color: Theme.colors.background
            antialiasing: true

            x: gauge.pointX(angle, gauge.outerRadius - gauge.thickness / 2) - width / 2
            y: gauge.pointY(angle, gauge.outerRadius - gauge.thickness / 2) - height / 2
            rotation: angle - 90
        }
    }

    // ------------------------------------------------------------------ arco

    Shape {
        anchors.fill: parent
        visible: !gauge.segmented
        preferredRendererType: Shape.CurveRenderer

        ShapePath {
            strokeColor: Theme.colors.surface_alt
            strokeWidth: 3
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap

            PathAngleArc {
                centerX: gauge.centerX
                centerY: gauge.centerY
                radiusX: gauge.outerRadius - gauge.thickness / 2
                radiusY: gauge.outerRadius - gauge.thickness / 2
                startAngle: gauge.startAngle
                sweepAngle: gauge.sweepAngle
            }
        }

        ShapePath {
            strokeColor: gauge.inWarning ? Theme.colors.danger : gauge.accent
            strokeWidth: 3
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap

            PathAngleArc {
                centerX: gauge.centerX
                centerY: gauge.centerY
                radiusX: gauge.outerRadius - gauge.thickness / 2
                radiusY: gauge.outerRadius - gauge.thickness / 2
                startAngle: gauge.startAngle
                // Varredura minima para o traco nao desaparecer no zero.
                sweepAngle: gauge.sweepAngle >= 0
                    ? Math.max(0.5, gauge.sweepAngle * gauge.fraction)
                    : Math.min(-0.5, gauge.sweepAngle * gauge.fraction)
            }
        }
    }

    // ----------------------------------------------------------- escala

    Repeater {
        model: gauge.scaleSteps

        delegate: Text {
            required property int index

            readonly property real position: index / (gauge.scaleSteps - 1)
            readonly property real angle: gauge.startAngle + gauge.sweepAngle * position
            readonly property real distance: gauge.innerRadius - 14
            readonly property bool warned: !isNaN(gauge.warningFrom)
                && position >= gauge.warningFraction

            // scaleFactor permite marcar o conta-giros em milhares (1, 2, 3)
            // em vez de 1000, 2000, 3000, que nao caberia no anel.
            text: ((gauge.minimum + (gauge.maximum - gauge.minimum) * position)
                * gauge.scaleFactor).toFixed(gauge.scaleDecimals)
            color: warned ? Theme.colors.danger : Theme.colors.text_muted
            font { pixelSize: 11; weight: Font.Medium }

            x: gauge.pointX(angle, distance) - width / 2
            y: gauge.pointY(angle, distance) - height / 2
        }
    }

    // ----------------------------------------------------------- leitura

    Column {
        anchors.centerIn: parent
        spacing: 0

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: gauge.valueText
            color: gauge.inWarning ? Theme.colors.danger : Theme.colors.text
            font { pixelSize: Math.round(gauge.outerRadius * 0.44); weight: Font.Light }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: gauge.units
            color: Theme.colors.text_muted
            font { pixelSize: 11; weight: Font.Medium; letterSpacing: 1.2 }
        }
    }

    Text {
        anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom }
        text: gauge.label
        color: Theme.colors.text_muted
        font { pixelSize: 12; weight: Font.DemiBold; letterSpacing: 1.6 }
    }
}
