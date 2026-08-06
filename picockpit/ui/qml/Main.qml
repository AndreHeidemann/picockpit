// Janela principal do PiCockpit OS.
//
// Barra superior fixa, trilha de navegacao a esquerda e area de conteudo que
// pode ser inteira ou dividida em duas regioes. Tudo dentro de uma tela logica
// que acompanha a escala escolhida nos ajustes.
import QtQuick
import QtQuick.Controls
import QtQuick.Window
import PiCockpit 1.0

ApplicationWindow {
    id: root

    // 1280x480 e uma proporcao comum de tela automotiva widescreen; a janela
    // e redimensionavel e o layout se adapta.
    width: 1280
    height: 480
    visible: true
    visibility: kiosk ? Window.FullScreen : Window.Windowed
    title: qsTr("PiCockpit OS")
    color: Theme.colors.background

    // Alternado com F11 para ensaiar o modo kiosk sem systemd. No carro
    // quem decide e a configuracao, e a janela ja nasce em tela cheia.
    property bool kiosk: AppInfo.kiosk

    readonly property var pages: Layout.pages
    property int currentIndex: 0

    readonly property string primaryKey: pages[currentIndex].key
    // A pagina de ajustes ocupa a tela toda mesmo com divisao ligada: e um
    // formulario, e formulario espremido em meia tela nao se usa dirigindo.
    readonly property bool splitActive: Layout.split && pages[currentIndex].splittable

    Shortcut {
        sequences: ["F11"]
        onActivated: root.kiosk = !root.kiosk
    }

    Shortcut {
        sequences: ["Ctrl+Q", "Esc"]
        onActivated: Qt.quit()
    }

    // Tela logica. Escalar aqui, e nao tamanho de fonte a tamanho de fonte,
    // mantem proporcao e espacamento coerentes: a interface inteira cresce
    // junto. A largura logica encolhe na mesma medida, para o conteudo
    // continuar preenchendo a janela.
    Item {
        id: canvas

        readonly property real factor: Settings.uiScale > 0 ? Settings.uiScale : 1.0

        width: root.width / factor
        height: root.height / factor
        transform: Scale {
            origin.x: 0
            origin.y: 0
            xScale: canvas.factor
            yScale: canvas.factor
        }

        TopBar {
            id: topBar
            anchors { top: parent.top; left: parent.left; right: parent.right }
            height: 56
            title: root.pages[root.currentIndex].label
                + (root.splitActive ? "  ·  " + Layout.labelOf(Layout.secondary) : "")
        }

        NavigationRail {
            id: rail
            anchors { top: topBar.bottom; left: parent.left; bottom: parent.bottom }
            width: 92
            model: root.pages
            currentIndex: root.currentIndex
            onSelected: function (index) { root.currentIndex = index }
        }

        Item {
            id: content

            anchors {
                top: topBar.bottom
                left: rail.right
                right: parent.right
                bottom: parent.bottom
            }

            PageHost {
                id: primaryHost

                anchors { top: parent.top; left: parent.left; bottom: parent.bottom }
                width: root.splitActive
                    ? Math.round(content.width * Layout.ratio) - 1
                    : content.width
                pageKey: root.primaryKey

                Behavior on width {
                    NumberAnimation { duration: 160; easing.type: Easing.OutQuad }
                }
            }

            Rectangle {
                id: divider

                anchors {
                    top: parent.top
                    bottom: parent.bottom
                    left: primaryHost.right
                }
                width: 1
                color: Theme.colors.surface_alt
                visible: root.splitActive
            }

            PageHost {
                anchors {
                    top: parent.top
                    left: divider.right
                    right: parent.right
                    bottom: parent.bottom
                }
                visible: root.splitActive
                active: root.splitActive
                pageKey: Layout.secondary
            }
        }
    }
}
