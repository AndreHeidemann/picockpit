// Janela principal do PiCockpit OS.
// Estrutura: barra superior fixa, trilha de navegacao a esquerda e StackView
// de conteudo. Nenhuma funcionalidade de veiculo ainda - Etapa 1 e infraestrutura.
import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "pages"

ApplicationWindow {
    id: root

    // 1280x480 e uma proporcao comum de tela automotiva widescreen; a janela
    // e redimensionavel e o layout se adapta.
    width: 1280
    height: 480
    visible: true
    title: qsTr("PiCockpit OS")
    color: Theme.colors.background

    // Alternado com F11 para ensaiar o modo kiosk sem systemd.
    property bool kiosk: false

    readonly property var pages: [
        { key: "dashboard", label: qsTr("Painel"), glyph: "◴" },
        { key: "media",     label: qsTr("Media"),  glyph: "▶" },
        { key: "settings",  label: qsTr("Ajustes"), glyph: "⚙" }
    ]

    property int currentIndex: 0

    onCurrentIndexChanged: contentStack.replace(pageComponent(currentIndex))

    function pageComponent(index) {
        switch (root.pages[index].key) {
        case "media":    return mediaPage
        case "settings": return settingsPage
        default:         return dashboardPage
        }
    }

    Component { id: dashboardPage; DashboardPage {} }
    Component { id: mediaPage;     MediaPage {} }
    Component { id: settingsPage;  SettingsPage {} }

    Shortcut {
        sequences: ["F11"]
        onActivated: {
            root.kiosk = !root.kiosk
            root.visibility = root.kiosk ? Window.FullScreen : Window.Windowed
        }
    }

    Shortcut {
        sequences: ["Ctrl+Q", "Esc"]
        onActivated: Qt.quit()
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
        width: 96
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
