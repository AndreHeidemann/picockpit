// Carrega uma pagina a partir da sua chave.
//
// Existe para que a regiao principal e a secundaria da tela dividida usem
// exatamente o mesmo mapeamento: uma pagina nao sabe, nem precisa saber, em
// que metade da tela esta.
import QtQuick
import "pages"

Loader {
    id: host

    property string pageKey: "dashboard"

    asynchronous: false

    sourceComponent: {
        switch (pageKey) {
        case "performance": return performancePage
        case "charts":      return chartsPage
        case "widgets":     return widgetsPage
        case "trips":       return tripsPage
        case "media":       return mediaPage
        case "settings":    return settingsPage
        default:            return dashboardPage
        }
    }

    // Troca de pagina com esmaecimento curto: em painel automotivo, resposta
    // percebida importa mais do que animacao elaborada.
    onPageKeyChanged: fade.restart()

    SequentialAnimation {
        id: fade

        NumberAnimation { target: host; property: "opacity"; to: 0.0; duration: 70 }
        NumberAnimation { target: host; property: "opacity"; to: 1.0; duration: 110 }
    }

    Component { id: dashboardPage;   DashboardPage {} }
    Component { id: performancePage; PerformancePage {} }
    Component { id: chartsPage;      ChartsPage {} }
    Component { id: widgetsPage;     WidgetsPage {} }
    Component { id: tripsPage;       TripsPage {} }
    Component { id: mediaPage;       MediaPage {} }
    Component { id: settingsPage;    SettingsPage {} }
}
