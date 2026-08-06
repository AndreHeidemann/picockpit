// Janela da multimidia: navegacao, ajustes e todo o comando do sistema.
//
// Ocupa apenas uma fracao do display. O restante fica para a janela de
// projecao do CarPlay/Android Auto, posicionada pelo compositor - nenhuma das
// solucoes de projeccao entrega o video como item Qt que a gente possa ancorar
// dentro da nossa cena.
import QtQuick
import QtQuick.Window
import QtQuick.Controls
import PiCockpit 1.0

Window {
    id: hub

    readonly property var target: Qt.application.screens[Display.consoleScreen]
    readonly property int targetWidth: target
        ? Math.round(target.width * Display.consoleFraction)
        : 420

    width: Math.max(320, targetWidth)
    height: target ? target.height : 720
    visible: true
    color: Theme.colors.background
    title: qsTr("PiCockpit OS - Multimidia")

    screen: target
    // Sem decoracao no carro; em bancada a janela continua movel.
    flags: AppInfo.kiosk ? Qt.Window | Qt.FramelessWindowHint : Qt.Window

    // Na bancada, com um monitor so, a janela nasce ao lado do cluster em vez
    // de sobre ele.
    x: Display.dual ? 0 : 40
    y: Display.dual ? 0 : 520

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
