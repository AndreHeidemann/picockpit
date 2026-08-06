// Conteudo do cluster: barra minima e instrumentos.
//
// Extraido da janela para poder ser reaproveitado quando o cluster divide a
// tela com a multimidia. No Wayland uma aplicacao nao escolhe a propria
// posicao - isso e prerrogativa do compositor -, entao dividir uma tela entre
// dois papeis significa compor as duas regioes dentro de uma janela, e nao
// posicionar duas janelas lado a lado.
import QtQuick
import PiCockpit 1.0
import "pages"

Item {
    id: view

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
