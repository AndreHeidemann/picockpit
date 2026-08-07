// Janela do motorista: instrumentos e nada mais.
//
// Nao tem barra de navegacao nem area sensivel a toque - e a tela que o
// motorista olha, nao a que ele opera. Isso nao e imposto por uma flag de
// janela, e sim pela composicao: o painel nao contem um unico MouseArea. Menu
// aberto por engano a 100 km/h e um modo de falha que nao pode existir.
//
// So existe quando ha dois displays. Com um monitor, o painel volta a ser a
// primeira pagina da janela de multimidia: dividir uma tela em duas janelas
// entregaria um cluster deformado e uma barra estreita demais.
import QtQuick
import QtQuick.Window
import PiCockpit 1.0

Window {
    id: cluster

    // Ver ConsoleWindow: `screens` existe na QGuiApplication real, nao no tipo
    // que o qmllint resolve estaticamente.
    // qmllint disable missing-property
    readonly property var target: Qt.application.screens[Display.clusterScreen]
    // qmllint enable missing-property
    readonly property var box: Display.clusterGeometry

    // Geometria vem do controlador, que sabe se a tela e exclusiva ou dividida
    // com a multimidia. Deixar cada janela decidir sozinha era como as duas
    // acabavam empilhadas.
    width: box.width
    height: box.height
    x: box.x
    y: box.y
    color: Theme.colors.background
    title: qsTr("PiCockpit OS - Painel")

    screen: target

    // Ocultar precisa passar por `visibility`, e nao por `visible`: em Qt as
    // duas propriedades estao ligadas, e definir visibility como FullScreen
    // mostra a janela mesmo com visible false. Foi assim que o cluster
    // apareceu por baixo da multimidia numa tela so - duas barras de
    // combustivel na mesma imagem.
    visibility: !Display.dual
        ? Window.Hidden
        : (AppInfo.kiosk && Display.fullscreenAllowed
            ? Window.FullScreen
            : Window.Windowed)
    visible: Display.dual

    Item {
        id: canvas

        readonly property real factor: Settings.uiScale > 0 ? Settings.uiScale : 1.0

        width: cluster.width / factor
        height: cluster.height / factor
        transform: Scale {
            origin.x: 0
            origin.y: 0
            xScale: canvas.factor
            yScale: canvas.factor
        }

        // Carregado apenas quando a janela existe de fato: com a tela
        // compartilhada, o cluster e composto dentro da janela da multimidia e
        // montar a cena duas vezes seria pagar duas vezes pela mais cara.
        Loader {
            anchors.fill: parent
            active: cluster.visible
            sourceComponent: ClusterView {}
        }
    }
}
