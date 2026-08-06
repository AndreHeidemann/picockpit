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

    readonly property var target: Qt.application.screens[Display.clusterScreen]

    // Com dois displays o cluster ocupa o seu inteiro. Com um so - a bancada -
    // ele cede a faixa da direita para a multimidia, reproduzindo o arranjo
    // final numa tela. Deixar o cluster em tela cheia aqui esconderia a outra
    // janela por baixo, que foi o que aconteceu na primeira montagem.
    readonly property bool sharing: !Display.dual

    // 1280x480 e uma proporcao comum de cluster automotivo widescreen.
    width: sharing && target
        ? Math.round(target.width * (1 - Display.consoleFraction))
        : 1280
    height: sharing && target ? target.height : 480
    x: 0
    y: 0
    visible: true
    color: Theme.colors.background
    title: qsTr("PiCockpit OS - Painel")

    screen: target
    visibility: AppInfo.kiosk && !sharing ? Window.FullScreen : Window.Windowed

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
