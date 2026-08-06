// Mostrador em arco, aberto na base.
//
// Desenhado com QtQuick.Shapes e CurveRenderer: a geometria vai para a GPU,
// ao contrario de Canvas, que rasteriza na CPU e derrubaria o FPS no Pi.
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

    property real thickness: 10
    property string label: ""
    property string units: ""
    property color accent: Theme.colors.primary
    property int tickCount: 9

    // Arco aberto na base: comeca em 150 graus e varre 240 no sentido horario.
    readonly property real startAngle: 150
    readonly property real sweepAngle: 240

    readonly property real fraction: maximum > minimum
        ? Math.max(0, Math.min(1, (value - minimum) / (maximum - minimum)))
        : 0
    readonly property real radius: Math.min(width, height) / 2 - thickness
    readonly property bool inWarning: !isNaN(warningFrom) && value >= warningFrom

    readonly property real warningFraction: isNaN(warningFrom)
        ? 1
        : Math.max(0, Math.min(1, (warningFrom - minimum) / (maximum - minimum)))
    readonly property color dangerColor: Theme.colors.danger
    readonly property color warningStroke: isNaN(warningFrom)
        ? "transparent"
        : Qt.rgba(dangerColor.r, dangerColor.g, dangerColor.b, 0.35)

    // Suaviza a chegada das amostras: o provider entrega a 20 Hz, a tela
    // desenha a 60. Sem isto o ponteiro andaria aos saltos.
    Behavior on value {
        NumberAnimation { duration: 130; easing.type: Easing.OutQuad }
    }

    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        asynchronous: false

        // Trilho
        ShapePath {
            strokeColor: Theme.colors.surface_alt
            strokeWidth: gauge.thickness
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap

            PathAngleArc {
                centerX: gauge.width / 2
                centerY: gauge.height / 2
                radiusX: gauge.radius
                radiusY: gauge.radius
                startAngle: gauge.startAngle
                sweepAngle: gauge.sweepAngle
            }
        }

        // Zona de atencao.
        // ShapePath nao e um Item: nao tem opacity nem visible. A transparencia
        // precisa estar na propria cor, e "apagar" a zona significa pintar de
        // transparente.
        ShapePath {
            strokeColor: gauge.warningStroke
            strokeWidth: gauge.thickness
            fillColor: "transparent"
            capStyle: ShapePath.FlatCap

            PathAngleArc {
                centerX: gauge.width / 2
                centerY: gauge.height / 2
                radiusX: gauge.radius
                radiusY: gauge.radius
                startAngle: gauge.startAngle + gauge.sweepAngle * gauge.warningFraction
                sweepAngle: gauge.sweepAngle * (1 - gauge.warningFraction)
            }
        }

        // Progresso
        ShapePath {
            strokeColor: gauge.inWarning ? Theme.colors.danger : gauge.accent
            strokeWidth: gauge.thickness
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap

            PathAngleArc {
                centerX: gauge.width / 2
                centerY: gauge.height / 2
                radiusX: gauge.radius
                radiusY: gauge.radius
                startAngle: gauge.startAngle
                sweepAngle: Math.max(0.5, gauge.sweepAngle * gauge.fraction)
            }
        }
    }

    // Marcacoes
    Repeater {
        model: gauge.tickCount

        delegate: Rectangle {
            required property int index

            readonly property real angle: gauge.startAngle
                + gauge.sweepAngle * (index / (gauge.tickCount - 1))
            readonly property real radians: angle * Math.PI / 180
            readonly property real distance: gauge.radius - gauge.thickness - 6

            width: 2
            height: 8
            radius: 1
            color: Theme.colors.text_muted
            opacity: 0.5
            antialiasing: true

            x: gauge.width / 2 + distance * Math.cos(radians) - width / 2
            y: gauge.height / 2 + distance * Math.sin(radians) - height / 2
            rotation: angle - 90
        }
    }

    Column {
        anchors.centerIn: parent
        spacing: 2

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Math.round(gauge.value)
            color: gauge.inWarning ? Theme.colors.danger : Theme.colors.text
            font { pixelSize: Math.round(gauge.radius * 0.42); weight: Font.Light }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: gauge.units
            color: Theme.colors.text_muted
            font { pixelSize: 12; weight: Font.Medium; letterSpacing: 1.2 }
        }
    }

    Text {
        anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom }
        text: gauge.label
        color: Theme.colors.text_muted
        font { pixelSize: 13; weight: Font.DemiBold; letterSpacing: 1.5 }
    }
}
