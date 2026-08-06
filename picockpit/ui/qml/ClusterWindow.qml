// Janela do motorista: instrumentos e nada mais.
//
// Nao tem barra de navegacao nem area sensivel a toque - e a tela que o
// motorista olha, nao a que ele opera. Isso nao e imposto por uma flag de
// janela, e sim pela composicao: o painel nao contem um unico MouseArea. Menu
// aberto por engano a 100 km/h e um modo de falha que nao pode existir.
import QtQuick
import QtQuick.Window
import PiCockpit 1.0
import "pages"

Window {
    id: cluster

    // 1280x480 e uma proporcao comum de cluster automotivo widescreen.
    width: 1280
    height: 480
    visible: true
    color: Theme.colors.background
    title: qsTr("PiCockpit OS - Painel")

    screen: Qt.application.screens[Display.clusterScreen]
    visibility: AppInfo.kiosk ? Window.FullScreen : Window.Windowed

    // Barra minima: relogio, FPS e alertas ja vivem dentro do painel.
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

        DashboardPage {
            anchors {
                top: topBar.bottom
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
        }
    }
}
