// Grafico de linha alimentado por uma serie temporal do Python.
//
// Desenhado com Shape/PathPolyline: a polilinha vai inteira para a GPU num
// unico no de cena. Um Canvas equivalente repintaria a textura a cada
// atualizacao, na CPU.
import QtQuick
import QtQuick.Shapes
import PiCockpit 1.0

Item {
    id: chart

    property string signalName: ""
    property string label: ""
    // A unidade vem do controlador, nao da pagina: escrita a mao, ela nao
    // acompanhava a troca para o sistema imperial e o grafico contradizia o
    // painel ao lado.
    readonly property string units: Chart.revision >= 0 ? Chart.unitOf(signalName) : ""
    property color accent: Theme.colors.primary
    property int decimals: 0

    // Depende de Chart.revision de proposito: binding QML so reavalia quando
    // depende de uma propriedade, e referenciar o sinal nao criaria dependencia
    // nenhuma - o grafico congelaria no primeiro desenho.
    readonly property var points: Chart.revision >= 0
        ? Chart.polyline(signalName, plot.width, plot.height)
        : []

    Rectangle {
        anchors.fill: parent
        radius: 12
        color: Theme.colors.surface
        border.width: 1
        border.color: Theme.colors.surface_alt
    }

    Row {
        id: header

        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
        spacing: 8

        Text {
            text: chart.label
            color: Theme.colors.text_muted
            font { pixelSize: 11; weight: Font.DemiBold; letterSpacing: 1.2 }
        }
    }

    Text {
        anchors { right: parent.right; top: parent.top; margins: 12 }
        text: (Chart.revision >= 0 ? Chart.latest(chart.signalName) : 0).toFixed(chart.decimals)
            + " " + chart.units
        color: chart.accent
        font { pixelSize: 14; weight: Font.DemiBold }
    }

    Item {
        id: plot

        anchors {
            left: parent.left
            right: parent.right
            top: header.bottom
            bottom: parent.bottom
            leftMargin: 12
            rightMargin: 12
            topMargin: 8
            bottomMargin: 12
        }

        // Linha de base, para o grafico nao ficar flutuando no vazio.
        Rectangle {
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
            height: 1
            color: Theme.colors.surface_alt
        }

        Shape {
            anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer
            visible: chart.points.length > 1

            ShapePath {
                strokeColor: chart.accent
                strokeWidth: 2
                fillColor: "transparent"
                capStyle: ShapePath.RoundCap
                joinStyle: ShapePath.RoundJoin

                PathPolyline {
                    path: chart.points
                }
            }
        }

        Text {
            anchors.centerIn: parent
            visible: chart.points.length <= 1
            text: qsTr("coletando...")
            color: Theme.colors.text_muted
            font.pixelSize: 12
        }
    }
}
