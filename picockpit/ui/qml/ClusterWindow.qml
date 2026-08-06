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
import "pages"

Window {
    id: cluster

    readonly property var target: Qt.application.screens[Display.clusterScreen]

    width: target ? target.width : 1280
    height: target ? target.height : 480
    x: 0
    y: 0
    visible: Display.dual
    color: Theme.colors.background
    title: qsTr("PiCockpit OS - Painel")

    screen: target
    visibility: AppInfo.kiosk ? Window.FullScreen : Window.Windowed

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

        TopBar {
            id: topBar

            anchors { top: parent.top; left: parent.left; right: parent.right }
            height: 44
            title: qsTr("Painel")
        }

        // Carregado apenas quando a janela existe de fato: com um display so,
        // montar o painel duas vezes seria pagar duas vezes pela mesma cena.
        Loader {
            anchors {
                top: topBar.bottom
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
            active: cluster.visible
            sourceComponent: DashboardPage {}
        }
    }
}
