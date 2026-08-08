// Janela da multimidia: navegacao, ajustes e todo o comando do sistema.
//
// Com dois displays ocupa apenas uma fracao da tela; o restante fica para a
// janela de projecao do Android Auto, posicionada pelo compositor -
// nenhuma das solucoes de projecao entrega o video como item Qt que a gente
// possa ancorar dentro da nossa cena.
//
// Com um display so, esta e a unica janela e ocupa a tela inteira, com o
// painel como primeira pagina da navegacao. E o arranjo de bancada, e tambem o
// de uma instalacao com tela unica.
import QtQuick
import QtQuick.Window
import PiCockpit 1.0

Window {
    id: hub

    // O qmllint enxerga `Qt.application` como QQmlApplication, que nao declara
    // `screens`; em execucao o objeto e uma QGuiApplication, que declara. Falso
    // positivo silenciado no ponto exato, e nao pela categoria inteira - ela
    // pega erro de verdade em todo o resto da arvore.
    // qmllint disable missing-property
    readonly property var target: Qt.application.screens[Display.consoleScreen]
    // qmllint enable missing-property
    readonly property var box: Display.consoleGeometry

    // Sozinha na tela ocupa tudo; ao lado do cluster cede a maior parte para a
    // projecao; dividindo a tela com o cluster fica na faixa da direita. Quem
    // decide e o controlador.
    width: Math.max(320, box.width)
    height: box.height
    visible: true
    color: Theme.colors.background
    title: qsTr("PiCockpit OS - Multimidia")

    screen: target
    // Sem decoracao no carro; em bancada a janela continua movel.
    flags: AppInfo.kiosk ? Qt.Window | Qt.FramelessWindowHint : Qt.Window
    // So vai a tela cheia quando e a unica coisa no display: dividindo a tela
    // ou sem cluster dedicado. Com tela propria e projecao ao lado, tela
    // cheia faz o Wayland ignorar `box` e tomar a saida inteira - a faixa do
    // LIVI so existe se esta janela ficar Windowed, do tamanho de `box`.
    visibility: AppInfo.kiosk && Display.consoleFullscreenAllowed
        ? Window.FullScreen
        : Window.Windowed

    x: box.x
    y: box.y

    property int currentIndex: 0

    // O painel so entra na navegacao quando nao existe cluster. Havendo tela
    // ou regiao de instrumentos, repetir o painel aqui e pior do que inutil:
    // ele ocupa uma fracao estreita da tela e fica ilegivel, competindo com o
    // mesmo conteudo exibido do lado certo.
    readonly property bool hasCluster: Display.dual || Display.shared
    readonly property var pages: hasCluster
        ? Layout.pages.filter(function (page) { return page.key !== "dashboard" })
        : Layout.pages

    onHasClusterChanged: currentIndex = 0

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

        // Regiao do cluster, presente apenas quando os dois papeis dividem a
        // mesma tela. Sao duas regioes de uma janela, e nao duas janelas: o
        // Wayland nao deixa a aplicacao escolher onde cada janela aparece.
        Loader {
            id: clusterRegion

            anchors { top: parent.top; left: parent.left; bottom: parent.bottom }
            width: Display.shared
                ? Math.round(canvas.width * (1 - Display.consoleFraction))
                : 0
            active: Display.shared
            visible: Display.shared
            sourceComponent: ClusterView {}
        }

        Rectangle {
            id: divider

            anchors { top: parent.top; bottom: parent.bottom; left: clusterRegion.right }
            width: Display.shared ? 1 : 0
            color: Theme.colors.surface_alt
            visible: Display.shared
        }

        Item {
            id: consoleRegion

            anchors {
                top: parent.top
                left: divider.right
                right: parent.right
                bottom: parent.bottom
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
    }

    Shortcut {
        sequences: ["Ctrl+Q", "Esc"]
        onActivated: Qt.quit()
    }
}
