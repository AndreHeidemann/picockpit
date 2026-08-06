// Janela principal do PiCockpit OS.
//
// Estrutura: barra superior fixa, trilha de navegacao a esquerda e StackView
// de conteudo, tudo dentro de uma tela logica que pode ser escalada.
import QtQuick
import QtQuick.Controls
import QtQuick.Window
import PiCockpit 1.0
import "pages"

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

    readonly property var pages: [
        { key: "dashboard", label: qsTr("Painel"), glyph: "◴" },
        { key: "performance", label: qsTr("Tempos"), glyph: "⏱" },
        { key: "charts",    label: qsTr("Graficos"), glyph: "◫" },
        { key: "trips",     label: qsTr("Viagens"), glyph: "▤" },
        { key: "media",     label: qsTr("Media"),  glyph: "▶" },
        { key: "settings",  label: qsTr("Ajustes"), glyph: "⚙" }
    ]

    property int currentIndex: 0

    onCurrentIndexChanged: contentStack.replace(pageComponent(currentIndex))

    function pageComponent(index) {
        switch (root.pages[index].key) {
        case "performance": return performancePage
        case "charts":   return chartsPage
        case "trips":    return tripsPage
        case "media":    return mediaPage
        case "settings": return settingsPage
        default:         return dashboardPage
        }
    }

    Component { id: dashboardPage; DashboardPage {} }
    Component { id: performancePage; PerformancePage {} }
    Component { id: chartsPage;    ChartsPage {} }
    Component { id: tripsPage;     TripsPage {} }
    Component { id: mediaPage;     MediaPage {} }
    Component { id: settingsPage;  SettingsPage {} }

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
        }

        NavigationRail {
            id: rail
            anchors { top: topBar.bottom; left: parent.left; bottom: parent.bottom }
            width: 92
            model: root.pages
            currentIndex: root.currentIndex
            onSelected: function (index) { root.currentIndex = index }
        }

        StackView {
            id: contentStack
            anchors {
                top: topBar.bottom
                left: rail.right
                right: parent.right
                bottom: parent.bottom
            }
            initialItem: dashboardPage

            // Transicoes curtas: em painel automotivo, resposta percebida importa
            // mais do que animacao elaborada.
            replaceEnter: Transition {
                NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 120 }
            }
            replaceExit: Transition {
                NumberAnimation { property: "opacity"; from: 1; to: 0; duration: 90 }
            }
        }
    }
}
