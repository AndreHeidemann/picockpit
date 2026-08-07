// Previa de um tema: mostra o desenho do instrumento, nao so o nome.
//
// Existe porque os cinco temas deixaram de ser a mesma geometria pintada de
// outra cor. Escolher "Track" por um rotulo escrito exige lembrar o que Track
// faz; escolher por um mostrador de 76 px que abre 264 graus com o anel grosso
// nao exige lembrar nada.
//
// A previa desenha o arco como traco, sem o gradiente do setor preenchido:
// ShapePath so aceita gradiente no preenchimento, e reconstruir o setor
// fechado aqui dobraria o codigo para ganhar uma nuance que a miniatura nao
// resolve. Abertura, espessura e densidade de segmentos - que sao o que
// distingue os modos - estao todas representadas em escala.
import QtQuick
import QtQuick.Shapes
import PiCockpit 1.0

Item {
    id: swatch

    property string themeName: ""
    property bool selected: false

    signal activated()

    // Consultas a uma tabela estatica: nao mudam quando o tema ativo muda, por
    // isso podem ser resolvidas uma vez na construcao do delegate.
    readonly property var colors: Theme.paletteOf(themeName)
    readonly property var geometry: Theme.gaugeOf(themeName)
    readonly property bool segmented: Theme.styleOf(themeName) === "segment"

    // Fracao acesa fixa: a previa compara desenhos, nao valores. Um valor
    // qualquer proximo de dois tercos mostra tanto o trilho quanto o aceso.
    readonly property real fraction: 0.66

    implicitWidth: 132
    implicitHeight: 116

    Rectangle {
        anchors.fill: parent
        radius: 12
        color: swatch.colors.background
        border.width: swatch.selected ? 2 : 1
        border.color: swatch.selected ? swatch.colors.primary : swatch.colors.surface_alt

        Behavior on border.color {
            ColorAnimation { duration: 150 }
        }
    }

    Item {
        id: preview

        anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: 12 }
        width: 76
        height: 76

        readonly property real outerRadius: width / 2 - 1
        readonly property real thickness: Math.max(
            2, outerRadius * swatch.geometry.thickness_ratio)
        // Mesma regra do mostrador de verdade: o vao fica centrado embaixo e e
        // a abertura que cresce em torno dele.
        readonly property real startAngle: 270 - swatch.geometry.sweep_degrees / 2
        readonly property real sweepAngle: swatch.geometry.sweep_degrees
        readonly property real radius: outerRadius - thickness / 2
        readonly property real centerX: width / 2
        readonly property real centerY: height / 2

        Shape {
            anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer

            ShapePath {
                strokeColor: swatch.colors.surface_alt
                strokeWidth: preview.thickness
                fillColor: "transparent"
                capStyle: ShapePath.FlatCap

                PathAngleArc {
                    centerX: preview.centerX
                    centerY: preview.centerY
                    radiusX: preview.radius
                    radiusY: preview.radius
                    startAngle: preview.startAngle
                    sweepAngle: preview.sweepAngle
                }
            }

            ShapePath {
                strokeColor: swatch.colors.primary
                strokeWidth: preview.thickness
                fillColor: "transparent"
                capStyle: ShapePath.FlatCap

                PathAngleArc {
                    centerX: preview.centerX
                    centerY: preview.centerY
                    radiusX: preview.radius
                    radiusY: preview.radius
                    startAngle: preview.startAngle
                    sweepAngle: preview.sweepAngle * swatch.fraction
                }
            }
        }

        // Separadores na densidade real do tema: e o que separa Technology,
        // com sessenta tracos de um pixel, de Track, com quarenta e quatro
        // grossos.
        Repeater {
            model: swatch.segmented ? swatch.geometry.separator_count : 0

            delegate: Rectangle {
                required property int index

                readonly property real angle: preview.startAngle
                    + preview.sweepAngle * (index / swatch.geometry.separator_count)

                // A previa tem cerca de um terco do mostrador real; um traco
                // de 3 px viraria um bloco aqui. Reduzido, mas nao achatado em
                // 1 px, senao Track e Technology ficariam iguais.
                width: Math.max(1, Math.round(swatch.geometry.tick_width * 0.6))
                height: preview.thickness
                color: swatch.colors.background
                antialiasing: true

                x: preview.centerX + preview.radius * Math.cos(angle * Math.PI / 180) - width / 2
                y: preview.centerY + preview.radius * Math.sin(angle * Math.PI / 180) - height / 2
                rotation: angle - 90
            }
        }

        // Numeral central na tipografia do proprio tema: e o outro eixo em que
        // os modos diferem, e sem ele a previa nao mostraria o peso da fonte.
        Text {
            anchors.centerIn: parent
            text: "88"
            color: swatch.colors.text
            font {
                pixelSize: Math.round(preview.outerRadius * swatch.geometry.value_ratio)
                weight: swatch.geometry.value_weight
            }
        }
    }

    Text {
        anchors {
            horizontalCenter: parent.horizontalCenter
            bottom: parent.bottom
            bottomMargin: 10
        }
        text: Theme.labelOf(swatch.themeName)
        color: swatch.selected ? swatch.colors.text : swatch.colors.text_muted
        font {
            pixelSize: 12
            weight: swatch.selected ? Font.DemiBold : Font.Medium
            letterSpacing: 0.8
        }
    }

    MouseArea {
        anchors.fill: parent
        onClicked: swatch.activated()
    }
}
