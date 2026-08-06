// Janela da multimidia: navegacao, ajustes e todo o comando do sistema.
//
// Com dois displays ocupa apenas uma fracao da tela; o restante fica para a
// janela de projecao do CarPlay/Android Auto, posicionada pelo compositor -
// nenhuma das solucoes de projecao entrega o video como item Qt que a gente
// possa ancorar dentro da nossa cena.
//
// Com um display so, esta e a unica janela e ocupa a tela inteira, com o
// painel como primeira pagina da navegacao. E o arranjo de bancada, e tambem o
// de uma instalacao com tela unica.
import QtQuick
import QtQuick.Window
import QtQuick.Controls
import PiCockpit 1.0

Window {
    id: hub

    readonly property var target: Qt.application.screens[Display.consoleScreen]

    // Sozinha na tela, ocupa tudo. Ao lado do cluster, cede a maior parte para
    // a projecao.
    readonly property bool solo: !Display.dual
    readonly property int targetWidth: !target
        ? 420
        : (solo ? target.width : Math.round(target.width * Display.consoleFraction))

    width: Math.max(320, targetWidth)
    height: target ? target.height : 720
    visible: true
    color: Theme.colors.background
    title: qsTr("PiCockpit OS - Multimidia")

    screen: target
    // Sem decoracao no carro; em bancada a janela continua movel.
    flags: AppInfo.kiosk ? Qt.Window | Qt.FramelessWindowHint : Qt.Window

    x: 0
    y: 0

    property int currentIndex: 0

    readonly property var pages: Layout.pages

    Item {
        id: canvas

        readonly property real factor: Settings.uiScale > 0 ? Settings.uiScale : 1.0

        width: hub.width / factor
        height: hub.height / factor
        transform: Scale {
            origin.x: 0
            origin.y: 0
            xScale: canvas.factor
            yScale: canvas.factor
        }

        TopBar {
            id: topBar

            anchors { top: parent.top; left: parent.left; right: parent.right }
            height: 52
            title: hub.pages[hub.currentIndex].label
        }

        NavigationRail {
            id: rail

            anchors { top: topBar.bottom; left: parent.left; bottom: parent.bottom }
            width: 92
            model: hub.pages
            currentIndex: hub.currentIndex
            onSelected: function (index) { hub.currentIndex = index }
        }

        PageHost {
            anchors {
                top: topBar.bottom
                left: rail.right
                right: parent.right
                bottom: parent.bottom
            }
            pageKey: hub.pages[hub.currentIndex].key
        }
    }

    Shortcut {
        sequences: ["Ctrl+Q", "Esc"]
        onActivated: Qt.quit()
    }
}
